from __future__ import absolute_import

import json
from datetime import datetime, date

import numpy
import xarray
from affine import Affine
from rasterio.io import MemoryFile
from rasterio.warp import Resampling
from skimage.draw import polygon as skimg_polygon
from itertools import chain
import re

import datacube
from datacube.utils import geometry
from datacube.storage.masking import mask_to_dict

from datacube_ows.cube_pool import cube
from datacube_ows.ogc_exceptions import WMSException

from datacube_ows.ows_configuration import get_config
from datacube_ows.wms_utils import img_coords_to_geopoint, GetMapParameters, \
    GetFeatureInfoParameters, solar_correct_data, collapse_datasets_to_times
from datacube_ows.ogc_utils import local_solar_date_range, dataset_center_time, ConfigException, tz_for_geometry, \
    solar_date

from datacube_ows.utils import log_call, group_by_statistical

import logging

from datacube_ows.utils import get_opencensus_tracer, opencensus_trace_call

_LOG = logging.getLogger(__name__)

tracer = get_opencensus_tracer()

class DataStacker(object):
    @log_call
    def __init__(self, product, geobox, times, resampling=None, style=None, bands=None, **kwargs):
        super(DataStacker, self).__init__(**kwargs)
        self._product = product
        self.cfg = product.global_cfg
        self._geobox = geobox
        self._resampling = resampling if resampling is not None else Resampling.nearest
        if style:
            self._needed_bands = style.needed_bands
        elif bands:
            self._needed_bands = [ self._product.band_idx.band(b) for b in bands ]
        else:
            self._needed_bands = self._product.band_idx.native_bands.index

        self.raw_times = times
        if self._product.is_month_time_res:
            self._times = list(t for t in times)
            self.group_by = group_by_statistical()
        elif self._product.is_year_time_res:
            self._times = list([date(t.year, 1, 1) for t in times])
            self.group_by = group_by_statistical()
        else:
            self._times = list([local_solar_date_range(geobox, t) for t in times])
            self.group_by = "solar_day"

    def needed_bands(self):
        return self._needed_bands

    @log_call
    @opencensus_trace_call(tracer=tracer)
    def datasets(self, index, mask=False, all_time=False, point=None):
        # Return datasets as a time-grouped xarray DataArray. (or None if no datasets)
        # No PQ product, so no PQ datasets.
        if not self._product.pq_name and mask:
            return None

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
        if all_time:
            all_datasets = self._dataset_query(index, prod_name, query_args)
        else:
            all_datasets = []
            for th in self._times:
                query_args["time"] = th
                all_datasets.extend(self._dataset_query(index, prod_name, query_args))
        return datacube.Datacube.group_datasets(all_datasets, self.group_by)

    def _dataset_query(self, index, prod_name, query_args):
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

        return datasets

    @log_call
    @opencensus_trace_call(tracer=tracer)
    def data(self, datasets, mask=False, manual_merge=False, skip_corrections=False, **kwargs):
        # pylint: disable=too-many-locals, consider-using-enumerate
        # datasets is an XArray DataArray of datasets grouped by time.
        if mask:
            prod = self._product.pq_product
            measurements = [prod.measurements[self._product.pq_band].copy()]
        else:
            prod = self._product.product
            measurements = [prod.measurements[name].copy() for name in self.needed_bands()]

        with datacube.set_options(reproject_threads=1, fast_load=True):
            if manual_merge:
                return self.manual_data_stack(datasets, measurements, mask, skip_corrections, **kwargs)
            elif self._product.solar_correction and not mask and not skip_corrections:
                # Merge performed already by dataset extent, but we need to
                # process the data for the datasets individually to do solar correction.
                merged = None
                for ds in datasets:
                    d = self.read_data(ds, measurements, self._geobox, **kwargs)
                    for band in self.needed_bands():
                        if band != self._product.pq_band:
                            # No idea why pylint suddenly doesn't like this statement
                            # pylint: disable=unsupported-assignment-operation, unsubscriptable-object
                            d[band] = solar_correct_data(d[band], ds)
                    if merged is None:
                        merged = d
                    else:
                        merged = merged.combine_first(d)
                return merged
            else:
                data = self.read_data(datasets, measurements, self._geobox, self._resampling, **kwargs)
                return data

    @log_call
    @opencensus_trace_call(tracer=tracer)
    def manual_data_stack(self, datasets, measurements, mask, skip_corrections, **kwargs):
        # pylint: disable=too-many-locals, too-many-branches
        # REFACTOR: TODO
        # manual merge
        if mask:
            bands = [self._product.pq_band]
        else:
            bands = self.needed_bands()
        time_slices = []
        for dt in datasets.time.values:
            tds = datasets.sel(time=dt)
            merged = None
            for ds in tds.values.item():
                d = self.read_data_for_single_dataset(ds, measurements, self._geobox, **kwargs)
                d = d.squeeze(["time"], drop=True)
                # GROK - collapse!!!
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
            time_slices.append(merged)

        result = xarray.concat(time_slices, datasets.time)
        return result

    # Read data for given datasets and measurements per the output_geobox
    @log_call
    @opencensus_trace_call(tracer=tracer)
    def read_data(self, datasets, measurements, geobox, resampling=Resampling.nearest, **kwargs):
        return datacube.Datacube.load_data(
                datasets,
                geobox,
                measurements=measurements,
                fuse_func=kwargs.get('fuse_func', None))

    # Read data for single datasets and measurements per the output_geobox
    @log_call
    @opencensus_trace_call(tracer=tracer)
    def read_data_for_single_dataset(self, dataset, measurements, geobox, resampling=Resampling.nearest, **kwargs):
        datasets = [dataset]
        if self._product.is_raw_time_res:
            dc_datasets = datacube.Datacube.group_datasets(datasets, 'solar_day')
        else:
            dc_datasets = datacube.Datacube.group_datasets(datasets, 'time')
        return datacube.Datacube.load_data(
            dc_datasets,
            geobox,
            measurements=measurements,
            fuse_func=kwargs.get('fuse_func', None))


