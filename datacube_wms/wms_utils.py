from datetime import datetime

from affine import Affine
from datacube.utils import geometry
from flask import render_template

from datacube_wms.wms_cfg import response_cfg
from datacube_wms.wms_layers import get_layers


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


def img_coords_to_geopoint(geobox, i,j):
    return geometry.point( geobox.coordinates["x"].values[int(i)],
             geobox.coordinates["y"].values[int(j)],
             geobox.crs)


def get_product_from_arg(args, argname="layers"):
    layers = args.get(argname, "").split(",")
    if len(layers) != 1:
        raise WMSException("Multi-layer requests not supported")
    layer=layers[0]
    platforms = get_layers()
    product = platforms.product_index.get(layer)
    if not product:
        raise WMSException("Layer %s is not defined" % layer,
                           WMSException.LAYER_NOT_DEFINED,
                           locator="Layer parameter")
    return product


def get_arg(args, argname, verbose_name, lower=False,
            errcode=None, permitted_values=[]):
    fmt = args.get(argname, "")
    if lower: fmt = fmt.lower()
    if not fmt:
        raise WMSException("No %s specified" % verbose_name,
                           errcode,
                           locator="%s parameter" % argname)

    if permitted_values:
        if fmt not in permitted_values:
            raise WMSException("%s %s is not supported" % (verbose_name, fmt),
                           errcode,
                           locator="%s parameter" % argname)
    return fmt

def get_time(args, product):
    # Time parameter
    times = args.get('time', '').split('/')
    if len(times) > 1:
        raise WMSException(
            "Selecting multiple time dimension values not supported",
            WMSException.INVALID_DIMENSION_VALUE,
            locator="Time parameter")
    elif not times[0]:
        raise WMSException(
            "Time dimension value not supplied",
            WMSException.MISSING_DIMENSION_VALUE,
            locator="Time parameter")
    try:
        time = datetime.strptime(times[0], "%Y-%m-%d").date()
    except ValueError:
        raise WMSException(
            "Time dimension value '%s' not valid for this layer" % times[0],
            WMSException.INVALID_DIMENSION_VALUE,
            locator="Time parameter")

    # Validate time paramter for requested layer.
    if time not in product.ranges["time_set"]:
        raise WMSException(
            "Time dimension value '%s' not valid for this layer" % times[0],
            WMSException.INVALID_DIMENSION_VALUE,
            locator="Time parameter")
    return time