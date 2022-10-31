# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import datetime
import logging
from importlib import import_module
from io import BytesIO
from itertools import chain
from typing import (Any, Callable, Mapping, MutableMapping, Optional, Sequence,
                    Tuple, TypeVar, Union, cast)
from urllib.parse import urlparse

import numpy
from affine import Affine
from datacube.utils import geometry
from dateutil.parser import parse
from flask import request
from PIL import Image
from pytz import timezone, utc
from timezonefinderL import TimezoneFinder

_LOG: logging.Logger = logging.getLogger(__name__)
tf = TimezoneFinder(in_memory=True)


def dataset_center_time(dataset: "datacube.model.Dataset") -> datetime.datetime:
    """
    Determine a center_time for the dataset

    Use metadata time if possible as this is what WMS uses to calculate it's temporal extents
    datacube-core center time accessed through the dataset API is calculated and may
    not agree with the metadata document.

    :param dataset:  An ODC dataset.
    :return: A datetime object representing the datasets center time
    """
    center_time: datetime.datetime = dataset.center_time
    try:
        metadata_time: str = dataset.metadata_doc['extent']['center_dt']
        center_time = parse(metadata_time)
    except KeyError:
        try:
            metadata_time: str = dataset.metadata_doc['properties']['dtr:start_datetime']
            center_time = parse(metadata_time)
        except KeyError:
            pass
    return center_time


class NoTimezoneException(Exception):
    """Exception, raised internally if no timezone can be found"""


def solar_date(dt: datetime.datetime, tz: datetime.tzinfo) -> datetime.date:
    """
    Convert a datetime to a new timezone, and evalute as a date.

    :param dt: A datetime in an aribitrary timezone.
    :param tz: The timezone to evaluate the date in.
    :return: A date object.
    """
    return dt.astimezone(tz).date()


def local_date(ds: "datacube.model.Dataset", tz: Optional[datetime.tzinfo] = None) -> datetime.date:
    """
    Calculate the local (solar) date for a dataset.

    :param ds: An ODC dataset object
    :param tz: (optional) A timezone object. If not provided, determine the timezone from extent of the dataset.
    :return: A date object.
    """
    dt_utc: datetime.datetime = dataset_center_time(ds)
    if not tz:
        tz = tz_for_geometry(ds.extent)
    return solar_date(dt_utc, tz)


def tz_for_dataset(ds: "datacube.model.Dataset") -> datetime.tzinfo:
    """
    Determine the timezone for a dataset (using it's extent)

    :param ds: An ODC dataset object
    :return: A timezone object
    """
    return tz_for_geometry(ds.extent)


def tz_for_coord(lon: Union[float, int], lat: Union[float, int]) -> datetime.tzinfo:
    """
    Determine the Timezone for given lat/long coordinates

    :param lon: Longitude, in degress
    :param lat: Latitude, in degrees
    :return: A timezone object
    :raises: NoTimezoneException
    """
    try:
        tzn: Optional[str] = tf.timezone_at(lng=lon, lat=lat)
    except Exception as e:
        # Generally shouldn't happen - a common symptom of various geographic and timezone related bugs
        _LOG.warning("Timezone detection failed for lat %f, lon %s (%s)", lat, lon, str(e))
        raise
    if not tzn:
        raise NoTimezoneException("tz find failed.")
    return timezone(tzn)


def local_solar_date_range(geobox: geometry.GeoBox, date: datetime.date) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    Converts a date to a local solar date datetime range.

    :param geobox: Geometry used to determine the appropriate timezone for local date conversion
    :param date: A date object
    :return: A tuple of two UTC datetime objects, spanning 1 second shy of 24 hours.
    """
    tz: datetime.tzinfo = tz_for_geometry(geobox.geographic_extent)
    start = datetime.datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=tz)
    end = datetime.datetime(date.year, date.month, date.day, 23, 59, 59, tzinfo=tz)
    return (start.astimezone(utc), end.astimezone(utc))


def month_date_range(date: datetime.date) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    Take a month from a date and convert to a one month long UTC datetime range encompassing the month.

    Ignores timezone effects - suitable for statistical/summary data

    :param date: A date or datetime object to take the month and year from
    :return: A tuple of two UTC datetime objects, delimiting an entire calendar month.
    """
    start = datetime.datetime(date.year, date.month, 1, 0, 0, 0, tzinfo=utc)
    y: int = date.year
    m: int = date.month + 1
    if m == 13:
        m = 1
        y = y + 1
    end = datetime.datetime(y, m, 1, 0, 0, 0, tzinfo=utc) - datetime.timedelta(days=1)
    return start, end


