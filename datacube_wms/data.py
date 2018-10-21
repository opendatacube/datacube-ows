import json
from datetime import timedelta, datetime

import numpy
import xarray
from dask import delayed
from dask import array as da
from affine import Affine
import rasterio as rio
from rasterio.io import MemoryFile
from rasterio.warp import Resampling
from skimage.draw import polygon as skimg_polygon
from itertools import chain
import re

import datacube
from datacube.utils import geometry
from datacube.storage.masking import mask_to_dict

from datacube_wms.cube_pool import cube

from datacube_wms.wms_layers import get_service_cfg
from datacube_wms.wms_utils import img_coords_to_geopoint, int_trim, \
    bounding_box_to_geom, GetMapParameters, GetFeatureInfoParameters, \
    solar_correct_data
from datacube_wms.ogc_utils import resp_headers

import logging
import math
from datacube.utils import clamp

from datacube.drivers import new_datasource
import multiprocessing
from multiprocessing import cpu_count
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, wait, as_completed
from .rasterio_env import rio_env
from collections import OrderedDict
import traceback

from dea.geom import read_with_reproject

_LOG = logging.getLogger(__name__)
MAX_WORKERS = cpu_count() * 2


def _round(x, multiple):
    return int(multiple * round(float(x) / multiple))


def _make_destination(shape, no_data, dtype):
    return numpy.full(shape, no_data, dtype)


def _read_file(source, geobox, band, no_data, resampling):
    # Activate Rasterio
    with rio_env():
        # Read our data
        with rio.open(source.filename, sharing=False) as src:
            dst = read_with_reproject(src, geobox,
                                      dst_nodata=no_data,
                                      src_nodata_fallback=no_data,
                                      band=source.get_bandnumber(),
                                      resampling=resampling)
    return dst


def _get_measurement(datasources, geobox, resampling, no_data, dtype, fuse_func=None):
    """ Gets the measurement array of a band of data
    """
    # pylint: disable=broad-except, protected-access

    def copyto_fuser(dest, src):
        """
        :type dest: numpy.ndarray
        :type src: numpy.ndarray
        """
        where_nodata = (dest == no_data) if not numpy.isnan(no_data) else numpy.isnan(dest)
        numpy.copyto(dest, src, where=where_nodata)
        return dest

    fuse_func = fuse_func or copyto_fuser
    destination = _make_destination(geobox.shape, no_data, dtype)

    for source in datasources:
        buffer = delayed(_read_file)(source, geobox, band=source.get_bandnumber(), no_data=no_data,
                                     resampling=resampling)
        destination = delayed(fuse_func)(destination, buffer)

    return da.from_delayed(destination, geobox.shape, dtype)


# Read data for given datasets and measurements per the output_geobox
# If use_overviews is true
# Do not use this function to load data where accuracy is important
# may have errors when reprojecting the data
def read_data(datasets, measurements, geobox, use_overviews=False, resampling=Resampling.nearest, **kwargs):
    # pylint: disable=too-many-locals, dict-keys-not-iterating
    if not hasattr(datasets, "__iter__"):
        datasets = [datasets]
    holder = numpy.empty(shape=tuple(), dtype=object)
    holder[()] = datasets
    sources = xarray.DataArray(holder)
    if use_overviews:
        all_bands = xarray.Dataset()
        for name, coord in geobox.coordinates.items():
            all_bands[name] = (name, coord.values, {'units': coord.units})

        for measurement in measurements:
            datasources = [new_datasource(d, measurement['name']) for d in datasets]
            datasources = sorted(datasources, key=lambda x: x._dataset.id)
            data = _get_measurement(datasources,
                                    geobox,
                                    resampling,
                                    measurement['nodata'],
                                    measurement['dtype'],
                                    fuse_func=kwargs.get('fuse_func', None),
                                    )
            coords = OrderedDict((dim, sources.coords[dim]) for dim in sources.dims)
            dims = tuple(coords.keys()) + tuple(geobox.dimensions)
            all_bands[measurement['name']] = (dims, data, measurement.dataarray_attrs())

        all_bands.attrs['crs'] = geobox.crs
        all_bands.load()
        return all_bands.load()
    else:
        return datacube.Datacube.load_data(sources, geobox, measurements, **kwargs)


