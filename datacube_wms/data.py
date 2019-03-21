from __future__ import absolute_import

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
from datacube_wms.ogc_utils import resp_headers, local_solar_date_range, local_date, dataset_center_time, \
    ProductLayerException

from datacube_wms.utils import log_call

import logging

from datacube.drivers import new_datasource
from collections import OrderedDict

from dea.geom import read_with_reproject

from datacube_wms.utils import get_opencensus_tracer, opencensus_trace_call

_LOG = logging.getLogger(__name__)

tracer = get_opencensus_tracer()

def _make_destination(shape, no_data, dtype):
    return numpy.full(shape, no_data, dtype)

@log_call
@opencensus_trace_call(tracer=tracer)
def _read_file(source, geobox, band, no_data, resampling):
    # Read our data
    with rio.DatasetReader(rio.path.parse_path(source.filename), sharing=False) as src:
        dst = read_with_reproject(src, geobox,
                                  dst_nodata=no_data,
                                  src_nodata_fallback=no_data,
                                  band=source.get_bandnumber(),
                                  resampling=resampling)
    return dst


@log_call
@opencensus_trace_call(tracer=tracer)
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
@log_call
@opencensus_trace_call(tracer=tracer)
def read_data(datasets, measurements, geobox, use_overviews=False, resampling=Resampling.nearest, **kwargs):
    # pylint: disable=too-many-locals, dict-keys-not-iterating, protected-access
    if not hasattr(datasets, "__iter__"):
        datasets = [datasets]
    if isinstance(datasets, xarray.DataArray):
        sources = datasets
    else:
        holder = numpy.empty(shape=tuple(), dtype=object)
        holder[()] = datasets
        sources = xarray.DataArray(holder)
    if use_overviews:
        all_bands = xarray.Dataset()
        for name, coord in geobox.coordinates.items():
            all_bands[name] = (name, coord.values, {'units': coord.units})

        datasets = sorted(datasets, key=lambda x: x.id)
        for measurement in measurements:
            datasources = [new_datasource(d, measurement['name']) for d in datasets]
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
        return all_bands.load()
    else:
        return datacube.Datacube.load_data(sources, geobox, measurements, **kwargs)


class DataStacker():
    @log_call
    def __init__(self, product, geobox, time, resampling=None, style=None, bands=None, **kwargs):
        super(DataStacker, self).__init__(**kwargs)
        self._product = product
        self._geobox = geobox
        self._resampling = resampling if resampling is not None else Resampling.nearest
        if style:
            self._needed_bands = style.needed_bands
        elif bands:
            self._needed_bands = [ self._product.band_idx.band(b) for b in bands ]
        else:
            self._needed_bands = self._product.band_idx.native_bands.index
        self._time = local_solar_date_range(geobox, time)

    def needed_bands(self):
        return self._needed_bands

    def point_in_dataset_by_extent(self, point, dataset):
        # Return true if dataset contains point
        compare_geometry = dataset.extent.to_crs(self._geobox.crs)
        return compare_geometry.contains(point)

    @log_call
    @opencensus_trace_call(tracer=tracer)
    def datasets(self, index, mask=False, all_time=False, point=None):
        # No PQ product, so no PQ datasets.
        if not self._product.pq_name and mask:
            return []

        if self._product.multi_product:
            prod_name = self._product.pq_names if mask and self._product.pq_name else self._product.product_names
            query_args = {
                "geopolygon": self._geobox.extent
            }
        else:
            prod_name = self._product.pq_name if mask and self._product.pq_name else self._product.product_name
            query_args = {
                "product": prod_name,
                "geopolygon": self._geobox.extent
            }
        if not all_time:
            query_args["time"] = self._time

        # ODC Dataset Query
        if self._product.multi_product:
            queries = []
            for pn in prod_name:
                query_args["product"] = pn
                queries.append(datacube.api.query.Query(**query_args))
            _LOG.debug("query start %s", datetime.now().time())
            datasets = []
            for q in queries:
                datasets.extend(index.datasets.search_eager(**q.search_terms))
            _LOG.debug("query stop %s", datetime.now().time())
        else:
            query = datacube.api.query.Query(**query_args)
            _LOG.debug("query start %s", datetime.now().time())
            datasets = index.datasets.search_eager(**query.search_terms)
            _LOG.debug("query stop %s", datetime.now().time())

        if point:
            # Cleanup Note. Previously by_bounds was used for PQ data
            datasets = [dataset for dataset in datasets if self.point_in_dataset_by_extent(point, dataset)]

        return datasets

    @log_call
    @opencensus_trace_call(tracer=tracer)
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
                data = read_data(datasets, measurements, self._geobox, use_overviews, self._resampling, **kwargs)
                return data

    @log_call
    @opencensus_trace_call(tracer=tracer)
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