def year_date_range(date: datetime.date) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    Convert a date to a UTC datetime range encompassing the calendar year including the date.

    Ignores timezone effects - suitable for statistical/summary data

    :param date: A date or datetime object to take the year from
    :return: A tuple of two UTC datetime objects, delimiting an entire calendar year.
    """
    start = datetime.datetime(date.year, 1, 1, 0, 0, 0, tzinfo=utc)
    end = datetime.datetime(date.year, 12, 31, 23, 59, 59, tzinfo=utc)
    return start, end


def day_summary_date_range(date: datetime.date) -> Tuple[datetime.datetime, datetime.datetime]:
    """
    Convert a date to a UTC datetime range encompassing the calendar date.

    Ignores timezone effects - suitable for statistical/summary data

    :param date: A date or datetime object to take the day, month and year from
    :return: A tuple of two UTC datetime objects, delimiting a calendar day.
    """
    start = datetime.datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=utc)
    end = datetime.datetime(date.year, date.month, date.day, 23, 59, 59, tzinfo=utc)
    return start, end


def tz_for_geometry(geom: geometry.Geometry) -> datetime.tzinfo:
    """
    Determine the timezone from a geometry.  Be clever if we can,
    otherwise use a minimal timezone based on the longitude.

    :param geom: A geometry object
    :return: A timezone object
    """
    crs_geo = geometry.CRS("EPSG:4326")
    geo_geom: geometry.Geometry = geom.to_crs(crs_geo)
    centroid: geometry.Geometry = geo_geom.centroid
    try:
        # 1. Try being smart with the centroid of the geometry
        return tz_for_coord(centroid.coords[0][0], centroid.coords[0][1])
    except NoTimezoneException:
        pass
    for pt in geo_geom.boundary.coords:
        try:
            # 2. Try being smart all the points in the geometry
            return tz_for_coord(pt[0], pt[1])
        except NoTimezoneException:
            pass
    # 3. Meh, just use longitude
    offset = round(centroid.coords[0][0] / 15.0)
    return datetime.timezone(datetime.timedelta(hours=offset))


def resp_headers(d: Mapping[str, str]) -> Mapping[str, str]:
    """
    Take a dictionary of http response headers and all required response headers from the configuration.

    :param d:
    :return:
    """
    from datacube_ows.ows_configuration import get_config
    return get_config().response_headers(d)


F = TypeVar('F', bound=Callable[..., Any])


def get_function(func: Union[F, str]) -> F:
    """Converts a config entry to a function, if necessary

    :param func: Either a Callable object or a fully qualified function name str, or None
    :return: a Callable object, or None
    """
    if func is not None and not callable(func):
        mod_name, func_name = func.rsplit('.', 1)
        try:
            mod = import_module(mod_name)
            func = getattr(mod, func_name)
        except (ImportError, ModuleNotFoundError, ValueError, AttributeError):
            raise ConfigException(f"Could not import python object: {func}")
        assert callable(func)
    return cast(F, func)


def parse_for_base_url(url: str) -> str:
    """
    Extract the base URL from a URL

    :param url: A URL
    :return: The base URL (path and parameters stripped)
    """
    parsed = urlparse(url)
    parsed = (parsed.netloc + parsed.path).rstrip("/")
    return parsed


def get_service_base_url(allowed_urls: Union[Sequence[str], str], request_url: str) -> str:
    """
    Choose the base URL to advertise in XML.

    :param allowed_urls: A list of allowed URLs, or a single allowed URL.
    :param request_url: The URL the incoming request came from
    :return: Return one of the allowed URLs.  Either one that seems to match the request, or the first in the list
    """
    if isinstance(allowed_urls, str):
        return allowed_urls
    parsed_request_url = parse_for_base_url(request_url)
    parsed_allowed_urls = [parse_for_base_url(u) for u in allowed_urls]
    try:
        idx: Optional[int] = parsed_allowed_urls.index(parsed_request_url)
    except ValueError:
        idx = None
    url = allowed_urls[idx] if idx is not None else allowed_urls[0]
    # template includes tailing /, strip any trail slash here to avoid duplicates
    url = url.rstrip("/")
    return url


# Collects additional headers from flask request objects
def capture_headers(req: "flask.Request",
                    args_dict: MutableMapping[str, Optional[str]]) \
        -> MutableMapping[str, Optional[str]]:
    """
    Capture significant flask metadata into the args dictionary

    :param req: A Flask request
    :param args_dict: A Flask args dictionary
    :return:
    """
    args_dict['referer'] = req.headers.get('Referer', None)
    args_dict['origin'] = req.headers.get('Origin', None)
    args_dict['requestid'] = req.environ.get("FLASK_REQUEST_ID")
    args_dict['host'] = req.headers.get('Host', None)
    args_dict['url_root'] = req.url_root

    return args_dict


class ConfigException(Exception):
    """
    General exception for OWS Configuration issues.
    """


# Function wrapper for configurable functional elements


class FunctionWrapper:
    """
    Function wrapper for configurable functional elements
    """

    def __init__(self,
                 product_or_style_cfg: Union[
                     "datacube_ows.ows_configuration.OWSNamedLayer", "datacube_ows.styles.StyleDef"],
                 func_cfg: Union[F, Mapping[str, Any]],
                 stand_alone: bool = False) -> None:
        """

        :param product_or_style_cfg: An instance of either NamedLayer or Style,
                the context in which the wrapper operates.
        :param func_cfg: A function or a configuration dictionary representing a function.
        :param stand_alone: Optional boolean.
                If False (the default) then only configuration dictionaries will be accepted.
        """
        if callable(func_cfg):
            if not stand_alone:
                raise ConfigException(
                    "Directly including callable objects in configuration is no longer supported. Please reference callables by fully qualified name.")
            self._func = func_cfg
            self._args = []
            self._kwargs = {}
            self.band_mapper = None
        elif isinstance(func_cfg, str):
            self._func = get_function(func_cfg)
            self._args = []
            self._kwargs = {}
            self.band_mapper = None
        else:
            if stand_alone and callable(func_cfg["function"]):
                self._func = func_cfg["function"]
            elif callable(func_cfg["function"]):
                raise ConfigException(
                    "Directly including callable objects in configuration is no longer supported. Please reference callables by fully qualified name.")
            else:
                self._func = get_function(func_cfg["function"])
            self._args = func_cfg.get("args", [])
            self._kwargs = func_cfg.get("kwargs", {}).copy()
            if "pass_product_cfg" in func_cfg:
                _LOG.warning("WARNING: pass_product_cfg in function wrapper definitions has been renamed "
                             "'mapped_bands'.  Please update your config accordingly")
            if func_cfg.get("mapped_bands", func_cfg.get("pass_product_cfg", False)):
                if hasattr(product_or_style_cfg, "band_idx"):
                    # NamedLayer
                    named_layer = cast("datacube_ows.ows_configuration.OWSNamedLayer",
                                       product_or_style_cfg)
                    b_idx = named_layer.band_idx
                    self.band_mapper = b_idx.band
                else:
                    # Style
                    style = cast("datacube_ows.styles.StyleDef", product_or_style_cfg)
                    b_idx = style.product.band_idx
                    delocaliser = style.local_band
                    self.band_mapper = lambda b: b_idx.band(delocaliser(b))
            else:
                self.band_mapper = None

    def __call__(self, *args, **kwargs) -> Any:
        if args and self._args:
            calling_args = chain(args, self._args)
        elif args:
            calling_args = args
        else:
            calling_args = self._args
        if kwargs and self._kwargs:
            calling_kwargs = self._kwargs.copy()
            calling_kwargs.update(kwargs)
        elif kwargs:
            calling_kwargs = kwargs.copy()
        else:
            calling_kwargs = self._kwargs.copy()

        if self.band_mapper:
            calling_kwargs["band_mapper"] = self.band_mapper

        return self._func(*calling_args, **calling_kwargs)


def cache_control_headers(max_age: int) -> str:
    if max_age <= 0:
        return {"cache-control": "no-cache"}
    else:
        return {"cache-control": f"max-age={max_age}"}


# Extent Mask Functions

def mask_by_val(data: "xarray.Dataset", band: str, val: Optional[Any] = None) -> "xarray.DataArray":
    """
    Mask by value.
    Value to mask by may be supplied, or is taken from 'nodata' metadata by default.

    :param val: The value to mask by, defaults to None, which means use the 'nodata' value in ODC metadata
    """
    if val is None:
        return data[band] != data[band].attrs['nodata']
    else:
        return data[band] != val


def mask_by_val2(data: "xarray.Dataset", band: str) -> "xarray.DataArray":
    """
    Mask by value, using ODC canonical nodata value

    Usually (always?) equivalent to mask_by_val(data, band, val=None)
    """
    return data[band] != data[band].nodata


def mask_by_bitflag(data: "xarray.Dataset", band: str) -> "xarray.DataArray":
    """
    Mask by ODC metadata nodata value, as a bitflag
    """
    return ~data[band] & data[band].attrs['nodata']


def mask_by_val_in_band(data: "xarray.Dataset", band: str, mask_band: str, val: Any = None) -> "xarray.DataArray":
    """
    Mask all bands by a value in a particular band

    :param mask_band: The band to mask by
    :param val: The value to mask by (defaults to metadata 'nodata' for the maskband)
    """
    return mask_by_val(data, mask_band, val)


def mask_by_quality(data: "xarray.Dataset", band: str) -> "xarray.DataArray":
    """
    Mask by a quality band.

    Equivalent to mask_by_val_in_band(mask_band="quality")
    :param data:
    :param band:
    :return:
    """
    return mask_by_val(data, "quality")


def mask_by_extent_flag(data: "xarray.Dataset", band: str) -> "xarray.DataArray":
    """
    Mask by extent.

    Equivalent to mask_by_val_in_band(data, band, mask_band="extent", val=1)
    """
    return data["extent"] == 1


def mask_by_extent_val(data: "xarray.Dataset", band: str) -> "xarray.DataArray":
    """
    Mask by extent value using metadata nodata.

    Equivalent to mask_by_val_in_band(data, band, mask_band="extent")
    """
    return mask_by_val(data, "extent")


def mask_by_nan(data: "xarray.Dataset", band: str) -> "numpy.NDArray":
    """
    Mask by nan, for bands with floating point data
    """
    return ~numpy.isnan(cast(numpy.generic, data[band]))


# Sub-product extractors - Subproducts are currently unsupported
#
# ls8_s3_path_pattern = re.compile('L8/(?P<path>[0-9]*)')
#
# def ls8_subproduct(ds):
#     return int(ls8_s3_path_pattern.search(ds.uris[0]).group("path"))

# Method for formatting urls, e.g. for use in feature_info custom inclusions.


def lower_get_args() -> MutableMapping[str, str]:
    """
    Return Flask request arguments, with argument names converted to lower case.

    Get parameters in WMS are case-insensitive, and intended to be single use.
    Spec does not specify which instance should be used if a parameter is provided more than once.
    This function uses the LAST instance.
    """
    d = {}
    for k in request.args.keys():
        kl = k.lower()
        for v in request.args.getlist(k):
            d[kl] = v
    return d


def create_geobox(
        crs: geometry.CRS,
        minx: Union[float, int], miny: Union[float, int],
        maxx: Union[float, int], maxy: Union[float, int],
        width: Optional[int] = None, height: Optional[int] = None,
) -> geometry.GeoBox:
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
    return geometry.GeoBox(width, height, affine, crs)


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
