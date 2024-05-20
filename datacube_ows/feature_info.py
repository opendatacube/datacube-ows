# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import logging
import re
from datetime import datetime
from itertools import chain
from typing import cast

import numpy
import xarray
from datacube.model import Dataset
from datacube.utils.masking import mask_to_dict
from odc.geo import geom
from odc.geo.geobox import GeoBox
from pandas import Timestamp

from datacube_ows.config_utils import CFG_DICT, RAW_CFG, ConfigException
from datacube_ows.http_utils import (FlaskResponse, html_json_response,
                                     json_response)
from datacube_ows.loading import DataStacker, ProductBandQuery
from datacube_ows.ows_configuration import OWSNamedLayer, get_config
from datacube_ows.styles import StyleDef
from datacube_ows.time_utils import dataset_center_time, tz_for_geometry
from datacube_ows.utils import log_call
from datacube_ows.wms_utils import (GetFeatureInfoParameters,
                                    img_coords_to_geopoint)


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
                        else:
                            pt_native = pt
                        if ds.extent.contains(pt_native):
                            uris.append(ds.uris)
                    else:
                        uris.append(ds.uris)
            break

    uris = list(chain.from_iterable(uris))
    unique_uris = set(uris)

    regex = re.compile(r"s3:\/\/(?P<bucket>[a-zA-Z0-9_\-\.]+)\/(?P<prefix>[\S]+)/[a-zA-Z0-9_\-\.]+.(yaml|json)")

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
    stacker = DataStacker(params.layer, geo_point_geobox, params.times)
    # --- Begin code section requiring datacube.
    cfg = get_config()
    all_time_datasets = cast(xarray.DataArray, stacker.datasets(params.layer.dc.index, all_time=True, point=geo_point))

    # Taking the data as a single point so our indexes into the data should be 0,0
    h_coord = cast(str, cfg.published_CRSs[params.crsid]["horizontal_coord"])
    v_coord = cast(str, cfg.published_CRSs[params.crsid]["vertical_coord"])
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
            stacker.datasets(params.layer.dc.index, all_flag_bands=True, point=geo_point)
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
                if params.layer.multi_product:
                    if "platform" in ds.metadata_doc:
                        date_info["source_product"] = "%s (%s)" % (ds.type.name, ds.metadata_doc["platform"]["code"])
                    else:
                        date_info["source_product"] = ds.type.name

                # Extract data pixel
                pixel_ds: xarray.Dataset = td.isel(**isel_kwargs)  # type: ignore[arg-type]

                # Get accurate timestamp from dataset
                assert ds.time is not None  # For type checker
                if params.layer.time_resolution.is_summary():
                    date_info["time"] = ds.time.begin.strftime("%Y-%m-%d")
                else:
                    date_info["time"] = dataset_center_time(ds).strftime("%Y-%m-%d %H:%M:%S %Z")
                # Collect raw band values for pixel and derived bands from styles
                date_info["bands"] = cast(RAW_CFG, _make_band_dict(params.layer, pixel_ds))
                derived_band_dict = cast(RAW_CFG, _make_derived_band_dict(pixel_ds, params.layer.style_index))
                if derived_band_dict:
                    date_info["band_derived"] = derived_band_dict
                # Add any custom-defined fields.
                for k, f in params.layer.feature_info_custom_includes.items():
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
                    if params.layer.time_resolution.is_subday():
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
        if params.layer.feature_info_include_utc_dates:
            unsorted_dates: list[str] = []
            for tds in all_time_datasets:
                for ds in tds.values.item():
                    assert ds is not None and ds.time is not None  # for type checker
                    if params.layer.time_resolution.is_solar():
                        unsorted_dates.append(ds.center_time.strftime("%Y-%m-%d"))
                    elif params.layer.time_resolution.is_subday():
                        unsorted_dates.append(ds.time.begin.isoformat())
                    else:
                        unsorted_dates.append(ds.time.begin.strftime("%Y-%m-%d"))
            feature_json["data_available_for_utc_dates"] = sorted(
                d.center_time.strftime("%Y-%m-%d") for d in all_time_datasets)

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