class DataStacker():
    def __init__(self, product, geobox, time, resampling=None, style=None, bands=None, **kwargs):
        super(DataStacker, self).__init__(**kwargs)
        self._product = product
        self._geobox = geobox
        self._resampling = resampling if resampling is not None else Resampling.nearest
        if style:
            self._needed_bands = style.needed_bands
        elif bands:
            self._needed_bands = bands
        else:
            self._needed_bands = self._product.product.measurements.keys()
        start_time = datetime(time.year, time.month, time.day) - timedelta(hours=product.time_zone)
        self._time = [start_time, start_time + timedelta(days=1)]

    def needed_bands(self):
        return self._needed_bands

    def point_in_dataset_by_extent(self, point, dataset):
        # Return true if dataset contains point
        compare_geometry = dataset.extent.to_crs(self._geobox.crs)
        return compare_geometry.contains(point)

    def datasets(self, index, mask=False, all_time=False, point=None):
        # Setup
        if all_time:
            # Use full available time range
            times = self._product.ranges["times"]
            time = [times[0], times[-1] + timedelta(days=1)]
        else:
            time = self._time
        if mask and self._product.pq_name:
            # Use PQ product
            prod_name = self._product.pq_name
        elif mask:
            # No PQ product, so no PQ datasets.
            return []
        else:
            # Use band product
            prod_name = self._product.product_name

        # ODC Dataset Query
        query = datacube.api.query.Query(product=prod_name, geopolygon=self._geobox.extent, time=time)
        _LOG.debug("query start %s", datetime.now().time())
        datasets = index.datasets.search_eager(**query.search_terms)
        _LOG.debug("query stop %s", datetime.now().time())

        if point:
            # Cleanup Note. Previously by_bounds was used for PQ data
            datasets = [dataset for dataset in datasets if self.point_in_dataset_by_extent(point, dataset)]

        return datasets

    def data(self, datasets, mask=False, manual_merge=False, skip_corrections=False, use_overviews=False, **kwargs):
        # pylint: disable=too-many-locals, consider-using-enumerate
        if mask:
            prod = self._product.pq_product
            measurements = [prod.measurements[self._product.pq_band].copy()]
        else:
            prod = self._product.product
            measurements = [prod.measurements[name].copy() for name in self.needed_bands()]

        with datacube.set_options(reproject_threads=1, fast_load=True):
            if manual_merge:
                return self.manual_data_stack(datasets, measurements, mask, skip_corrections, use_overviews, **kwargs)
            elif self._product.solar_correction and not mask and not skip_corrections:
                # Merge performed already by dataset extent, but we need to
                # process the data for the datasets individually to do solar correction.
                merged = None
                for ds in datasets:
                    d = read_data(ds, measurements, self._geobox, use_overviews, **kwargs)
                    for band in self.needed_bands():
                        if band != self._product.pq_band:
                            d[band] = solar_correct_data(d[band], ds)
                    if merged is None:
                        merged = d
                    else:
                        merged = merged.combine_first(d)
                return merged
            else:
                # Merge performed already by dataset extent
                if isinstance(datasets, xarray.DataArray):
                    sources = datasets
                else:
                    holder = numpy.empty(shape=tuple(), dtype=object)
                    holder[()] = datasets
                    sources = xarray.DataArray(holder)
                data = read_data(datasets, measurements, self._geobox, use_overviews, self._resampling, **kwargs)
                return data

    def manual_data_stack(self, datasets, measurements, mask, skip_corrections, use_overviews, **kwargs):
        # pylint: disable=too-many-locals, too-many-branches
        # manual merge
        merged = None
        if mask:
            bands = [self._product.pq_band]
        else:
            bands = self.needed_bands()
        for ds in datasets:
            d = read_data(ds, measurements, self._geobox, use_overviews, **kwargs)
            extent_mask = None
            for band in bands:
                for f in self._product.extent_mask_func:
                    if extent_mask is None:
                        extent_mask = f(d, band)
                    else:
                        extent_mask &= f(d, band)
            dm = d.where(extent_mask)
            if self._product.solar_correction and not mask and not skip_corrections:
                for band in bands:
                    if band != self._product.pq_band:
                        dm[band] = solar_correct_data(dm[band], ds)
            if merged is None:
                merged = dm
            else:
                merged = merged.combine_first(dm)
        if mask:
            merged = merged.astype('uint8', copy=True)
            for band in bands:
                merged[band].attrs = d[band].attrs
        return merged


def bbox_to_geom(bbox, crs):
    return datacube.utils.geometry.box(bbox.left, bbox.bottom, bbox.right, bbox.top, crs)


