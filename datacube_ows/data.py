# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from io import BytesIO
from typing import Any

import numpy
import numpy.ma
import xarray
from pandas import Timestamp
from PIL import Image
from rasterio.features import rasterize
from rasterio.io import MemoryFile

from datacube_ows.http_utils import json_response, png_response
from datacube_ows.loading import DataStacker
from datacube_ows.ogc_exceptions import WMSException
from datacube_ows.query_profiler import QueryProfiler
from datacube_ows.resource_limits import ResourceLimited
from datacube_ows.time_utils import solar_date, tz_for_geometry
from datacube_ows.utils import default_to_utc, log_call
from datacube_ows.wms_utils import GetMapParameters

TYPE_CHECKING = False
if TYPE_CHECKING:
    from odc.geo import geom
    from odc.geo.geobox import GeoBox

    from datacube_ows.ows_configuration import OWSConfig, OWSNamedLayer
    from datacube_ows.protocol_versions import FlaskResponse
    from datacube_ows.styles import StyleDef


_LOG: logging.Logger = logging.getLogger(__name__)


def user_date_sorter(
    layer: OWSNamedLayer,
    odc_dates: list[datetime],
    geometry: geom.Geometry,
    user_dates: list[datetime],
) -> xarray.DataArray:
    # TODO: Make more elegant.  Just a little bit elegant would do.
    result = []
    tz = tz_for_geometry(geometry) if layer.time_resolution.is_solar() else None

    def check_date(time_res, user_date, odc_date) -> bool:
        ts = Timestamp(odc_date).tz_localize("UTC")
        if time_res.is_solar():
            assert tz is not None
            norm_date = solar_date(ts, tz)
            return norm_date == user_date
        if time_res.is_summary():
            norm_date = date(ts.year, ts.month, ts.day)
            return norm_date == user_date
        norm_date = datetime(
            ts.year, ts.month, ts.day, ts.hour, ts.minute, ts.second, tzinfo=ts.tzinfo
        )
        user_date = default_to_utc(user_date)
        return user_date >= norm_date and user_date < norm_date + timedelta(
            hours=23, minutes=59, seconds=59
        )

    for odc_date in odc_dates:
        for idx, user_date in enumerate(user_dates):
            if check_date(layer.time_resolution, user_date, odc_date):
                result.append(idx)
                break
    npresult = numpy.array(result, dtype="uint8")
    return xarray.DataArray(
        npresult, coords={"time": odc_dates}, dims=["time"], name="user_date_sorter"
    )


class EmptyResponse(Exception):
    pass


