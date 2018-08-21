try:
    from datacube_wms.wms_cfg_local import service_cfg
except:
    from datacube_wms.wms_cfg import service_cfg

import boto3
from os import getenv

def preauthenticate_s3():
    return service_cfg.get("preauthenticate_s3", False)


def get_boto_session():
    if not preauthenticate_s3():
        return None

    AWS_DEFAULT_REGION = "ap-southeast-2"
    region = getenv("AWS_REGION", None)
    region = region if region is not None else getenv("AWS_DEFAULT_REGION", AWS_DEFAULT_REGION)
    boto_session = boto3.session.Session(region_name=region)
    s3 = boto_session.resource("s3")
    return boto_session 


def get_rio_geotiff_georeference_source():
    return service_cfg.get("geotiff_georeference_source", "PAM,INTERNAL,TABFILE,WORLDFILE,NONE")

