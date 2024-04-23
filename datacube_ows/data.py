# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import json
import logging
import re
from datetime import date, datetime, timedelta
from itertools import chain
from typing import Iterable, cast, Any, Mapping

import numpy
import numpy.ma
import pytz
import xarray
from datacube.model import Dataset
from datacube.utils.masking import mask_to_dict
from flask import render_template
from odc.geo import geom
from odc.geo.geobox import GeoBox
from pandas import Timestamp
from rasterio.features import rasterize
from rasterio.io import MemoryFile

from datacube_ows.cube_pool import cube
from datacube_ows.loading import DataStacker, ProductBandQuery
from datacube_ows.mv_index import MVSelectOpts
from datacube_ows.ogc_exceptions import WMSException
from datacube_ows.ogc_utils import (dataset_center_time,
                                    solar_date, tz_for_geometry,
                                    xarray_image_as_png)
from datacube_ows.config_utils import ConfigException, RAW_CFG, CFG_DICT
from datacube_ows.ows_configuration import get_config, OWSNamedLayer, OWSConfig
from datacube_ows.styles import StyleDef
from datacube_ows.query_profiler import QueryProfiler
from datacube_ows.resource_limits import ResourceLimited
from datacube_ows.utils import default_to_utc, log_call
from datacube_ows.wms_utils import (GetFeatureInfoParameters, GetMapParameters,
                                    img_coords_to_geopoint)

_LOG = logging.getLogger(__name__)

FlaskResponse = tuple[str | bytes, int, dict[str, str]]


def user_date_sorter(layer: OWSNamedLayer, odc_dates: list[datetime],
                     geometry: geom.Geometry, user_dates: list[datetime]) -> xarray.DataArray:
    # TODO: Make more elegant.  Just a little bit elegant would do.
    result = []
    if layer.time_resolution.is_solar():
        tz = tz_for_geometry(geometry)
    else:
        tz = None

    def check_date(time_res, user_date, odc_date):
        ts = Timestamp(odc_date).tz_localize("UTC")
        if time_res.is_solar():
            norm_date = solar_date(ts, tz)
            return norm_date == user_date
        elif time_res.is_summary():
            norm_date = date(ts.year,
                             ts.month,
                             ts.day,
                             tzinfo=pytz.utc)
            return norm_date == user_date
        else:
            norm_date = datetime(ts.year,
                                 ts.month,
                                 ts.day,
                                 ts.hour,
                                 ts.minute,
                                 ts.second,
                                 tzinfo=ts.tzinfo)
            user_date = default_to_utc(user_date)
            return user_date >= norm_date and user_date < norm_date + timedelta(hours=23, minutes=59, seconds=59)

    for odc_date in odc_dates:
        for idx, user_date in enumerate(user_dates):
            if check_date(layer.time_resolution, user_date, odc_date):
                result.append(idx)
                break
    npresult = numpy.array(result, dtype="uint8")
    xrresult = xarray.DataArray(
        npresult,
        coords={"time": odc_dates},
        dims=["time"],
        name="user_date_sorter"
    )
    return xrresult


class EmptyResponse(Exception):
    pass


