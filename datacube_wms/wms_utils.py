from datetime import datetime

from affine import Affine
from datacube.utils import geometry
from flask import render_template
import math

try:
    from datacube_wms.wms_cfg_local import response_cfg, service_cfg
except:
    from datacube_wms.wms_cfg import response_cfg, service_cfg
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

    def __init__(self, msg, code=None, locator=None, http_response=400):
        self.http_response = http_response
        self.errors = []
        self.add_error(msg, code, locator)

    def add_error(self, msg, code=None, locator=None):
        self.errors.append({
            "msg": msg,
            "code": code,
            "locator": locator
        })


def wms_exception(e, traceback=[]):
    return render_template("wms_error.xml", exception=e, traceback=traceback), e.http_response, resp_headers(
        {"Content-Type": "application/xml"})


def _get_geobox(args, crs):
    width = int(args['width'])
    height = int(args['height'])
    minx, miny, maxx, maxy = map(float, args['bbox'].split(','))

    # miny-maxy for negative scale factor and maxy in the translation, includes inversion of Y axis.
    affine = Affine.translation(minx, maxy) * Affine.scale((maxx - minx) / width, (miny - maxy) / height)
    return geometry.GeoBox(width, height, affine, crs)


def int_trim(val, minval, maxval):
    return max(min(val, maxval), minval)


def zoom_factor(args, crs):
    # Determine the geographic "zoom factor" for the request.
    # (Larger zoom factor means deeper zoom.  Smaller zoom factor means larger area.)
    # Extract request bbox and crs
    width = int(args['width'])
    height = int(args['height'])
    minx, miny, maxx, maxy = map(float, args['bbox'].split(','))
    p1 = geometry.point(minx, maxy, crs)
    p2 = geometry.point(minx, miny, crs)
    p3 = geometry.point(maxx, maxy, crs)
    p4 = geometry.point(maxx, miny, crs)

    # Project to a geographic coordinate system
    # This is why we can't just use the regular geobox.  The scale needs to be
    # "standardised" in some sense, not dependent on the CRS of the request.
    geo_crs = geometry.CRS("EPSG:4326")
    gp1 = p1.to_crs(geo_crs)
    gp2 = p2.to_crs(geo_crs)
    gp3 = p3.to_crs(geo_crs)
    gp4 = p4.to_crs(geo_crs)

    minx = min(gp1.points[0][0], gp2.points[0][0], gp3.points[0][0], gp4.points[0][0])
    maxx = max(gp1.points[0][0], gp2.points[0][0], gp3.points[0][0], gp4.points[0][0])
    miny = min(gp1.points[0][1], gp2.points[0][1], gp3.points[0][1], gp4.points[0][1])
    maxy = max(gp1.points[0][1], gp2.points[0][1], gp3.points[0][1], gp4.points[0][1])

    # Create geobox affine transformation (N.B. Don't need an actual Geobox)
    affine = Affine.translation(minx, miny) * Affine.scale((maxx - minx) / width, (maxy - miny) / height)

    # Zoom factor is the reciprocal of the square root of the transform determinant
    # (The determinant is x scale factor multiplied by the y scale factor)
    return 1.0 / math.sqrt(affine.determinant)


def img_coords_to_geopoint(geobox, i, j):
    return geometry.point(geobox.coordinates["x"].values[int(i)],
                          geobox.coordinates["y"].values[int(j)],
                          geobox.crs)


def get_product_from_arg(args, argname="layers"):
    layers = args.get(argname, "").split(",")
    if len(layers) != 1:
        raise WMSException("Multi-layer requests not supported")
    layer = layers[0]
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


def bounding_box_to_geom(bbox, bb_crs, target_crs):
    poly = geometry.polygon([
        (bbox.left, bbox.top),
        (bbox.left, bbox.bottom),
        (bbox.right, bbox.bottom),
        (bbox.right, bbox.top),
        (bbox.left, bbox.top),
    ], bb_crs)
    return poly.to_crs(target_crs)


class GetParameters(object):
    def __init__(self, args, layer_arg="layers"):
        # Version
        self.version = get_arg(args, "version", "WMS version",
                               permitted_values=['1.1.1', '1.3.0'])
        # CRS
        if self.version == '1.1.1':
            crs_arg = "srs"
        else:
            crs_arg = "crs"
        self.crsid = get_arg(args, crs_arg, "Coordinate Reference System",
                        errcode=WMSException.INVALID_CRS,
                        permitted_values=service_cfg["published_CRSs"].keys())
        self.crs = geometry.CRS(self.crsid)
        # Layers
        self.product = self.get_product(args)

        # BBox, height and width parameters
        self.geobox = _get_geobox(args, self.crs)
        # Time parameter
        self.time = get_time(args, self.product)
        self.method_specific_init(args)

    def method_specific_init(self, args):
        return

    def get_product(self, args):
        return get_product_from_arg(args)


class GetMapParameters(GetParameters):
    def method_specific_init(self, args):
        # Validate Format parameter
        self.format = get_arg(args, "format", "image format",
                  errcode=WMSException.INVALID_FORMAT,
                  lower=True,
                  permitted_values=["image/png"])
        # Styles
        self.styles = args.get("styles", "").split(",")
        if len(self.styles) != 1:
            raise WMSException("Multi-layer GetMap requests not supported")
        style_r = self.styles[0]
        if not style_r:
            style_r = self.product.default_style
        self.style = self.product.style_index.get(style_r)
        if not self.style:
            raise WMSException("Style %s is not defined" % style_r,
                               WMSException.STYLE_NOT_DEFINED,
                               locator="Style parameter")
        # Zoom factor
        self.zf = zoom_factor(args, self.crs)


class GetFeatureInfoParameters(GetParameters):
    def get_product(self, args):
        return get_product_from_arg(args, "query_layers")

    def method_specific_init(self, args):
        # Validate Formata parameter
        self.format = get_arg(args, "info_format", "info format", lower=True,
                  errcode=WMSException.INVALID_FORMAT,
                  permitted_values=["application/json"])
        # Point coords
        if self.version == "1.1.1":
            coords = ["x", "y"]
        else:
            coords = ["i", "j"]
        i = args.get(coords[0])
        j = args.get(coords[1])
        if i is None:
            raise WMSException("HorizontalCoordinate not supplied", WMSException.INVALID_POINT,
                               "%s parameter" % coords[0])
        if j is None:
            raise WMSException("Vertical coordinate not supplied", WMSException.INVALID_POINT,
                               "%s parameter" % coords[0])
        self.i = int(i)
        self.j = int(j)

        return

