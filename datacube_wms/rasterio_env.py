try:
    from datacube_wms.wms_cfg_local import service_cfg
except ImportError:
    from datacube_wms.wms_cfg import service_cfg

from dea.aws.rioenv import setup_local_env, local_env, has_local_env, s3_gdal_opts
from os import getenv

def preauthenticate_s3():
    return service_cfg.get("preauthenticate_s3", False)


def get_boto_region():
    default_region = "ap-southeast-2"
    region = getenv("AWS_REGION", None)
    region = region if region is not None else getenv("AWS_DEFAULT_REGION", default_region)
    return region


def get_gdal_opts():
    gdal_opts_cfg = service_cfg.get("gdal_opts", dict())
    return s3_gdal_opts(max_header_sz_kb=32,
                        GDAL_GEOREF_SOURCES='INTERNAL',
                        **gdal_opts_cfg)


def rio_env():
    if has_local_env():
        return local_env()
    else:
        return setup_local_env(region_name=get_boto_region(),
                               **get_gdal_opts())