@log_call
def get_map(args: dict[str, str]) -> FlaskResponse:
    # pylint: disable=too-many-nested-blocks, too-many-branches, too-many-statements, too-many-locals
    # Parse GET parameters
    params = GetMapParameters(args)
    qprof = QueryProfiler(params.ows_stats)
    n_dates = len(params.times)
    if n_dates == 1:
        mdh = None
    else:
        mdh = params.style.get_multi_date_handler(n_dates)
        if mdh is None:
            raise WMSException("Style %s does not support GetMap requests with %d dates" % (params.style.name, n_dates),
                               WMSException.INVALID_DIMENSION_VALUE, locator="Time parameter")
    qprof["n_dates"] = n_dates
    with cube() as dc:
        try:
            if not dc:
                raise WMSException("Database connectivity failure")
            # Tiling.
            stacker = DataStacker(params.product, params.geobox, params.times, params.resampling, style=params.style)
            qprof["zoom_factor"] = params.zf
            qprof.start_event("count-datasets")
            n_datasets = stacker.datasets(dc.index, mode=MVSelectOpts.COUNT)
            qprof.end_event("count-datasets")
            qprof["n_datasets"] = n_datasets
            qprof["zoom_level_base"] = params.resources.base_zoom_level
            qprof["zoom_level_adjusted"] = params.resources.load_adjusted_zoom_level
            try:
                params.product.resource_limits.check_wms(n_datasets, params.zf, params.resources)
            except ResourceLimited as e:
                stacker.resource_limited = True
                qprof["resource_limited"] = str(e)
            if qprof.active:
                q_ds_dict = cast(dict[ProductBandQuery, xarray.DataArray],
                                 stacker.datasets(dc.index, mode=MVSelectOpts.DATASETS))
                qprof["datasets"] = []
                for q, dsxr in q_ds_dict.items():
                    query_res: dict[str, Any] = {}
                    query_res["query"] = str(q)
                    query_res["datasets"] = [
                        [
                            f"{ds.id} ({ds.type.name})"
                            for ds in tdss
                        ]
                        for tdss in dsxr.values
                    ]
                    qprof["datasets"].append(query_res)
            if stacker.resource_limited and not params.product.low_res_product_names:
                qprof.start_event("extent-in-query")
                extent = cast(geom.Geometry | None, stacker.datasets(dc.index, mode=MVSelectOpts.EXTENT))
                qprof.end_event("extent-in-query")
                if extent is None:
                    qprof["write_action"] = "No extent: Write Empty"
                    raise EmptyResponse()
                else:
                    qprof["write_action"] = "Polygon"
                    qprof.start_event("write")
                    body = _write_polygon(
                        params.geobox,
                        extent,
                        params.product.resource_limits.zoom_fill,
                        params.product)
                    qprof.end_event("write")
            elif n_datasets == 0:
                qprof["write_action"] = "No datasets: Write Empty"
                raise EmptyResponse()
            else:
                if stacker.resource_limited:
                    qprof.start_event("count-summary-datasets")
                    qprof["n_summary_datasets"] = stacker.datasets(dc.index, mode=MVSelectOpts.COUNT)
                    qprof.end_event("count-summary-datasets")
                qprof.start_event("fetch-datasets")
                datasets = cast(dict[ProductBandQuery, xarray.DataArray], stacker.datasets(dc.index))
                for flagband, dss in datasets.items():
                    if not dss.any():
                        _LOG.warning("Flag band %s returned no data", str(flagband))
                    if len(dss.time) != n_dates and flagband.main:
                        qprof["write_action"] = f"{n_dates} requested, only {len(dss.time)} found - returning empty image"
                        raise EmptyResponse()
                qprof.end_event("fetch-datasets")
                _LOG.debug("load start %s %s", datetime.now().time(), args["requestid"])
                qprof.start_event("load-data")
                data = stacker.data(datasets)
                qprof.end_event("load-data")
                if not data:
                    qprof["write_action"] = "No Data: Write Empty"
                    raise EmptyResponse()
                _LOG.debug("load stop %s %s", datetime.now().time(), args["requestid"])
                qprof.start_event("build-masks")
                td_masks = []
                for npdt in data.time.values:
                    td = data.sel(time=npdt)
                    td_ext_mask_man: numpy.ndarray | None = None
                    td_ext_mask: xarray.DataArray | None = None
                    band = ""
                    for band in params.style.needed_bands:
                        if band not in params.style.flag_bands:
                            if params.product.data_manual_merge:
                                if td_ext_mask_man is None:
                                    td_ext_mask_man = ~numpy.isnan(td[band])
                                else:
                                    td_ext_mask_man &= ~numpy.isnan(td[band])
                            else:
                                for f in params.product.extent_mask_func:
                                    if td_ext_mask is None:
                                        td_ext_mask = f(td, band)
                                    else:
                                        td_ext_mask &= f(td, band)
                    if params.product.data_manual_merge:
                        td_ext_mask = xarray.DataArray(td_ext_mask_man)
                    if td_ext_mask is None:
                        td_ext_mask = xarray.DataArray(
                                            ~numpy.zeros(
                                                        td[band].values.shape,
                                                        dtype=numpy.bool_
                                            ),
                                            td[band].coords
                        )
                    td_masks.append(td_ext_mask)
                extent_mask = xarray.concat(td_masks, dim=data.time)
                qprof.end_event("build-masks")
                qprof["write_action"] = "Write Data"
                if mdh and mdh.preserve_user_date_order:
                    sorter = user_date_sorter(
                                              params.product,
                                              data.time.values,
                                              params.geobox.geographic_extent,
                                              params.times)
                    data = data.sortby(sorter)
                    extent_mask = extent_mask.sortby(sorter)

                body = _write_png(data, params.style, extent_mask, qprof)
        except EmptyResponse:
            qprof.start_event("write")
            body = _write_empty(params.geobox)
            qprof.end_event("write")

    if params.ows_stats:
        return json_response(qprof.profile())
    else:
        return png_response(body, extra_headers=params.product.resource_limits.wms_cache_rules.cache_headers(n_datasets))