def get_map(args):
    # pylint: disable=too-many-nested-blocks, too-many-branches, too-many-statements, too-many-locals
    # Parse GET parameters
    params = GetMapParameters(args)

    with cube() as dc:
        # Tiling.
        stacker = DataStacker(params.product, params.geobox, params.time, params.resampling, style=params.style)
        datasets = stacker.datasets(dc.index)
        zoomed_out = params.zf < params.product.min_zoom
        too_many_datasets = (params.product.max_datasets_wms > 0 and len(datasets) > params.product.max_datasets_wms)
        if not datasets:
            body = _write_empty(params.geobox)
        elif too_many_datasets:
            body = _write_polygon(
                params.geobox,
                params.geobox.extent,
                params.product.zoom_fill)
        elif zoomed_out:
            # Zoomed out to far to properly render data.
            # Construct a polygon which is the union of the extents of the matching datasets.
            extent = None
            extent_crs = None
            for ds in datasets:
                if extent:
                    new_extent = bbox_to_geom(ds.extent.boundingbox, ds.extent.crs)
                    if new_extent.crs != extent_crs:
                        new_extent = new_extent.to_crs(extent_crs)
                    extent = extent.union(new_extent)
                else:
                    extent = bbox_to_geom(ds.extent.boundingbox, ds.extent.crs)
                    extent_crs = extent.crs
            extent = extent.to_crs(params.crs)
            body = _write_polygon(params.geobox, extent, params.product.zoom_fill)
        else:
            _LOG.debug("load start %s %s", datetime.now().time(), args["requestid"])
            data = stacker.data(datasets,
                                manual_merge=params.product.data_manual_merge,
                                use_overviews=True,
                                fuse_func=params.product.fuse_func)
            _LOG.debug("load stop %s %s", datetime.now().time(), args["requestid"])
            if params.style.masks:
                if params.product.pq_name == params.product.name:
                    pq_band_data = (data[params.product.pq_band].dims, data[params.product.pq_band].astype("uint16"))
                    pq_data = xarray.Dataset({params.product.pq_band: pq_band_data},
                                             coords=data[params.product.pq_band].coords
                                             )
                    flag_def = data[params.product.pq_band].flags_definition
                    pq_data[params.product.pq_band].attrs["flags_definition"] = flag_def
                else:
                    pq_datasets = stacker.datasets(dc.index, mask=True)
                    if pq_datasets:
                        pq_data = stacker.data(pq_datasets,
                                               mask=True,
                                               manual_merge=params.product.pq_manual_merge,
                                               use_overviews=True,
                                               fuse_func=params.product.fuse_func)
                    else:
                        pq_data = None
            else:
                pq_data = None
            extent_mask = None
            if not params.product.data_manual_merge:
                for band in params.style.needed_bands:
                    for f in params.product.extent_mask_func:
                        if extent_mask is None:
                            extent_mask = f(data, band)
                        else:
                            extent_mask &= f(data, band)

            if data is not None:
                body = _write_png(data, pq_data, params.style, extent_mask)
            else:
                body = _write_empty(params.geobox)

    return body, 200, resp_headers({"Content-Type": "image/png"})


def _write_png(data, pq_data, style, extent_mask):
    width = data[data.crs.dimensions[1]].size
    height = data[data.crs.dimensions[0]].size

    img_data = style.transform_data(data, pq_data, extent_mask)

    with MemoryFile() as memfile:
        with memfile.open(driver='PNG',
                          width=width,
                          height=height,
                          count=len(img_data.data_vars),
                          transform=Affine.identity(),
                          nodata=0,
                          dtype='uint8') as thing:
            for idx, band in enumerate(img_data.data_vars, start=1):
                thing.write_band(idx, img_data[band].values)

        return memfile.read()


def _write_empty(geobox):
    with MemoryFile() as memfile:
        with memfile.open(driver='PNG',
                          width=geobox.width,
                          height=geobox.height,
                          count=1,
                          transform=Affine.identity(),
                          nodata=0,
                          dtype='uint8') as thing:
            pass
        return memfile.read()


