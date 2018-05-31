from datetime import datetime
from pytz import utc

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
    if service_cfg["published_CRSs"][crs.crs_str].get("vertical_coord_first"):
        miny, minx, maxy, maxx = map(float, args['bbox'].split(','))
    else:
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
    h_coord = service_cfg["published_CRSs"][geobox.crs.crs_str].get("horizontal_coord", "longitude")
    v_coord = service_cfg["published_CRSs"][geobox.crs.crs_str].get("vertical_coord", "latitude")
    return geometry.point(geobox.coordinates[h_coord].values[int(i)],
                          geobox.coordinates[v_coord].values[int(j)],
                          geobox.crs)


def get_product_from_arg(args, argname="layers"):
    layers = args.get(argname, "").split(",")
    if len(layers) != 1:
        raise WMSException("Multi-layer requests not supported")
    layer = layers[0]
    layer_chunks = layer.split("__")
    layer = layer_chunks[0]
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


def get_time(args, product, raw_product):
    # Time parameter
    times = args.get('time', '').split('/')
    if len(times) > 1:
        raise WMSException(
            "Selecting multiple time dimension values not supported",
            WMSException.INVALID_DIMENSION_VALUE,
            locator="Time parameter")
    elif not times[0]:
        # default to last available time if not supplied.
        chunks = raw_product.split("__")
        if len(chunks) == 1:
            path = None
            ranges = product.ranges
        else:
            path = int(chunks[1])
            ranges = product.sub_ranges[path]

        return ranges["times"][-1]
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
    def __init__(self, args):
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
        self.raw_product = self.get_raw_product(args)

        # BBox, height and width parameters
        self.geobox = _get_geobox(args, self.crs)
        # Time parameter
        self.time = get_time(args, self.product, self.raw_product)

        self.method_specific_init(args)

    def method_specific_init(self, args):
        return

    def get_product(self, args):
        return get_product_from_arg(args)

    def get_raw_product(self, args):
        return args["layers"].split(",")[0]


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

    def get_raw_product(self, args):
        return args["query_layers"].split(",")[0]

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
        raise WMSException(
            "Time dimension value not supplied",
            WMSException.MISSING_DIMENSION_VALUE,
            locator="Time parameter")

# Solar angle correction functions

def declination_rad(dt):
    # Estimate solar declination from a datetime.  (value returned in radians).
    # Formula taken from https://en.wikipedia.org/wiki/Position_of_the_Sun#Declination_of_the_Sun_as_seen_from_Earth
    timedel = dt - datetime(dt.year, 1, 1, 0, 0, 0, tzinfo=utc)
    day_count = timedel.days + timedel.seconds/(60.0*60.0*24.0)
    return (-1.0 * math.radians(23.44) * math.cos(2*math.pi/365*(day_count + 10)))

def cosine_of_solar_zenith(lat, lon, utc_dt):
    # Estimate cosine of solar zenith angle (angle between sun and local zenith) at requested latitude, longitude and datetime.
    # Formula taken from https://en.wikipedia.org/wiki/Solar_zenith_angle
    utc_seconds_since_midnight = ((utc_dt.hour * 60) + utc_dt.minute) * 60 + utc_dt.second
    utc_hour_deg_angle = (utc_seconds_since_midnight / (60*60*24) * 360.0) - 180.0
    local_hour_deg_angle = utc_hour_deg_angle + lon
    local_hour_angle_rad = math.radians(local_hour_deg_angle)
    latitude_rad = math.radians(lat)
    solar_decl_rad = declination_rad(utc_dt)

    return math.sin(latitude_rad)*math.sin(solar_decl_rad) + math.cos(latitude_rad)*math.cos(solar_decl_rad)*math.cos(local_hour_angle_rad)

def solar_correct_data(data, dataset):
    # Apply solar angle correction to the data for a dataset.
    # See for example http://gsp.humboldt.edu/olm_2015/Courses/GSP_216_Online/lesson4-1/radiometric.html
    native_x = (dataset.bounds.right + dataset.bounds.left)/2.0
    native_y = (dataset.bounds.top + dataset.bounds.bottom)/2.0
    pt = geometry.point(native_x, native_y, dataset.crs)
    crs_geo = geometry.CRS("EPSG:4326")
    geo_pt = pt.to_crs(crs_geo)
    data_time = dataset.center_time.astimezone(utc)
    data_lon, data_lat = geo_pt.coords[0]

    csz = cosine_of_solar_zenith(data_lat, data_lon, data_time)

    return data / csz