def png_response(body: bytes, cfg: OWSConfig | None = None, extra_headers: dict[str, str] | None = None) -> FlaskResponse:
    if not cfg:
        cfg = get_config()
    assert cfg is not None  # For type checker
    if extra_headers is None:
        extra_headers = {}
    headers = {"Content-Type": "image/png"}
    headers.update(extra_headers)
    headers = cfg.response_headers(headers)
    return body, 200, cfg.response_headers(headers)


@log_call
def _write_png(data: xarray.Dataset, style: StyleDef, extent_mask: xarray.DataArray,
               qprof: QueryProfiler) -> bytes:
    qprof.start_event("combine-masks")
    mask = style.to_mask(data, extent_mask)
    qprof.end_event("combine-masks")
    qprof.start_event("apply-style")
    img_data = style.transform_data(data, mask)
    qprof.end_event("apply-style")
    qprof.start_event("write")
    # If time dimension is present animate over it.
    # Verified using : https://docs.dea.ga.gov.au/notebooks/Frequently_used_code/Animated_timeseries.html
    mdh = style.get_multi_date_handler(img_data)
    if mdh:
        image = xarray_image_as_png(img_data, loop_over='time', animate=True, frame_duration=mdh.frame_duration)
    else:
        image = xarray_image_as_png(img_data)
    qprof.end_event("write")
    return image


@log_call
def _write_empty(geobox: GeoBox) -> bytes:
    with MemoryFile() as memfile:
        with memfile.open(driver='PNG',
                          width=geobox.width,
                          height=geobox.height,
                          count=1,
                          transform=None,
                          nodata=0,
                          dtype='uint8') as thing:
            pass
        return memfile.read()


def get_coordlist(geo: geom.Geometry, layer_name: str) -> list[tuple[float | int, float | int]]:
    if geo.type == 'Polygon':
        coordinates_list = [geo.json["coordinates"]]
    elif geo.type == 'MultiPolygon':
        coordinates_list = geo.json["coordinates"]
    elif geo.type == 'GeometryCollection':
        coordinates_list = []
        for geom in geo.json["geometries"]:
            if geom["type"] == "Polygon":
                coordinates_list.append(geom["coordinates"])
            elif geom["type"] == "MultiPolygon":
                coordinates_list.extend(geom["coordinates"])
            else:
                _LOG.warning(
                    "Extent contains non-polygon GeometryType (%s in GeometryCollection - ignoring), layer: %s",
                    geom["type"],
                    layer_name)
    else:
        raise Exception("Unexpected extent/geobox polygon geometry type: %s in layer %s" % (geo.type, layer_name))
    return coordinates_list


@log_call
def _write_polygon(geobox: GeoBox, polygon: geom.Geometry, zoom_fill: list[int], layer: OWSNamedLayer) -> bytes:
    geobox_ext = geobox.extent
    if geobox_ext.within(polygon):
        data = numpy.full([geobox.height, geobox.width], fill_value=1, dtype="uint8")
    else:
        data = numpy.zeros([geobox.height, geobox.width], dtype="uint8")
        data = rasterize(shapes=[polygon],
                          fill=0,
                          default_value=2,
                          out=data,
                          transform=geobox.affine
                        )
    with MemoryFile() as memfile:
        with memfile.open(driver='PNG',
                          width=geobox.width,
                          height=geobox.height,
                          count=4,
                          transform=None,
                          nodata=0,
                          dtype='uint8') as thing:
            for idx, fill in enumerate(zoom_fill, start=1):
                thing.write_band(idx, data * fill)
        return memfile.read()