@log_call
def get_map(cfg: OWSConfig, args: dict[str, str]) -> FlaskResponse:
    # pylint: disable=too-many-nested-blocks, too-many-branches, too-many-statements, too-many-locals
    # Parse GET parameters
    try:
        params = GetMapParameters(cfg, args)
    except ValueError as e:
        # See #1478 for one example that brings us here.
        raise WMSException("Failed to get map parameters") from e
    qprof = QueryProfiler(params.ows_stats)
    n_dates = len(params.times)
    if n_dates == 1:
        mdh = None
    else:
        mdh = params.style.get_multi_date_handler(n_dates)
        if mdh is None:
            raise WMSException(
                f"Style {params.style.name} does not support GetMap "
                f"requests with {n_dates} dates",
                WMSException.INVALID_DIMENSION_VALUE,
                locator="Time parameter",
            )
    qprof["n_dates"] = n_dates
    # Tiling.
    try:
        stacker = DataStacker(
            params.layer,
            params.geobox,
            params.times,
            params.resampling,
            style=params.style,
        )
    except ValueError as e:
        # TimeZoneFinder raises a ValueError when lat/lon is out of bounds.
        # There is already a warning logged for the problem so just raise here.
        raise WMSException("Error creating DataStacker") from e
    qprof["zoom_factor"] = params.zf
    qprof.start_event("count-datasets")
    n_datasets = stacker.n_datasets()
    qprof.end_event("count-datasets")
    qprof["n_datasets"] = n_datasets
    try:
        qprof["zoom_level_base"] = params.resources.base_zoom_level
        qprof["zoom_level_adjusted"] = params.resources.load_adjusted_zoom_level
    except ValueError as e:
        # Non-closed polygon can bring us here.
        raise WMSException("Error getting zoom level") from e
    try:
        params.layer.resource_limits.check_wms(n_datasets, params.zf, params.resources)
    except ResourceLimited as e:
        stacker.resource_limited = True
        qprof["resource_limited"] = str(e)
    try:
        if qprof.active:
            q_ds_dict = stacker.datasets()
            qprof["datasets"] = []
            for q, dsxr in q_ds_dict.items():
                query_res: dict[str, Any] = {
                    "query": str(q),
                    "datasets": [
                        [f"{ds.id} ({ds.product.name})" for ds in tdss]
                        for tdss in dsxr.values
                    ],
                }
                qprof["datasets"].append(query_res)
        if stacker.resource_limited and not params.layer.low_res_product_names:
            qprof.start_event("extent-in-query")
            extent = stacker.extent(crs=params.crs)
            qprof.end_event("extent-in-query")
            if extent is None:
                qprof["write_action"] = "No extent: Write Empty"
                raise EmptyResponse()
            qprof["write_action"] = "Polygon"
            qprof.start_event("write")
            body = _write_polygon(
                params.geobox,
                extent,
                params.layer.resource_limits.zoom_fill,
                params.layer,
            )
            qprof.end_event("write")
        elif n_datasets == 0:
            qprof["write_action"] = "No datasets: Write Empty"
            raise EmptyResponse()
        else:
            if stacker.resource_limited:
                qprof.start_event("count-summary-datasets")
                qprof["n_summary_datasets"] = stacker.n_datasets()
                qprof.end_event("count-summary-datasets")
            qprof.start_event("fetch-datasets")
            datasets = stacker.datasets()
            for flagband, dss in datasets.items():
                if not dss.any():
                    _LOG.warning("Flag band %s returned no data", str(flagband))
                if len(dss.time) != n_dates and flagband.main:
                    qprof["write_action"] = (
                        f"{n_dates} requested, only {len(dss.time)} found - returning empty image"
                    )
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
                        if params.layer.data_manual_merge:
                            if td_ext_mask_man is None:
                                td_ext_mask_man = ~numpy.isnan(td[band])
                            else:
                                td_ext_mask_man &= ~numpy.isnan(td[band])
                        else:
                            for f in params.layer.extent_mask_func:
                                if td_ext_mask is None:
                                    td_ext_mask = f(td, band)
                                else:
                                    td_ext_mask &= f(td, band)
                if params.layer.data_manual_merge:
                    td_ext_mask = xarray.DataArray(td_ext_mask_man)
                if td_ext_mask is None:
                    td_ext_mask = xarray.DataArray(
                        ~numpy.zeros(td[band].values.shape, dtype=numpy.bool_),
                        td[band].coords,
                    )
                td_masks.append(td_ext_mask)
            extent_mask = xarray.concat(td_masks, dim=data.time)
            qprof.end_event("build-masks")
            qprof["write_action"] = "Write Data"
            if mdh and mdh.preserve_user_date_order:
                sorter = user_date_sorter(
                    params.layer,
                    data.time.values,
                    params.geobox.geographic_extent,
                    params.times,  # type: ignore[arg-type]
                )
                data = data.sortby(sorter)
                extent_mask = extent_mask.sortby(sorter)

            body = _write_png(data, params.style, extent_mask, qprof)
    except EmptyResponse:
        qprof.start_event("write")
        body = _write_empty(params.geobox)
        qprof.end_event("write")

    if params.ows_stats:
        return json_response(qprof.profile(), cfg)
    return png_response(
        body,
        cfg,
        extra_headers=params.layer.resource_limits.wms_cache_rules.cache_headers(
            n_datasets
        ),
    )


@log_call
def _write_png(
    data: xarray.Dataset,
    style: StyleDef,
    extent_mask: xarray.DataArray,
    qprof: QueryProfiler,
) -> bytes:
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
        image = xarray_image_as_png(
            img_data, loop_over="time", animate=True, frame_duration=mdh.frame_duration
        )
    else:
        image = xarray_image_as_png(img_data)
    qprof.end_event("write")
    return image


@log_call
def _write_empty(geobox: GeoBox) -> bytes:
    with MemoryFile() as memfile:
        with memfile.open(
            driver="PNG",
            width=geobox.width,
            height=geobox.height,
            count=1,
            transform=None,
            nodata=0,
            dtype="uint8",
        ):
            pass
        return memfile.read()


