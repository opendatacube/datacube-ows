from __future__ import absolute_import, division, print_function

import re
import datetime
from importlib import import_module
from itertools import chain

from dateutil.parser import parse
from urllib.parse import urlparse
from timezonefinderL import TimezoneFinder
from datacube.utils import geometry
from pytz import timezone, utc

import logging

_LOG = logging.getLogger(__name__)


tf = TimezoneFinder(in_memory=True)

# Use metadata time if possible as this is what WMS uses to calculate it's temporal extents
# datacube-core center time accessed through the dataset API is calculated and may
# not agree with the metadata document
def dataset_center_time(dataset):
    center_time = dataset.center_time
    try:
        metadata_time = dataset.metadata_doc['extent']['center_dt']
        center_time = parse(metadata_time)
    except KeyError:
        try:
            metadata_time = dataset.metadata_doc['properties']['dtr:start_datetime']
            center_time = parse(metadata_time)
        except KeyError:
            pass
    return center_time


class NoTimezoneException(Exception):
    pass


def solar_date(dt, tz):
    return dt.astimezone(tz).date()


def local_date(ds, tz=None):
    dt_utc = dataset_center_time(ds)
    if tz:
        return dt_utc.astimezone(tz).date()
    else:
        return dt_utc.astimezone(tz_for_geometry(ds.extent)).date()


def tz_for_dataset(ds):
    return tz_for_geometry(ds.extent)


def tz_for_coord(lon, lat):
    tzn = tf.timezone_at(lng=lon, lat=lat)
    if not tzn:
        raise NoTimezoneException ("tz find failed.")
    return timezone(tzn)


def local_solar_date_range(geobox, date):
    tz = tz_for_geometry(geobox.geographic_extent)
    start = datetime.datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=tz)
    end = datetime.datetime(date.year, date.month, date.day, 23, 59, 59, tzinfo=tz)
    return (start.astimezone(utc), end.astimezone(utc))


def tz_for_geometry(geom):
    crs_geo = geometry.CRS("EPSG:4326")
    geo_geom = geom.to_crs(crs_geo)
    centroid = geo_geom.centroid
    try:
        return tz_for_coord(centroid.coords[0][0], centroid.coords[0][1])
    except NoTimezoneException:
        pass
    for pt in geo_geom.boundary.coords:
        try:
            return tz_for_coord(pt[0], pt[1])
        except NoTimezoneException:
            pass
    offset = round(centroid.coords[0][0] / 15.0)
    return datetime.timezone(datetime.timedelta(hours=offset))


def resp_headers(d):
    from datacube_ows.ows_configuration import get_config
    return get_config().response_headers(d)


def get_function(func):
    """Converts a config entry to a function, if necessary

    :param func: Either a Callable object or a fully qualified function name str, or None
    :return: a Callable object, or None
    """
    if func is not None and not callable(func):
        mod_name, func_name = func.rsplit('.', 1)
        mod = import_module(mod_name)
        func = getattr(mod, func_name)
        assert callable(func)
    return func

def parse_for_base_url(url):
    parsed = urlparse(url)
    parsed = (parsed.netloc + parsed.path).rstrip("/")
    return parsed


def get_service_base_url(allowed_urls, request_url):
    if not isinstance(allowed_urls, list):
        return allowed_urls
    parsed_request_url = parse_for_base_url(request_url)
    parsed_allowed_urls = [parse_for_base_url(u) for u in allowed_urls]
    try:
        idx = parsed_allowed_urls.index(parsed_request_url)
    except ValueError:
        idx = None
    url = allowed_urls[idx] if idx is not None else allowed_urls[0]
    # template includes tailing /, strip any trail slash here to avoid duplicates
    url = url.rstrip("/")
    return url


# Collects additional headers from flask request objects
def capture_headers(request, args_dict):
    args_dict['referer'] = request.headers.get('Referer', None)
    args_dict['origin'] = request.headers.get('Origin', None)
    args_dict['requestid'] = request.environ.get("FLASK_REQUEST_ID")
    args_dict['host'] = request.headers.get('Host', None)
    args_dict['url_root'] = request.url_root

    return args_dict

# Exceptions raised when attempting to create a
# product layer from a bad config or without correct
# product range
class ProductLayerException(Exception):
    pass


class ConfigException(Exception):
    pass

# Function wrapper for configurable functional elements

class FunctionWrapper(object):
    def __init__(self,  product_cfg, func_cfg):
        if callable(func_cfg):
            raise ConfigException("Directly including callable objects in configuration is no longer supported. Please reference callables by fully qualified name.")
        elif isinstance(func_cfg, str):
            self._func = get_function(func_cfg)
            self._args = []
            self._kwargs = {}
            self.product_cfg = None
        else:
            self._func = get_function(func_cfg["function"])
            self._args = func_cfg.get("args", [])
            self._kwargs = func_cfg.get("kwargs", {})
            if func_cfg.get("pass_product_cfg", False):
                self.product_cfg = product_cfg
            else:
                self.product_cfg = None

    def __call__(self, *args, **kwargs):
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
            calling_kwargs = kwargs
        else:
            calling_kwargs = self._kwargs

        if self.product_cfg:
            calling_kwargs["product_cfg"] = self.product_cfg


        return self._func(*calling_args, **calling_kwargs)


# Extent Mask Functions

def mask_by_val(data, band, val=None):
    if val is None:
        return data[band] != data[band].attrs['nodata']
    else:
        return data[band] != val

def mask_by_val2(data, band):
    # REVISIT: Is this the same as mask_by_val or subtlely different?
    return data[band] != data[band].nodata


def mask_by_bitflag(data, band):
    return ~data[band] & data[band].attrs['nodata']


def mask_by_quality(data, band):
    return data["quality"] != 1


def mask_by_extent_flag(data, band):
    return data["extent"] == 1


def mask_by_extent_val(data, band):
    return data["extent"] != data["extent"].attrs['nodata']

# Sub-product extractors

ls8_s3_path_pattern = re.compile('L8/(?P<path>[0-9]*)')


def ls8_subproduct(ds):
    return int(ls8_s3_path_pattern.search(ds.uris[0]).group("path"))

# Method for formatting urls, e.g. for use in feature_info custom inclusions.

def feature_info_url_template(data, template):
    return template.format(data=data)