@log_call
def get_s3_browser_uris(datasets: dict[ProductBandQuery, xarray.DataArray],
                        pt: geom.Geometry | None = None,
                        s3url: str = "", s3bucket: str = "") -> set[str]:
    uris = []
    last_crs = None
    for pbq, dss in datasets.items():
        if pbq.main:
            for tds in dss:
                for ds in tds.values.item():
                    if pt and ds.extent:
                        if ds.crs != last_crs:
                            pt_native = pt.to_crs(ds.crs)
                            last_crs = ds.crs
                        if ds.extent.contains(pt_native):
                            uris.append(ds.uris)
                    else:
                        uris.append(ds.uris)
            break

    uris = list(chain.from_iterable(uris))
    unique_uris = set(uris)

    regex = re.compile(r"s3:\/\/(?P<bucket>[a-zA-Z0-9_\-\.]+)\/(?P<prefix>[\S]+)/[a-zA-Z0-9_\-\.]+.yaml")

    # convert to browsable link
    def convert(uri: str) -> str:
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
def _make_band_dict(prod_cfg: OWSNamedLayer, pixel_dataset: xarray.Dataset) -> dict[str, dict[str, bool | str] | str]:
    band_dict: dict[str, dict[str, bool | str] | str] = {}
    for k, v in pixel_dataset.data_vars.items():
        band_val = pixel_dataset[k].item()
        flag_def = pixel_dataset[k].attrs.get("flags_definition")
        if flag_def:
            try:
                flag_dict = mask_to_dict(flag_def, band_val)
            except TypeError as te:
                logging.warning('Working around for float bands')
                flag_dict = mask_to_dict(flag_def, int(band_val))
            ret_val: dict[str, bool | str] = {}
            for flag, val in flag_dict.items():
                if not val:
                    continue
                if val == True:
                    ret_val[flag_def[flag].get('description', flag)] = True
                else:
                    ret_val[flag_def[flag].get('description', flag)] = val
            band_dict[k] = ret_val
        else:
            try:
                band_lbl = prod_cfg.band_idx.band_label(k)
                assert k is not None   # for type checker
                if band_val == pixel_dataset[k].nodata or numpy.isnan(band_val):
                    band_dict[band_lbl] = "n/a"
                else:
                    band_dict[band_lbl] = band_val
            except ConfigException:
                pass
    return band_dict


@log_call
def _make_derived_band_dict(pixel_dataset: xarray.Dataset, style_index: dict[str, StyleDef]) -> dict[str, int | float]:
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


def geobox_is_point(geobox: GeoBox) -> bool:
    return geobox.height == 1 and geobox.width == 1