@log_call
@opencensus_trace_call(tracer=tracer)
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
                    pq_datasets = stacker.datasets(dc.index, mask=True, all_time=params.product.pq_ignore_time)
                    if pq_datasets:
                        pq_data = stacker.data(pq_datasets,
                                               mask=True,
                                               manual_merge=params.product.pq_manual_merge,
                                               use_overviews=True,
                                               fuse_func=params.product.pq_fuse_func)
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


@log_call
@opencensus_trace_call(tracer=tracer)
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


@log_call
@opencensus_trace_call(tracer=tracer)
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


@log_call
@opencensus_trace_call(tracer=tracer)
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


@log_call
@opencensus_trace_call(tracer=tracer)
def get_s3_browser_uris(datasets):
    uris = [d.uris for d in datasets]
    uris = list(chain.from_iterable(uris))
    unique_uris = set(uris)

    regex = re.compile(r"s3:\/\/(?P<bucket>[a-zA-Z0-9_\-\.]+)\/(?P<prefix>[\S]+)/[a-zA-Z0-9_\-\.]+.yaml")

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

    formatted = {convert(uri) for uri in unique_uris}

    return formatted


@log_call
@opencensus_trace_call(tracer=tracer)
def _make_band_dict(prod_cfg, pixel_dataset, band_list):
    band_dict = {}
    for band in band_list:
        try:
            band_lbl = prod_cfg.band_idx.band_label(band)
            ret_val = band_val = pixel_dataset[band].item()
            if band_val == pixel_dataset[band].nodata or numpy.isnan(band_val):
                band_dict[band_lbl] = "n/a"
            else:
                if 'flags_definition' in pixel_dataset[band].attrs:
                    flag_def = pixel_dataset[band].attrs['flags_definition']
                    flag_dict = mask_to_dict(flag_def, band_val)
                    ret_val = [flag_def[flag]['description'] for flag, val in flag_dict.items() if val]
                band_dict[band_lbl] = ret_val
        except ProductLayerException:
            pass
    return band_dict


@log_call
@opencensus_trace_call(tracer=tracer)
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

        value = style.index_function(pixel_dataset).item()
        derived_band_dict[style_name] = value if not numpy.isnan(value) else "n/a"
    return derived_band_dict


@log_call
def geobox_is_point(geobox):
    #pylint: disable=protected-access
    pts = geobox.extent._geom.GetGeometryRef(0).GetPoints()
    return pts.count(pts[0]) == len(pts)


@log_call
@opencensus_trace_call(tracer=tracer)
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
        geo_point_geobox = datacube.utils.geometry.GeoBox.from_geopolygon(
            geo_point, params.geobox.resolution, crs=params.geobox.crs)
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
        if datasets:
            # Group datasets by time, load only datasets that match the idx_date
            available_dates = {local_date(d) for d in datasets}
            pixel_ds = None
            ds_at_time = [ds for ds in datasets if local_date(ds) == params.time]
            if len(ds_at_time) > 0:
                data = stacker.data(ds_at_time, skip_corrections=True)
                pixel_ds = data.isel(**isel_kwargs)

                # Non-geographic coordinate systems need to be projected onto a geographic
                # coordinate system.  Why not use EPSG:4326?
                # Extract coordinates in CRS
                data_x = getattr(data, h_coord)
                data_y = getattr(data, v_coord)

                x = data_x[isel_kwargs[h_coord]].item()
                y = data_y[isel_kwargs[v_coord]].item()
                pt = geometry.point(x, y, params.crs)

                if params.product.multi_product:
                    feature_json["source_product"] = "%s (%s)" % (ds_at_time[0].type.name, ds_at_time[0].metadata_doc["platform"]["code"])

                # Project to EPSG:4326
                crs_geo = geometry.CRS("EPSG:4326")
                ptg = pt.to_crs(crs_geo)

                # Capture lat/long coordinates
                feature_json["lon"], feature_json["lat"] = ptg.coords[0]

                # Extract data pixel
                pixel_ds = data.isel(**isel_kwargs)

                # Get accurate timestamp from dataset
                feature_json["time"] = dataset_center_time(ds_at_time[0]).strftime("%Y-%m-%d %H:%M:%S UTC")

                # Collect raw band values for pixel and derived bands from styles
                feature_json["bands"] = _make_band_dict(params.product, pixel_ds, stacker.needed_bands())
                derived_band_dict = _make_derived_band_dict(pixel_ds, params.product.style_index)
                if derived_band_dict:
                    feature_json["band_derived"] = derived_band_dict
                if callable(params.product.feature_info_include_custom):
                    additional_data = params.product.feature_info_include_custom(feature_json["bands"])
                    feature_json.update(additional_data)

            my_flags = 0
            for pqd in pq_datasets:
                idx_date = dataset_center_time(pqd)
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
            if params.product.feature_info_include_utc_dates:
                feature_json["data_available_for_utc_dates"] = sorted(
                    d.center_time.strftime("%Y-%m-%d") for d in datasets)
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
