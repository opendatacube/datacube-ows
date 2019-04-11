from __future__ import absolute_import
try:
    from datacube_wms.wms_cfg_local import service_cfg
except ImportError:
    from datacube_wms.wms_cfg import service_cfg

from dea.aws.rioenv import s3_gdal_opts
from rasterio.env import Env
from os import getenv

def get_boto_region():
    default_region = "ap-southeast-2"
    region = getenv("AWS_REGION", None)
    region = region if region is not None else getenv("AWS_DEFAULT_REGION", default_region)
    return region


def get_gdal_opts():
    gdal_opts_cfg = service_cfg.get("gdal_opts", dict())
    return s3_gdal_opts(max_header_sz_kb=32,
                        GDAL_GEOREF_SOURCES='INTERNAL',
                        CPL_VSIL_CURL_ALLOWED_EXTENSIONS='tif,tiff',
                        **gdal_opts_cfg)


def rio_env():
    return Env(**get_gdal_opts())
