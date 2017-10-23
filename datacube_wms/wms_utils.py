from affine import Affine
from datacube.utils import geometry
from flask import render_template

from datacube_wms.wms_cfg import response_cfg


def resp_headers(d):
    hdrs = {}
    hdrs.update(response_cfg)
    hdrs.update(d)
    return hdrs


class WMSException(Exception):
    INVALID_FORMAT = "InvalidFormat"
    INVALID_CRS = "InvalidCRS"
    LAYER_NOT_DEFINED = "LayerNotDefined"
    STYLE_NOT_DEFINED = "StyleNotDefined"
    LAYER_NOT_QUERYABLE = "LayerNotQueryable"
    INVALID_POINT = "InvalidPoint"
    CURRENT_UPDATE_SEQUENCE = "CurrentUpdateSequence"
    INVALID_UPDATE_SEQUENCE = "InvalidUpdateSequence"
    MISSING_DIMENSION_VALUE = "MissingDimensionValue"
    INVALID_DIMENSION_VALUE = "InvalidDimensionValue"
    OPERATION_NOT_SUPPORTED = "OperationNotSupported"

    def __init__(self, msg, code=None, locator=None, http_response = 400):
        self.http_response = http_response
        self.errors=[]
        self.add_error(msg, code, locator)
    def add_error(self, msg, code=None, locator=None):
        self.errors.append( {
                "msg": msg,
                "code": code,
                "locator": locator
        })


def wms_exception(e, traceback=[]):
    return render_template("wms_error.xml", exception=e, traceback=traceback), e.http_response, resp_headers({"Content-Type": "application/xml"})


def _get_geobox(args, crs):
    width = int(args['width'])
    height = int(args['height'])
    minx, miny, maxx, maxy = map(float, args['bbox'].split(','))

    affine = Affine.translation(minx, miny) * Affine.scale((maxx - minx) / width, (maxy - miny) / height)
    return geometry.GeoBox(width, height, affine, crs)