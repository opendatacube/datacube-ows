from __future__ import absolute_import, division, print_function

from importlib import import_module
from datetime import timedelta, datetime
from dateutil.parser import parse
from urllib.parse import urlparse
try:
    from datacube_wms.wms_cfg_local import service_cfg, layer_cfg, response_cfg
except ImportError:
    from datacube_wms.wms_cfg import service_cfg, layer_cfg, response_cfg


# Use metadata time if possible as this is what WMS uses to calculate it's temporal extents
# datacube-core center time accessed through the dataset API is caluclated and may
# not agree with the metadata document
def dataset_center_time(dataset):
    center_time = dataset.center_time
    try:
        metadata_time = dataset.metadata_doc['extent']['center_dt']
        center_time = parse(metadata_time)
    except KeyError:
        pass
    return center_time


def mean_solar_time(time, mean_long):
    mean_solar_tz_offset = mean_long / 15.0
    mean_local_solar_time = time + timedelta(hours=mean_solar_tz_offset)
    return mean_local_solar_time.date()


def local_date(ds):
    dt_utc = dataset_center_time(ds)
    mean_long = (ds.metadata.lon.begin + ds.metadata.lon.end) / 2.0
    return mean_solar_time(dt_utc, mean_long)


def local_solar_date_range(geobox, time):
    mean_long = geobox.geographic_extent.centroid.coords[0][0]
    mean_solar_tz_offset = mean_long / 15.0
    mst = datetime(time.year, time.month, time.day) - timedelta(hours=mean_solar_tz_offset)
    mst_1 = mst + timedelta(days=1)
    return (mst, mst_1)


def resp_headers(d):
    hdrs = {}
    hdrs.update(response_cfg)
    hdrs.update(d)
    return hdrs


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
    url = request_url if parsed_request_url in parsed_allowed_urls else allowed_urls[0]
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
# product layer form a bad config or without correct
# product range
class ProductLayerException(Exception):
    pass