@log_call
def _write_polygon(
    geobox: GeoBox, polygon: geom.Geometry, zoom_fill: list[int], layer: OWSNamedLayer
) -> bytes:
    geobox_ext = geobox.extent
    if geobox_ext.within(polygon):
        data = numpy.full([geobox.height, geobox.width], fill_value=1, dtype="uint8")
    else:
        data = numpy.zeros([geobox.height, geobox.width], dtype="uint8")
        data = rasterize(
            shapes=[polygon], fill=0, default_value=2, out=data, transform=geobox.affine
        )
    with MemoryFile() as memfile:
        with memfile.open(
            driver="PNG",
            width=geobox.width,
            height=geobox.height,
            count=4,
            transform=None,
            nodata=0,
            dtype="uint8",
        ) as thing:
            for idx, fill in enumerate(zoom_fill, start=1):
                thing.write_band(idx, data * fill)
        return memfile.read()


def xarray_image_as_png(
    img_data: xarray.Dataset,
    loop_over=None,
    animate: bool = False,
    frame_duration: int = 1000,
):
    """
    Render an Xarray image as a PNG.

    :param img_data: An xarray dataset, containing 3 or 4 uint8 variables: red, green,
                blue, and optionally alpha.
    :param loop_over: Optional name of a dimension on img_data.  If set,
                xarray_image_as_png is called in a loop over all coordinate values for
                the named dimension.
    :param animate: Optional generate animated PNG
    :return: A list of bytes representing a PNG image file. (Or a list of lists of
                bytes, if loop_over was set.)
    """
    if loop_over and not animate:
        return [
            xarray_image_as_png(img_data.sel(**{loop_over: coord}))
            for coord in img_data.coords[loop_over].values
        ]
    xcoord = None
    ycoord = None
    for cc in ("x", "longitude", "Longitude", "long", "lon"):
        if cc in img_data.coords:
            xcoord = cc
            break
    for cc in ("y", "latitude", "Latitude", "lat"):
        if cc in img_data.coords:
            ycoord = cc
            break
    if not xcoord or not ycoord:
        raise ValueError("Could not identify spatial coordinates")
    width = len(img_data.coords[xcoord])
    height = len(img_data.coords[ycoord])
    img_io = BytesIO()
    # Render XArray to APNG via Pillow
    # https://pillow.readthedocs.io/en/stable/handbook/image-file-formats.html#apng-sequences
    if loop_over and animate:
        time_slices_array = [
            xarray_image_as_png(img_data.sel(**{loop_over: coord}), animate=True)
            for coord in img_data.coords[loop_over].values
        ]
        images = []

        for t_slice in time_slices_array:
            im = Image.fromarray(t_slice)
            images.append(im)
        images[0].save(
            img_io,
            "PNG",
            save_all=True,
            default_image=True,
            loop=0,
            duration=frame_duration,
            append_images=images,
        )
        img_io.seek(0)
        return img_io.read()

    if "time" in img_data.dims:
        img_data = img_data.squeeze(dim="time", drop=True)

    pillow_data = render_frame(img_data.transpose(xcoord, ycoord), width, height)
    if not loop_over and animate:
        return pillow_data

    # Change PNG rendering to Pillow
    im_final = Image.fromarray(pillow_data)
    im_final.save(img_io, "PNG")
    img_io.seek(0)
    return img_io.read()


def render_frame(img_data: xarray.Dataset, width: int, height: int) -> numpy.ndarray:
    """Render to a 3D numpy array an Xarray RGB(A) Dataset input

    Args:
        img_data ([type]): Input 3D XArray
        width ([type]): Width of the frame to render
        height ([type]): Height of the frame to render

    Returns:
        numpy.ndarray: 3D Rendered Xarray as numpy array
    """
    masked = False
    last_band = None
    buffer = numpy.zeros((4, width, height), numpy.uint8)
    band_index = {"red": 0, "green": 1, "blue": 2, "alpha": 3}
    for band_var in img_data.data_vars:
        band = str(band_var)
        index = band_index[band]
        band_data = img_data[band].values
        if band == "alpha":
            masked = True
        buffer[index, :, :] = band_data
        last_band = band_data
    if not masked:
        assert last_band is not None  # For typechecker.
        alpha_mask = numpy.empty(last_band.shape).astype("uint8")
        alpha_mask.fill(255)
        buffer[3, :, :] = alpha_mask
    return buffer.transpose()