def _write_polygon(geobox, polygon, zoom_fill):
    geobox_ext = geobox.extent
    if geobox_ext.within(polygon):
        data = numpy.full([geobox.height, geobox.width], fill_value=1, dtype="uint8")
    else:
        data = numpy.zeros([geobox.height, geobox.width], dtype="uint8")
        if polygon.type == 'Polygon':
            coordinates_list = [polygon.json["coordinates"]]
        elif polygon.type == 'MultiPolygon':
            coordinates_list = polygon.json["coordinates"]
        else:
            raise Exception("Unexpected extent/geobox polygon geometry type: %s" % polygon.type)
        for polygon_coords in coordinates_list:
            pixel_coords = [~geobox.transform * coords for coords in polygon_coords[0]]
            rs, cs = skimg_polygon([c[1] for c in pixel_coords], [c[0] for c in pixel_coords],
                                   shape=[geobox.width, geobox.height])
            data[rs, cs] = 1

    with MemoryFile() as memfile:
        with memfile.open(driver='PNG',
                          width=geobox.width,
                          height=geobox.height,
                          count=len(zoom_fill),
                          transform=Affine.identity(),
                          nodata=0,
                          dtype='uint8') as thing:
            for idx, fill in enumerate(zoom_fill, start=1):
                thing.write_band(idx, data * fill)
        return memfile.read()


def get_s3_browser_uris(datasets):
    uris = [d.uris for d in datasets]
    uris = list(chain.from_iterable(uris))
    unique_uris = set(uris)

    regex = re.compile(r"s3:\/\/(?P<bucket>[a-zA-Z0-9_\-]+)\/(?P<prefix>[\S]+)/[a-zA-Z0-9_\-]+.yaml")

    # convert to browsable link
    def convert(uri):
        uri_format = "http://{bucket}.s3-website-ap-southeast-2.amazonaws.com/?prefix={prefix}"
        result = regex.match(uri)
        if result is not None:
            new_uri = uri_format.format(bucket=result.group("bucket"),
                                        prefix=result.group("prefix"))
        else:
            new_uri = uri
        return new_uri

    formatted = [convert(uri) for uri in unique_uris]

    return formatted


def _make_band_dict(pixel_dataset, band_list):
    band_dict = {}
    for band in band_list:
        ret_val = band_val = pixel_dataset[band].item()
        if band_val == pixel_dataset[band].nodata:
            band_dict[band] = "n/a"
        else:
            if 'flags_definition' in pixel_dataset[band].attrs:
                flag_def = pixel_dataset[band].attrs['flags_definition']
                flag_dict = mask_to_dict(flag_def, band_val)
                ret_val = [flag_def[flag]['description'] for flag, val in flag_dict.items() if val]
            band_dict[band] = ret_val
    return band_dict


def _make_derived_band_dict(pixel_dataset, style_index):
    """Creates a dict of values for bands derived by styles.
    This only works for styles with an `index_function` defined.

    :param xarray.Dataset pixel_dataset: A 1x1 pixel dataset containing band arrays
    :param dict(str, StyleCfg) style_index: dict of style configuration dicts
    :return: dict of style names to derived value
    """
    derived_band_dict = {}
    for style_name, style in style_index.items():
        if not hasattr(style, 'index_function') or style.index_function is None:
            continue

        if any(pixel_dataset[band] == pixel_dataset[band].nodata for band in style.needed_bands):
            continue

        derived_band_dict[style_name] = style.index_function(pixel_dataset).item()
    return derived_band_dict


def geobox_is_point(geobox):
    pts = geobox.extent._geom.GetGeometryRef(0).GetPoints()
    return pts.count(pts[0]) == len(pts)