@log_call
def feature_info(args: dict[str, str]) -> FlaskResponse:
    # pylint: disable=too-many-nested-blocks, too-many-branches, too-many-statements, too-many-locals
    # Parse GET parameters
    params = GetFeatureInfoParameters(args)
    feature_json: CFG_DICT = {}

    geo_point = img_coords_to_geopoint(params.geobox, params.i, params.j)
    # shrink geobox to point
    # Prepare to extract feature info
    if geobox_is_point(params.geobox):
        # request geobox is already 1x1
        geo_point_geobox = params.geobox
    else:
        # Make a 1x1 pixel geobox
        geo_point_geobox = GeoBox.from_geopolygon(
            geo_point, params.geobox.resolution, crs=params.geobox.crs)
    tz = tz_for_geometry(geo_point_geobox.geographic_extent)
    stacker = DataStacker(params.product, geo_point_geobox, params.times)
    # --- Begin code section requiring datacube.
    cfg = get_config()
    with cube() as dc:
        if not dc:
            raise WMSException("Database connectivity failure")
        all_time_datasets = cast(xarray.DataArray, stacker.datasets(dc.index, all_time=True, point=geo_point))

        # Taking the data as a single point so our indexes into the data should be 0,0
        h_coord = cfg.published_CRSs[params.crsid]["horizontal_coord"]
        v_coord = cfg.published_CRSs[params.crsid]["vertical_coord"]
        s3_bucket = cfg.s3_bucket
        s3_url = cfg.s3_url
        isel_kwargs = {
            h_coord: 0,
            v_coord: 0
        }
        if any(all_time_datasets):
            # Group datasets by time, load only datasets that match the idx_date
            global_info_written = False
            feature_json["data"] = []
            fi_date_index: dict[datetime, RAW_CFG] = {}
            time_datasets = cast(
                dict[ProductBandQuery, xarray.DataArray],
                stacker.datasets(dc.index, all_flag_bands=True, point=geo_point)
            )
            data = stacker.data(time_datasets, skip_corrections=True)
            if data is not None:
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
                        pt = geom.point(x, y, params.crs)

                        # Project to EPSG:4326
                        crs_geo = geom.CRS("EPSG:4326")
                        ptg = pt.to_crs(crs_geo)

                        # Capture lat/long coordinates
                        feature_json["lon"], feature_json["lat"] = ptg.coords[0]

                    date_info: CFG_DICT = {}

                    ds: Dataset | None = None
                    for pbq, dss in time_datasets.items():
                        if pbq.main:
                            ds = dss.sel(time=dt).values.tolist()[0]
                            break
                    assert ds is not None
                    if params.product.multi_product:
                        if "platform" in ds.metadata_doc:
                            date_info["source_product"] = "%s (%s)" % (ds.type.name, ds.metadata_doc["platform"]["code"])
                        else:
                            date_info["source_product"] = ds.type.name

                    # Extract data pixel
                    pixel_ds: xarray.Dataset = td.isel(**isel_kwargs)  # type: ignore[arg-type]

                    # Get accurate timestamp from dataset
                    assert ds.time is not None  # For type checker
                    if params.product.time_resolution.is_summary():
                        date_info["time"] = ds.time.begin.strftime("%Y-%m-%d")
                    else:
                        date_info["time"] = dataset_center_time(ds).strftime("%Y-%m-%d %H:%M:%S %Z")
                    # Collect raw band values for pixel and derived bands from styles
                    date_info["bands"] = cast(RAW_CFG, _make_band_dict(params.product, pixel_ds))
                    derived_band_dict = cast(RAW_CFG, _make_derived_band_dict(pixel_ds, params.product.style_index))
                    if derived_band_dict:
                        date_info["band_derived"] = derived_band_dict
                    # Add any custom-defined fields.
                    for k, f in params.product.feature_info_custom_includes.items():
                        date_info[k] = f(date_info["bands"])

                    cast(list[RAW_CFG], feature_json["data"]).append(date_info)
                    fi_date_index[dt] = cast(dict[str, list[RAW_CFG]], feature_json)["data"][-1]
            feature_json["data_available_for_dates"] = []
            pt_native = None
            for d in all_time_datasets.coords["time"].values:
                dt_datasets = all_time_datasets.sel(time=d)
                for ds in dt_datasets.values.item():
                    assert ds is not None  # For type checker
                    if pt_native is None:
                        pt_native = geo_point.to_crs(ds.crs)
                    elif pt_native.crs != ds.crs:
                        pt_native = geo_point.to_crs(ds.crs)
                    if ds.extent and ds.extent.contains(pt_native):
                        # tolist() converts a numpy datetime64 to a python datatime
                        dt = Timestamp(stacker.group_by.group_by_func(ds)).to_pydatetime()
                        if params.product.time_resolution.is_subday():
                            cast(list[RAW_CFG], feature_json["data_available_for_dates"]).append(dt.isoformat())
                        else:
                            cast(list[RAW_CFG], feature_json["data_available_for_dates"]).append(dt.strftime("%Y-%m-%d"))
                        break
            if time_datasets:
                feature_json["data_links"] = cast(
                    RAW_CFG,
                    sorted(get_s3_browser_uris(time_datasets, pt_native, s3_url, s3_bucket)))
            else:
                feature_json["data_links"] = []
            if params.product.feature_info_include_utc_dates:
                unsorted_dates: list[str] = []
                for tds in all_time_datasets:
                    for ds in tds.values.item():
                        assert ds is not None and ds.time is not None  # for type checker
                        if params.product.time_resolution.is_solar():
                            unsorted_dates.append(ds.center_time.strftime("%Y-%m-%d"))
                        elif params.product.time_resolution.is_subday():
                            unsorted_dates.append(ds.time.begin.isoformat())
                        else:
                            unsorted_dates.append(ds.time.begin.strftime("%Y-%m-%d"))
                feature_json["data_available_for_utc_dates"] = sorted(
                    d.center_time.strftime("%Y-%m-%d") for d in all_time_datasets)
    # --- End code section requiring datacube.

    result: CFG_DICT = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": feature_json,
                "geometry": {
                    "type": "Point",
                    "coordinates": geo_point.coords[0]
                }
            }
        ]
    }
    if params.format == "text/html":
        return html_json_response(result, cfg)
    else:
        return json_response(result, cfg)


def json_response(result: CFG_DICT, cfg: OWSConfig | None = None) -> FlaskResponse:
    if not cfg:
        cfg = get_config()
    assert cfg is not None  # for type checker
    return json.dumps(result), 200, cfg.response_headers({"Content-Type": "application/json"})


def html_json_response(result: CFG_DICT, cfg: OWSConfig | None = None) -> FlaskResponse:
    if not cfg:
        cfg = get_config()
    assert cfg is not None  # for type checker
    html_content = render_template("html_feature_info.html", result=result)
    return html_content, 200, cfg.response_headers({"Content-Type": "text/html"})
