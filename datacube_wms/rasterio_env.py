from __future__ import absolute_import, division, print_function

try:
    from datacube_wms.wms_cfg_local import service_cfg
except ImportError:
    from datacube_wms.wms_cfg import service_cfg

import boto3
from os import getenv

__session__ = None

def preauthenticate_s3():
    return service_cfg.get("preauthenticate_s3", False)


def get_boto_session():
    #pylint: disable=global-statement
    global __session__
    if not preauthenticate_s3():
        return None
    if __session__ is not None:
        return __session__

    region = get_boto_region()
    boto_session = boto3.session.Session(region_name=region)
    s3 = boto_session.resource("s3")

    __session__ = boto_session

    return __session__

def get_boto_credentials():
    if not preauthenticate_s3():
        return None

    region = get_boto_region()
    boto_session = boto3.session.Session(region_name=region)

    creds = boto_session.get_credentials()
    credentials = creds.get_frozen_credentials()
    return credentials

def get_boto_region():
    default_region = "ap-southeast-2"
    region = getenv("AWS_REGION", None)
    region = region if region is not None else getenv("AWS_DEFAULT_REGION", default_region)
    return region

def get_rio_geotiff_georeference_source():
    return service_cfg.get("geotiff_georeference_source", "PAM,INTERNAL,TABFILE,WORLDFILE,NONE")