def feature_info(args):
    # pylint: disable=too-many-nested-blocks, too-many-branches, too-many-statements, too-many-locals
    # Parse GET parameters
    params = GetFeatureInfoParameters(args)
    feature_json = {}

    geo_point = img_coords_to_geopoint(params.geobox, params.i, params.j)
    # shrink geobox to point
    # Prepare to extract feature info
    if geobox_is_point(params.geobox):
        geo_point_geobox = params.geobox
    else:
        geo_point_geom = bbox_to_geom(geo_point.boundingbox, geo_point.crs)
        geo_point_geobox = datacube.utils.geometry.GeoBox.from_geopolygon(geo_point_geom, params.geobox.resolution, crs=params.geobox.crs)
    stacker = DataStacker(params.product, geo_point_geobox, params.time)

    # --- Begin code section requiring datacube.
    service_cfg = get_service_cfg()
    with cube() as dc:
        datasets = stacker.datasets(dc.index, all_time=True, point=geo_point)
        pq_datasets = stacker.datasets(dc.index, mask=True, all_time=False, point=geo_point)

        # Taking the data as a single point so our indexes into the data should be 0,0
        h_coord = service_cfg.published_CRSs[params.crsid]["horizontal_coord"]
        v_coord = service_cfg.published_CRSs[params.crsid]["vertical_coord"]
        isel_kwargs = {
            h_coord: 0,
            v_coord: 0
        }

        if not datasets:
            pass
        else:
            available_dates = set()
            drill = {}
            for d in datasets:
                idx_date = (d.center_time + timedelta(hours=params.product.time_zone)).date()
                available_dates.add(idx_date)
                pixel_ds = None
                if idx_date == params.time and "lon" not in feature_json:
                    data = stacker.data([d], skip_corrections=True)
                    # Use i,j image coordinates to extract data pixel from dataset, and
                    # convert to lat/long geographic coordinates
                    if service_cfg.published_CRSs[params.crsid]["geographic"]:
                        # Geographic coordinate systems (e.g. EPSG:4326/WGS-84) are already in lat/long
                        feature_json["lat"] = data.latitude[params.j].item()
                        feature_json["lon"] = data.longitude[params.i].item()
                        pixel_ds = data.isel(**isel_kwargs)
                    else:
                        # Non-geographic coordinate systems need to be projected onto a geographic
                        # coordinate system.  Why not use EPSG:4326?
                        # Extract coordinates in CRS
                        data_x = getattr(data, h_coord)
                        data_y = getattr(data, v_coord)


                        x = data_x[isel_kwargs[h_coord]].item()
                        y = data_y[isel_kwargs[v_coord]].item()
                        pt = geometry.point(x, y, params.crs)

                        # Project to EPSG:4326
                        crs_geo = geometry.CRS("EPSG:4326")
                        ptg = pt.to_crs(crs_geo)

                        # Capture lat/long coordinates
                        feature_json["lon"], feature_json["lat"] = ptg.coords[0]

                    # Extract data pixel
                    pixel_ds = data.isel(**isel_kwargs)

                    # Get accurate timestamp from dataset
                    feature_json["time"] = d.center_time.strftime("%Y-%m-%d %H:%M:%S UTC")

                    # Collect raw band values for pixel and derived bands from styles
                    feature_json["bands"] = _make_band_dict(pixel_ds, stacker.needed_bands())
                    derived_band_dict = _make_derived_band_dict(pixel_ds, params.product.style_index)
                    if derived_band_dict:
                        feature_json["band_derived"] = derived_band_dict

                if params.product.band_drill:
                    if pixel_ds is None:
                        data = stacker.data([d], skip_corrections=True)
                        pixel_ds = data.isel(**isel_kwargs)
                    drill_section = {}
                    for band in params.product.band_drill:
                        band_val = pixel_ds[band].item()
                        if band_val == pixel_ds[band].nodata:
                            drill_section[band] = "n/a"
                        else:
                            drill_section[band] = pixel_ds[band].item()
                    drill[idx_date.strftime("%Y-%m-%d")] = drill_section

            if drill:
                feature_json["time_drill"] = drill
                feature_json["datasets_read"] = len(datasets)

            my_flags = 0
            for pqd in pq_datasets:
                idx_date = (pqd.center_time + timedelta(hours=params.product.time_zone)).date()
                if idx_date == params.time:
                    pq_data = stacker.data([pqd], mask=True)
                    pq_pixel_ds = pq_data.isel(**isel_kwargs)
                    # PQ flags
                    m = params.product.pq_product.measurements[params.product.pq_band]
                    flags = pq_pixel_ds[params.product.pq_band].item()
                    if not flags & ~params.product.info_mask:
                        my_flags = my_flags | flags
                    else:
                        continue
                    feature_json["flags"] = {}
                    for mk, mv in m["flags_definition"].items():
                        if mk in params.product.ignore_flags_info:
                            continue
                        bits = mv["bits"]
                        values = mv["values"]
                        if not isinstance(bits, int):
                            continue
                        flag = 1 << bits
                        if my_flags & flag:
                            val = values['1']
                        else:
                            val = values['0']
                        feature_json["flags"][mk] = val

            feature_json["data_available_for_dates"] = [d.strftime("%Y-%m-%d") for d in sorted(available_dates)]
            feature_json["data_links"] = sorted(get_s3_browser_uris(datasets))
    # --- End code section requiring datacube.

    result = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": feature_json
            }
        ]
    }
    return json.dumps(result), 200, resp_headers({"Content-Type": "application/json"})