def datasets_in_xarray(xa):
    if xa is None:
        return 0
    return sum(len(xa.values[i]) for i in range(0, len(xa.values)))


def bbox_to_geom(bbox, crs):
    return datacube.utils.geometry.box(bbox.left, bbox.bottom, bbox.right, bbox.top, crs)


@log_call
@opencensus_trace_call(tracer=tracer)
def get_map(args):
    # pylint: disable=too-many-nested-blocks, too-many-branches, too-many-statements, too-many-locals
    # Parse GET parameters
    params = GetMapParameters(args)
    n_dates = len(params.times)
    if n_dates == 1:
        mdh = None
    else:
        mdh = params.style.get_multi_date_handler(n_dates)
        if mdh is None:
            raise WMSException("Style %s does not support GetMap requests with %d dates" % (params.style.name, n_dates),
                               WMSException.INVALID_DIMENSION_VALUE, locator="Time parameter")

    with cube() as dc:
        # Tiling.
        stacker = DataStacker(params.product, params.geobox, params.times, params.resampling, style=params.style)
        datasets = stacker.datasets(dc.index)
        n_datasets = datasets_in_xarray(datasets)
        zoomed_out = params.zf < params.product.min_zoom
        too_many_datasets = (params.product.max_datasets_wms > 0
                             and n_datasets > params.product.max_datasets_wms
        )
        if n_datasets == 0:
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
            for dt in datasets.time.values:
                tds = datasets.sel(time=dt)
                for ds in tds.values.item():
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
                    n_pq_datasets = datasets_in_xarray(pq_datasets)
                    if n_pq_datasets > 0:
                        pq_data = stacker.data(pq_datasets,
                                               mask=True,
                                               manual_merge=params.product.pq_manual_merge,
                                               fuse_func=params.product.pq_fuse_func)
                    else:
                        pq_data = None
            else:
                pq_data = None

            extent_mask = None
            if not params.product.data_manual_merge:
                td_masks = []
                for npdt in data.time.values:
                    td = data.sel(time=npdt)
                    td_ext_mask = None
                    for band in params.style.needed_bands:
                        for f in params.product.extent_mask_func:
                            if td_ext_mask is None:
                                td_ext_mask = f(td, band)
                            else:
                                td_ext_mask &= f(td, band)
                    td_masks.append(td_ext_mask)
                extent_mask = xarray.concat(td_masks, dim=data.time)
                #    extent_mask.add_time(td.time, ext_mask)

            if not data or (params.style.masks and not pq_data):
                body = _write_empty(params.geobox)
            else:
                body = _write_png(data, pq_data, params.style, extent_mask, params.geobox)
                
    cfg = get_config()
    return body, 200, cfg.response_headers({"Content-Type": "image/png"})


