# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import logging
import datetime
from io import BytesIO
from typing import Any, cast
from deprecat import deprecat
import numpy
import xarray
from affine import Affine
from odc.geo.geobox import GeoBox
from odc.geo.geom import CRS
from PIL import Image
TYPE_CHECKING = False
if TYPE_CHECKING:
    from datacube_ows.config_utils import OWSExtensibleConfigEntry


_LOG: logging.Logger = logging.getLogger(__name__)


@deprecat(
    reason="The 'rolling_windows_ndays' mosaicing function has moved to 'datacube.time_utils' - "
           "please import it from there.",
    version="1.9.0"
)
def rolling_window_ndays(
        available_dates: list[datetime.datetime],
        layer_cfg: "OWSExtensibleConfigEntry",
        ndays: int = 6) -> tuple[datetime.datetime, datetime.datetime]:
    from datacube_ows.time_utils import rolling_window_ndays
    return rolling_window_ndays(available_dates=available_dates,
                                layer_cfg=layer_cfg,
                                ndays=ndays)


def mask_by_val(data: xarray.Dataset, band: str, val: Any = None) -> xarray.DataArray:
    """
    Mask by value.
    Value to mask by may be supplied, or is taken from 'nodata' metadata by default.

    :param val: The value to mask by, defaults to None, which means use the 'nodata' value in ODC metadata
    """
    if val is None:
        return data[band] != data[band].attrs['nodata']
    else:
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
    return ~data[band] & data[band].attrs['nodata']


def mask_by_val_in_band(data: xarray.Dataset, band: str, mask_band: str, val: Any = None) -> xarray.DataArray:
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
    return ~numpy.isnan(cast(numpy.generic, data[band]))


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
        minx: float | int, miny: float | int,
        maxx: float | int, maxy: float | int,
        width: int | None = None, height: int | None = None,
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
        raise Exception("Must supply at least a width or height")
    if height is not None:
        scale_y = (float(miny) - float(maxy)) / height
    if width is not None:
        scale_x = (float(maxx) - float(minx)) / width
    else:
        scale_x = -scale_y
        width = int(round((float(maxx) - float(minx)) / scale_x))
    if height is None:
        scale_y = - scale_x
        height = int(round((float(miny) - float(maxy)) / scale_y))
    affine = Affine.translation(minx, maxy) * Affine.scale(scale_x, scale_y)
    return GeoBox((height, width), affine, crs)


def xarray_image_as_png(img_data, loop_over=None, animate=False, frame_duration=1000):
    """
    Render an Xarray image as a PNG.

    :param img_data: An xarray dataset, containing 3 or 4 uint8 variables: red, greed, blue, and optionally alpha.
    :param loop_over: Optional name of a dimension on img_data.  If set, xarray_image_as_png is called in a loop
                over all coordinate values for the named dimension.
    :param animate: Optional generate animated PNG
    :return: A list of bytes representing a PNG image file. (Or a list of lists of bytes, if loop_over was set.)
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
        raise Exception("Could not identify spatial coordinates")
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
            im = Image.fromarray(t_slice, "RGBA")
            images.append(im)
        images[0].save(img_io, "PNG", save_all=True, default_image=True, loop=0, duration=frame_duration, append_images=images)
        img_io.seek(0)
        return img_io.read()

    if "time" in img_data.dims:
        img_data = img_data.squeeze(dim="time", drop=True)

    pillow_data = render_frame(img_data.transpose(xcoord, ycoord), width, height)
    if not loop_over and animate:
        return pillow_data

    # Change PNG rendering to Pillow
    im_final = Image.fromarray(pillow_data, "RGBA")
    im_final.save(img_io, "PNG")
    img_io.seek(0)
    return img_io.read()


def render_frame(img_data, width, height):
    """Render to a 3D numpy array an Xarray RGB(A) input

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
    band_index = {
        "red": 0,
        "green": 1,
        "blue": 2,
        "alpha": 3,
    }
    for band in img_data.data_vars:
        index = band_index[band]
        band_data = img_data[band].values
        if band == "alpha":
            masked = True
        buffer[index, :, :] = band_data
        index += 1
        last_band = band_data
    if not masked:
        alpha_mask = numpy.empty(last_band.shape).astype('uint8')
        alpha_mask.fill(255)
        buffer[3, :, :] = alpha_mask
    return buffer.transpose()
