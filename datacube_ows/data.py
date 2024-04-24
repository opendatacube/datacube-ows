# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import logging
from datetime import date, datetime, timedelta
from typing import Any, cast

import numpy
import numpy.ma
import pytz
import xarray
from odc.geo import geom
from odc.geo.geobox import GeoBox
from pandas import Timestamp
from rasterio.features import rasterize
from rasterio.io import MemoryFile

from datacube_ows.cube_pool import cube
from datacube_ows.http_utils import FlaskResponse, json_response, png_response
from datacube_ows.loading import DataStacker, ProductBandQuery
from datacube_ows.mv_index import MVSelectOpts
from datacube_ows.ogc_exceptions import WMSException
from datacube_ows.ogc_utils import xarray_image_as_png
from datacube_ows.ows_configuration import OWSNamedLayer
from datacube_ows.query_profiler import QueryProfiler
from datacube_ows.resource_limits import ResourceLimited
from datacube_ows.styles import StyleDef
from datacube_ows.time_utils import solar_date, tz_for_geometry
from datacube_ows.utils import default_to_utc, log_call
from datacube_ows.wms_utils import GetMapParameters

_LOG = logging.getLogger(__name__)


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
                             ts.day)
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