@log_call
@opencensus_trace_call(tracer=tracer)
def _write_png(data, pq_data, style, extent_mask, geobox):
    img_data = style.transform_data(data, pq_data, extent_mask)
    width = geobox.width
    height = geobox.height
    # width, height = img_data.pixel_counts()


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
def get_s3_browser_uris(datasets, s3url="", s3bucket=""):
    uris = []
    for tds in datasets:
        for ds in tds.values.item():
            uris.append(ds.uris)
    uris = list(chain.from_iterable(uris))
    unique_uris = set(uris)

    regex = re.compile(r"s3:\/\/(?P<bucket>[a-zA-Z0-9_\-\.]+)\/(?P<prefix>[\S]+)/[a-zA-Z0-9_\-\.]+.yaml")

    # convert to browsable link
    def convert(uri):
        uri_format = "http://{bucket}.s3-website-ap-southeast-2.amazonaws.com/?prefix={prefix}"
        uri_format_prod = str(s3url) + "/?prefix={prefix}"
        result = regex.match(uri) 
        if result is not None:
            if result.group("bucket") == str(s3bucket):
                new_uri = uri_format_prod.format(prefix=result.group("prefix"))
            else:
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
                    # HACK: Work around bands with floating point values
                    try:
                        flag_dict = mask_to_dict(flag_def, band_val)
                    except TypeError as te:
                        logging.warning('Working around for float bands')
                        flag_dict = mask_to_dict(flag_def, int(band_val))
                    try:
                        ret_val = [flag_def[flag]['description'] for flag, val in flag_dict.items() if val]
                    except KeyError:
                        # Weirdly formatted flag definition.  Hacky workaround for USGS data in DEAfrica demo.
                        ret_val = [ val for flag, val in flag_dict.items() if val ]
                band_dict[band_lbl] = ret_val
        except ConfigException:
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
        if not style.include_in_feature_info:
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
    tz = tz_for_geometry(geo_point_geobox.geographic_extent)
    stacker = DataStacker(params.product, geo_point_geobox, params.times)

    # --- Begin code section requiring datacube.
    cfg = get_config()
    with cube() as dc:
        datasets = stacker.datasets(dc.index, all_time=True, point=geo_point)

        # Taking the data as a single point so our indexes into the data should be 0,0
        h_coord = cfg.published_CRSs[params.crsid]["horizontal_coord"]
        v_coord = cfg.published_CRSs[params.crsid]["vertical_coord"]
        s3_bucket = cfg.s3_bucket
        s3_url = cfg.s3_url
        isel_kwargs = {
            h_coord: 0,
            v_coord: 0
        }
        if any(datasets):
            # Group datasets by time, load only datasets that match the idx_date
            global_info_written = False
            feature_json["data"] = []
            fi_date_index = {}
            ds_at_times =collapse_datasets_to_times(datasets, params.times, tz)
            # ds_at_times["time"].attrs["units"] = 'seconds since 1970-01-01 00:00:00'
            data = stacker.data(ds_at_times, skip_corrections=True,
                                manual_merge=params.product.data_manual_merge,
                                fuse_func=params.product.fuse_func
                                )
            for dt in data.time.values:
                td = data.sel(time=dt)
                # Global data that should apply to all dates, but needs some data to extract
                if not global_info_written:
                    global_info_written = True
                    # Non-geographic coordinate systems need to be projected onto a geographic
                    # coordinate system.  Why not use EPSG:4326?
                    # Extract coordinates in CRS
                    data_x = getattr(td, h_coord)
                    data_y = getattr(td, v_coord)

                    x = data_x[isel_kwargs[h_coord]].item()
                    y = data_y[isel_kwargs[v_coord]].item()
                    pt = geometry.point(x, y, params.crs)

                    # Project to EPSG:4326
                    crs_geo = geometry.CRS("EPSG:4326")
                    ptg = pt.to_crs(crs_geo)

                    # Capture lat/long coordinates
                    feature_json["lon"], feature_json["lat"] = ptg.coords[0]

                date_info = {}

                ds = ds_at_times.sel(time=dt).values.tolist()[0]
                if params.product.multi_product:
                    date_info["source_product"] = "%s (%s)" % (ds.type.name, ds.metadata_doc["platform"]["code"])

                # Extract data pixel
                pixel_ds = td.isel(**isel_kwargs)

                # Get accurate timestamp from dataset
                date_info["time"] = dataset_center_time(ds).strftime("%Y-%m-%d %H:%M:%S UTC")

                # Collect raw band values for pixel and derived bands from styles
                date_info["bands"] = _make_band_dict(params.product, pixel_ds, stacker.needed_bands())
                derived_band_dict = _make_derived_band_dict(pixel_ds, params.product.style_index)
                if derived_band_dict:
                    date_info["band_derived"] = derived_band_dict
                # Add any custom-defined fields.
                for k, f in params.product.feature_info_custom_includes.items():
                    date_info[k] = f(date_info["bands"])

                feature_json["data"].append(date_info)
                fi_date_index[dt] = feature_json["data"][-1]

            my_flags = 0
            if params.product.pq_names == params.product.product_names:
                pq_datasets = ds_at_times
            else:
                pq_datasets = stacker.datasets(dc.index, mask=True, all_time=False, point=geo_point)

            if pq_datasets:
                pq_datasets =collapse_datasets_to_times(pq_datasets, params.times, tz)
                pq_data = stacker.data(pq_datasets, mask=True)
                feature_json["flags"] = []
                for dt in pq_data.time.values:
                    pqd =pq_data.sel(time=dt)
                    date_info = fi_date_index.get(dt)
                    if not date_info:
                        date_info = {}
                        feature_json["data"].append(date_info)
                    pq_pixel_ds = pqd.isel(**isel_kwargs)
                    # PQ flags
                    m = params.product.pq_product.measurements[params.product.pq_band]
                    flags = pq_pixel_ds[params.product.pq_band].item()
                    if not flags & ~params.product.info_mask:
                        my_flags = my_flags | flags
                    else:
                        continue
                    date_info["flags"] = {}
                    for mk, mv in m["flags_definition"].items():
                        if mk in params.product.ignore_info_flags:
                            continue
                        bits = mv["bits"]
                        values = mv["values"]
                        if isinstance(bits, int):
                            flag = 1 << bits
                            if my_flags & flag:
                                val = values['1']
                            else:
                                val = values['0']
                            date_info["flags"][mk] = val
                        else:
                            try:
                                for i in bits:
                                    if not isinstance(i, int):
                                        raise TypeError()
                                # bits is a list of ints try to do it alos way
                                for key, desc in values.items():
                                    if (isinstance(key, str) and key == str(my_flags)) or (isinstance(key, int) and key==my_flags):
                                        date_info["flags"][mk] = desc
                                        break
                            except TypeError:
                                pass
            feature_json["data_available_for_dates"] = []
            for d in datasets.coords["time"].values:
                dt = datetime.utcfromtimestamp(d.astype(int) * 1e-9)
                if params.product.is_raw_time_res:
                    dt = solar_date(dt, tz)
                feature_json["data_available_for_dates"].append(dt.strftime("%Y-%m-%d"))
            feature_json["data_links"] = sorted(get_s3_browser_uris(datasets, s3_url, s3_bucket))
            if params.product.feature_info_include_utc_dates:
                unsorted_dates = []
                for tds in datasets:
                    for ds in tds.values.item():
                        if params.product.time_resolution.is_raw_time_res:
                            unsorted_dates.append(ds.center_time.strftime("%Y-%m-%d"))
                        else:
                            unsorted_dates.append(ds.time.begin.strftime("%Y-%m-%d"))
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
    return json.dumps(result), 200, cfg.response_headers({"Content-Type": "application/json"})
