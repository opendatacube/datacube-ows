from __future__ import absolute_import, division, print_function

try:
    from datacube_wms.wms_cfg_local import service_cfg
except ImportError:
    from datacube_wms.wms_cfg import service_cfg

import boto3
from os import getenv
from time import monotonic

__session__ = None
__session_start__ = monotonic()
__credentials__ = None
MAX_SESSION_TIME = (30 * 60) # Seconds

DEFAULT_GDAL_OPTS = {
    "VSI_CACHE": True,
    "CPL_VSIL_CURL_ALLOWED_EXTENSIONS": ".tif",
    "GDAL_DISABLE_READDIR_ON_OPEN": "EMPTY_DIR",
    "GDAL_GEOREF_SOURCES": "INTERNAL",
    "GDAL_INGESTED_BYTES_AT_OPEN": 32*1024
}

def preauthenticate_s3():
    return service_cfg.get("preauthenticate_s3", False)

# Not thread safe
def get_boto_session():
    #pylint: disable=global-statement
    global __session__
    global __session_start__
    if not preauthenticate_s3():
        return None
    now = monotonic()
    time_diff = __session_start__ - now
    if __session__ is None or time_diff > MAX_SESSION_TIME:
        region = get_boto_region()
        boto_session = boto3.session.Session(region_name=region)
        s3 = boto_session.resource("s3")

        __session__ = boto_session
        __session_start__ = now

    return __session__

def get_boto_credentials():
    global __credentials__
    if __credentials__ is None:
        session = get_boto_session()
        if session is None:
            return None
        creds = session.get_credentials()
        if creds is None:
            return None
        __credentials__ = creds.get_frozen_credentials()
    return __credentials__

def get_boto_region():
    default_region = "ap-southeast-2"
    region = getenv("AWS_REGION", None)
    region = region if region is not None else getenv("AWS_DEFAULT_REGION", default_region)
    return region


def get_gdal_opts():
    gdal_opts = service_cfg.get("gdal_opts", dict())
    return {**DEFAULT_GDAL_OPTS, **gdal_opts}
