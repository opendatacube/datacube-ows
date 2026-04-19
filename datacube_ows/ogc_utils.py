# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import logging
from typing import Any, cast

import numpy
from affine import Affine
from deprecat import deprecat
from odc.geo.geobox import GeoBox

TYPE_CHECKING = False
if TYPE_CHECKING:
    import datetime

    import xarray
    from odc.geo.crs import CRS

    from datacube_ows.config_utils import OWSExtensibleConfigEntry


_LOG: logging.Logger = logging.getLogger(__name__)


@deprecat(
    reason="The 'rolling_windows_ndays' mosaicing function has moved to 'datacube_ows.time_utils' - "
    "please import it from there.",
    version="1.9.0",
)
def rolling_window_ndays(
    available_dates: list[datetime.datetime],
    layer_cfg: OWSExtensibleConfigEntry,
    ndays: int = 6,
) -> tuple[datetime.datetime, datetime.datetime]:
    from datacube_ows.time_utils import rolling_window_ndays

    return rolling_window_ndays(
        available_dates=available_dates, layer_cfg=layer_cfg, ndays=ndays
    )


def mask_by_val(data: xarray.Dataset, band: str, val: Any = None) -> xarray.DataArray:
    """
    Mask by value.
    Value to mask by may be supplied, or is taken from 'nodata' metadata by default.

    :param val: The value to mask by, defaults to None, which means use the 'nodata' value in ODC metadata
    """
    if val is None:
        return data[band] != data[band].attrs["nodata"]
    return data[band] != val


def mask_by_val2(data: xarray.Dataset, band: str) -> xarray.DataArray:
    """
    Mask by value, using ODC canonical nodata value

    Usually (always?) equivalent to mask_by_val(data, band, val=None)
    """
    return data[band] != data[band].nodata


def mask_by_bitflag(data: xarray.Dataset, band: str) -> xarray.DataArray:
    """
    Mask by ODC metadata nodata value, as a bitflag
    """
    return ~data[band] & data[band].attrs["nodata"]


def mask_by_val_in_band(
    data: xarray.Dataset, band: str, mask_band: str, val: Any = None
) -> xarray.DataArray:
    """
    Mask all bands by a value in a particular band

    :param mask_band: The band to mask by
    :param val: The value to mask by (defaults to metadata 'nodata' for the maskband)
    """
    return mask_by_val(data, mask_band, val)


def mask_by_quality(data: xarray.Dataset, band: str) -> xarray.DataArray:
    """
    Mask by a quality band.

    Equivalent to mask_by_val_in_band(mask_band="quality")
    :param data:
    :param band:
    :return:
    """
    return mask_by_val(data, "quality")


def mask_by_extent_flag(data: xarray.Dataset, band: str) -> xarray.DataArray:
    """
    Mask by extent.

    Equivalent to mask_by_val_in_band(data, band, mask_band="extent", val=1)
    """
    return data["extent"] == 1


def mask_by_extent_val(data: xarray.Dataset, band: str) -> xarray.DataArray:
    """
    Mask by extent value using metadata nodata.

    Equivalent to mask_by_val_in_band(data, band, mask_band="extent")
    """
    return mask_by_val(data, "extent")


def mask_by_nan(data: xarray.Dataset, band: str) -> numpy.ndarray:
    """
    Mask by nan, for bands with floating point data
    """
    return ~numpy.isnan(cast("numpy.generic", data[band]))


# Example mosaic date function


# Sub-product extractors - Subproducts are currently unsupported
#
# ls8_s3_path_pattern = re.compile('L8/(?P<path>[0-9]*)')
#
# def ls8_subproduct(ds):
#     return int(ls8_s3_path_pattern.search(ds.uris[0]).group("path"))

# Method for formatting urls, e.g. for use in feature_info custom inclusions.


def create_geobox(
    crs: CRS,
    minx: float | int,
    miny: float | int,
    maxx: float | int,
    maxy: float | int,
    width: int | None = None,
    height: int | None = None,
) -> GeoBox:
    """
    Create an ODC Geobox.

    :param crs:  The CRS (name or object) to use.
    :param minx: The minimum X coordinate of the geobox.
    :param miny: The minimum Y coordinate of the geobox.
    :param maxx: The maximum X coordinate of the geobox.
    :param maxy: The maximum Y coordinate of the geobox.
    :param width: The width of the Geobox, in pixels
    :param height: The height of the Geobox, in pixels
    :return: An ODC geobox object
    """
    if width is None and height is None:
        raise ValueError("Must supply at least a width or height")
    if height is not None:
        scale_y = (float(miny) - float(maxy)) / height
    if width is not None:
        scale_x = (float(maxx) - float(minx)) / width
    else:
        scale_x = -scale_y  # pylint: disable=possibly-used-before-assignment
        width = round((float(maxx) - float(minx)) / scale_x)
    if height is None:
        scale_y = -scale_x
        height = round((float(miny) - float(maxy)) / scale_y)
    affine = Affine.translation(minx, maxy) * Affine.scale(scale_x, scale_y)
    return GeoBox((height, width), affine, crs)
