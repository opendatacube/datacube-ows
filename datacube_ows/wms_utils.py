# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import math
from datetime import date, datetime, timezone

import numpy
import regex as re
from affine import Affine
from dateutil.parser import parse
from dateutil.relativedelta import relativedelta
from matplotlib import pyplot as plt
from odc.geo import geom
from odc.geo.crs import CRS
from odc.geo.geobox import GeoBox
from rasterio.warp import Resampling
from typing_extensions import override

from datacube_ows.config_utils import ConfigException
from datacube_ows.ogc_exceptions import WMSException
from datacube_ows.ogc_utils import create_geobox
from datacube_ows.ows_configuration import OWSNamedLayer, get_config
from datacube_ows.resource_limits import RequestScale
from datacube_ows.styles import StyleDef, StyleDefBase
from datacube_ows.styles.expression import ExpressionException
from datacube_ows.utils import default_to_utc, find_matching_date

RESAMPLING_METHODS = {
    "nearest": Resampling.nearest,
    "cubic": Resampling.cubic,
    "bilinear": Resampling.bilinear,
    "cubic_spline": Resampling.cubic_spline,
    "lanczos": Resampling.lanczos,
    "average": Resampling.average,
}


def _bounding_pts(
    minx: int, miny: int, maxx: int, maxy: int, src_crs, dst_crs=None
) -> tuple[float, float, float, float]:
    # pylint: disable=too-many-locals
    p1 = geom.point(minx, maxy, src_crs)
    p2 = geom.point(minx, miny, src_crs)
    p3 = geom.point(maxx, maxy, src_crs)
    p4 = geom.point(maxx, miny, src_crs)

    conv = dst_crs is not None
    gp1 = p1.to_crs(dst_crs) if conv else p1
    gp2 = p2.to_crs(dst_crs) if conv else p2
    gp3 = p3.to_crs(dst_crs) if conv else p3
    gp4 = p4.to_crs(dst_crs) if conv else p4

    minx = min(gp1.points[0][0], gp2.points[0][0], gp3.points[0][0], gp4.points[0][0])
    maxx = max(gp1.points[0][0], gp2.points[0][0], gp3.points[0][0], gp4.points[0][0])
    miny = min(gp1.points[0][1], gp2.points[0][1], gp3.points[0][1], gp4.points[0][1])
    maxy = max(gp1.points[0][1], gp2.points[0][1], gp3.points[0][1], gp4.points[0][1])

    # miny-maxy for negative scale factor and maxy in the translation, includes inversion of Y axis.

    return minx, miny, maxx, maxy


def _get_geobox_xy(args, crs: CRS) -> tuple:
    if get_config().published_CRSs[str(crs)]["vertical_coord_first"]:
        miny, minx, maxy, maxx = map(float, args["bbox"].split(","))
    else:
        minx, miny, maxx, maxy = map(float, args["bbox"].split(","))
    return minx, miny, maxx, maxy


def _get_geobox(args, crs: CRS) -> GeoBox:
    width = int(args["width"])
    height = int(args["height"])
    minx, miny, maxx, maxy = _get_geobox_xy(args, crs)

    if minx == maxx or miny == maxy:
        raise WMSException("Bounding box must enclose a non-zero area")

    if crs.epsg == 3857 and (maxx < -13_000_000 or minx > 13_000_000):
        # EPSG:3857 query AND closer to the anti-meridian than the prime meridian:
        # re-project to epsg:3832 (Pacific Web-Mercator)
        ll = geom.point(x=minx, y=miny, crs=crs).to_crs("epsg:3832")
        ur = geom.point(x=maxx, y=maxy, crs=crs).to_crs("epsg:3832")
        minx, miny = ll.coords[0]
        maxx, maxy = ur.coords[0]
        crs = CRS("epsg:3832")

    return create_geobox(crs, minx, miny, maxx, maxy, width, height)


def _get_polygon(args, crs: CRS) -> geom.Geometry:
    minx, miny, maxx, maxy = _get_geobox_xy(args, crs)
    return geom.polygon(
        [(minx, maxy), (minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)], crs
    )


def zoom_factor(args, crs) -> float:
    # Determine the geographic "zoom factor" for the request.
    # (Larger zoom factor means deeper zoom.  Smaller zoom factor means larger area.)
    # Extract request bbox and crs
    width = int(args["width"])
    height = int(args["height"])
    minx, miny, maxx, maxy = _get_geobox_xy(args, crs)

    # Project to a geographic coordinate system
    # This is why we can't just use the regular geobox.  The scale needs to be
    # "standardised" in some sense, not dependent on the CRS of the request.
    # TODO: can we do better in polar regions?
    minx, miny, maxx, maxy = _bounding_pts(
        minx, miny, maxx, maxy, crs, dst_crs="epsg:4326"
    )
    # Create geobox affine transformation (N.B. Don't need an actual Geobox)
    affine = Affine.translation(minx, miny) * Affine.scale(
        (maxx - minx) / width, (maxy - miny) / height
    )
    # Zoom factor is the reciprocal of the square root of the transform determinant
    # (The determinant is x scale factor multiplied by the y scale factor)
    return 1.0 / math.sqrt(affine.determinant)


def img_coords_to_geopoint(geobox, i, j) -> geom.Geometry:
    cfg = get_config()
    h_coord = cfg.published_CRSs[str(geobox.crs)]["horizontal_coord"]
    v_coord = cfg.published_CRSs[str(geobox.crs)]["vertical_coord"]
    return geom.point(
        geobox.coordinates[h_coord].values[int(i)],
        geobox.coordinates[v_coord].values[int(j)],
        geobox.crs,
    )


def get_layer_from_arg(args, argname: str = "layers") -> OWSNamedLayer:
    layers = args.get(argname, "").split(",")
    if len(layers) != 1:
        raise WMSException("Multi-layer requests not supported")
    lyr = layers[0]
    layer_chunks = lyr.split("__")
    lyr = layer_chunks[0]
    cfg = get_config()
    layer = cfg.layer_index.get(lyr)
    if not layer:
        raise WMSException(
            f"Layer {lyr} is not defined",
            WMSException.LAYER_NOT_DEFINED,
            locator="Layer parameter",
            valid_keys=list(cfg.layer_index),
        )
    return layer


def get_arg(
    args,
    argname: str,
    verbose_name: str,
    lower: bool = False,
    errcode=None,
    permitted_values=None,
):
    fmt = args.get(argname, "")
    if lower:
        fmt = fmt.lower()
    if not fmt:
        raise WMSException(
            f"No {verbose_name} specified",
            errcode,
            locator=f"{argname} parameter",
            valid_keys=permitted_values,
        )

    if permitted_values and fmt not in permitted_values:
        raise WMSException(
            f"{verbose_name} {fmt} is not supported",
            errcode,
            locator=f"{argname} parameter",
            valid_keys=permitted_values,
        )
    return fmt


def get_times_for_layer(layer: OWSNamedLayer) -> list[datetime | date]:
    return layer.ranges.times


def get_times(args, layer: OWSNamedLayer) -> list[datetime | date]:
    # Time parameter
    times_raw = args.get("time", "")
    times = times_raw.split(",")

    return [parse_time_item(item, layer) for item in times]


def parse_time_item(item: str, layer: OWSNamedLayer) -> datetime | date:
    times = item.split("/")
    # Time range handling follows the implementation described by GeoServer
    # https://docs.geoserver.org/stable/en/user/services/wms/time.html

    # If all times are equal we can proceed
    if len(times) > 1:
        # TODO WMS Time range selections (/ notation) are poorly and incompletely implemented.
        start, end = parse_wms_time_strings(
            times, with_tz=layer.time_resolution.is_subday()
        )
        if layer.time_resolution.is_subday():
            matching_times: list[datetime | date] = [
                t for t in layer.ranges.times if start <= t <= end
            ]
        else:
            start, end = start.date(), end.date()
            matching_times = [t for t in layer.ranges.times if start <= t <= end]
        if matching_times:
            # default to the first matching time
            return matching_times[0]
        if layer.regular_time_axis:
            raise WMSException(
                f"No data available for time dimension range '{start}'-'{end}' for this layer",
                WMSException.INVALID_DIMENSION_VALUE,
                locator="Time parameter",
            )
        raise WMSException(
            f"Time dimension range '{start}'-'{end}' not valid for this layer",
            WMSException.INVALID_DIMENSION_VALUE,
            locator="Time parameter",
        )
    if not times[0]:
        # default to last available time if not supplied.
        product_times = get_times_for_layer(layer)
        return product_times[-1]
    try:
        time = parse(times[0])
        day = time.date()
    except ValueError:
        raise WMSException(
            f"Time dimension value '{times[0]}' not valid for this layer",
            WMSException.INVALID_DIMENSION_VALUE,
            locator="Time parameter",
        ) from None

    # Validate time parameter for requested layer.
    if layer.regular_time_axis:
        # Note regular time axis and time resolution are effectively exclusive
        start, end = layer.time_range()
        if day < start:
            raise WMSException(
                f"Time dimension value '{times[0]}' not valid for this layer",
                WMSException.INVALID_DIMENSION_VALUE,
                locator="Time parameter",
            )
        if day > end:
            raise WMSException(
                f"Time dimension value '{times[0]}' not valid for this layer",
                WMSException.INVALID_DIMENSION_VALUE,
                locator="Time parameter",
            )
        if (day - start).days % layer.time_axis_interval != 0:
            raise WMSException(
                f"Time dimension value '{times[0]}' not valid for this layer",
                WMSException.INVALID_DIMENSION_VALUE,
                locator="Time parameter",
            )
        return day
    if layer.time_resolution.is_subday():
        if not find_matching_date(time, layer.ranges.times):
            raise WMSException(
                f"Time dimension value '{times[0]}' not valid for this layer",
                WMSException.INVALID_DIMENSION_VALUE,
                locator="Time parameter",
            )
        return time
    if day not in layer.ranges.time_set:
        raise WMSException(
            f"Time dimension value '{times[0]}' not valid for this layer",
            WMSException.INVALID_DIMENSION_VALUE,
            locator="Time parameter",
        )
    return day


def parse_time_delta(delta_str) -> relativedelta:
    pattern = (
        r"P((?P<years>\d+)Y)?((?P<months>\d+)M)?((?P<days>\d+)D)?"
        r"(T(((?P<hours>\d+)H)?((?P<minutes>\d+)M)?((?P<seconds>\d+)S)?)?)?"
    )
    parts = re.search(pattern, delta_str).groupdict()
    return relativedelta(**{k: int(v) for k, v in parts.items() if v is not None})  # type: ignore[arg-type]


def parse_wms_time_string(t: str, start: bool = True) -> datetime | relativedelta:
    if t.upper() == "PRESENT":
        return datetime.now(timezone.utc)
    if t.startswith("P"):
        return parse_time_delta(t)
    default = (
        datetime(1970, 1, 1) if start else datetime(1970, 12, 31, 23, 23, 59, 999999)
    )  # default year ignored
    return parse(t, default=default)


def parse_wms_time_strings(parts: list[str], with_tz: bool = False) -> tuple:
    start = parse_wms_time_string(parts[0])
    end = parse_wms_time_string(parts[-1], start=False)

    a_tiny_bit = relativedelta(microseconds=1)
    # Follows GeoServer https://docs.geoserver.org/stable/en/user/services/wms/time.html#reduced-accuracy-times

    if isinstance(start, relativedelta):
        if isinstance(end, relativedelta):
            raise WMSException(
                f"Could not understand time value '{parts}'",
                WMSException.INVALID_DIMENSION_VALUE,
                locator="Time parameter",
            )
        fuzzy_end = parse_wms_time_string(parts[-1], start=True)
        return fuzzy_end - start + a_tiny_bit, end
    if isinstance(end, relativedelta):
        end = start + end - a_tiny_bit
    if with_tz:
        start = default_to_utc(start)
        end = default_to_utc(end)
    return start, end


class GetParameters:
    def __init__(self, args) -> None:
        self.cfg = get_config()
        # Version
        self.version = get_arg(
            args, "version", "WMS version", permitted_values=["1.1.1", "1.3.0"]
        )
        # CRS
        crs_arg = "srs" if self.version == "1.1.1" else "crs"
        self.crsid = get_arg(
            args,
            crs_arg,
            "Coordinate Reference System",
            errcode=WMSException.INVALID_CRS,
            permitted_values=list(self.cfg.published_CRSs),
        )
        self.crs = self.cfg.crs(self.crsid)
        # Layers
        self.layer = self.get_layer(args)

        self.geometry = _get_polygon(args, self.crs)
        # BBox, height and width parameters
        self.geobox = _get_geobox(args, self.crs)
        # Web-merc antimeridian hack:
        if self.geobox.crs != self.crs:
            self.crs = self.geobox.crs  # type: ignore[assignment]
            self.geometry = self.geometry.to_crs(self.crs)

        # Time parameter
        self.times = get_times(args, self.layer)

        self.method_specific_init(args)

    def method_specific_init(self, args) -> None:
        pass

    def get_layer(self, args) -> OWSNamedLayer:
        return get_layer_from_arg(args)


def single_style_from_args(layer: OWSNamedLayer, args, required: bool = True):
    # User Band Math (overrides style if present).
    if layer.user_band_math and "code" in args and "colorscheme" in args:
        code = args["code"]
        mpl_ramp = args["colorscheme"]
        try:
            plt.get_cmap(mpl_ramp)
        except Exception:
            raise WMSException(
                f"Invalid Matplotlib ramp name: {mpl_ramp}",
                locator="Colorscalerange parameter",
            ) from None
        colorscalerange = args.get("colorscalerange", "0,1").split(",")
        if len(colorscalerange) != 2:
            raise WMSException(
                "Colorscale range must be two numbers, sorted and separated by a comma.",
                locator="Colorscalerange parameter",
            )
        try:
            colorscalerange = [float(r) for r in colorscalerange]
        except ValueError:
            raise WMSException(
                "Colorscale range must be two numbers, sorted and separated by a comma.",
                locator="Colorscalerange parameter",
            ) from None
        if colorscalerange[0] >= colorscalerange[1]:
            raise WMSException(
                "Colorscale range must be two numbers, sorted and separated by a comma.",
                locator="Colorscalerange parameter",
            )
        try:
            style: StyleDefBase | None = StyleDef(
                layer,
                {
                    "name": "custom_user_style",
                    "index_expression": code,
                    "mpl_ramp": mpl_ramp,
                    "range": colorscalerange,
                    "legend": {
                        "title": "User-Custom Index",
                        "show_legend": True,
                        "begin": str(colorscalerange[0]),
                        "end": str(colorscalerange[1]),
                    },
                },
                stand_alone=True,
                user_defined=True,
            )
        except ExpressionException as e:
            raise WMSException(
                f"Code expression invalid: {e}", locator="Code parameter"
            ) from None
        except ConfigException as e:
            raise WMSException(f"Code invalid: {e}", locator="Code parameter") from None
    else:
        # Regular WMS Styles
        styles = args.get("styles", "").split(",")
        if len(styles) != 1:
            raise WMSException("Multi-layer GetMap requests not supported")
        style_r = styles[0]
        if not style_r and not required:
            return None
        if not style_r:
            style_r = layer.default_style.name
        style = layer.style_index.get(style_r)
        if not style:
            raise WMSException(
                f"Style {style_r} is not defined",
                WMSException.STYLE_NOT_DEFINED,
                locator="Style parameter",
                valid_keys=list(layer.style_index),
            )
    return style


class GetLegendGraphicParameters:
    def __init__(self, args) -> None:
        self.layer = get_layer_from_arg(args, "layer")

        # Validate Format parameter
        self.format = get_arg(
            args,
            "format",
            "image format",
            errcode=WMSException.INVALID_FORMAT,
            lower=True,
            permitted_values=["image/png"],
        )
        self.style = single_style_from_args(self.layer, args)
        self.styles = [self.style]
        # Time parameter
        self.times = get_times(args, self.layer)


class GetMapParameters(GetParameters):
    @override
    def method_specific_init(self, args) -> None:
        # Validate Format parameter
        self.format = get_arg(
            args,
            "format",
            "image format",
            errcode=WMSException.INVALID_FORMAT,
            lower=True,
            permitted_values=["image/png"],
        )

        self.style = single_style_from_args(self.layer, args)
        cfg = get_config()
        if self.geobox.width > cfg.wms_max_width:
            raise WMSException(
                f"Width {self.geobox.width} exceeds supported maximum {self.cfg.wms_max_width}.",
                locator="Width parameter",
            )
        if self.geobox.height > cfg.wms_max_height:
            raise WMSException(
                f"Width {self.geobox.height} exceeds supported maximum {self.cfg.wms_max_height}.",
                locator="Height parameter",
            )

        # Zoom factor
        self.zf = zoom_factor(args, self.crs)

        self.ows_stats = bool(args.get("ows_stats"))

        # TODO: Do we need to make resampling method configurable?
        self.resampling = Resampling.nearest

        self.resources = RequestScale(
            native_crs=CRS(self.layer.native_CRS),
            native_resolution=(self.layer.resolution_x, self.layer.resolution_y),
            geobox=self.geobox,
            n_dates=len(self.times),
            request_bands=self.style.odc_needed_bands(),
        )


class GetFeatureInfoParameters(GetParameters):
    @override
    def get_layer(self, args) -> OWSNamedLayer:
        return get_layer_from_arg(args, "query_layers")

    @override
    def method_specific_init(self, args) -> None:
        # Validate Formata parameter
        self.format = get_arg(
            args,
            "info_format",
            "info format",
            lower=True,
            errcode=WMSException.INVALID_FORMAT,
            permitted_values=["application/json", "text/html"],
        )
        # Point coords
        coords = ["x", "y"] if self.version == "1.1.1" else ["i", "j"]
        i = args.get(coords[0])
        j = args.get(coords[1])
        if i is None:
            raise WMSException(
                "HorizontalCoordinate not supplied",
                WMSException.INVALID_POINT,
                f"{coords[0]} parameter",
            )
        if j is None:
            raise WMSException(
                "Vertical coordinate not supplied",
                WMSException.INVALID_POINT,
                f"{coords[0]} parameter",
            )
        self.i = int(i)
        self.j = int(j)
        self.style = single_style_from_args(self.layer, args, required=False)


# Solar angle correction functions
def declination_rad(dt) -> float:
    # Estimate solar declination from a datetime.  (value returned in radians).
    # Formula taken from https://en.wikipedia.org/wiki/Position_of_the_Sun#Declination_of_the_Sun_as_seen_from_Earth
    timedel = dt - datetime(dt.year, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    day_count = timedel.days + timedel.seconds / (60.0 * 60.0 * 24.0)
    return -1.0 * math.radians(23.44) * math.cos(2 * math.pi / 365 * (day_count + 10))


def cosine_of_solar_zenith(lat: float, lon: float, utc_dt) -> float:
    # Estimate cosine of solar zenith angle
    # (angle between sun and local zenith) at requested latitude, longitude and datetime.
    # Formula taken from https://en.wikipedia.org/wiki/Solar_zenith_angle
    utc_seconds_since_midnight = (
        (utc_dt.hour * 60) + utc_dt.minute
    ) * 60 + utc_dt.second
    utc_hour_deg_angle = (utc_seconds_since_midnight / (60 * 60 * 24) * 360.0) - 180.0
    local_hour_deg_angle = utc_hour_deg_angle + lon
    local_hour_angle_rad = math.radians(local_hour_deg_angle)
    latitude_rad = math.radians(lat)
    solar_decl_rad = declination_rad(utc_dt)
    return math.sin(latitude_rad) * math.sin(solar_decl_rad) + math.cos(
        latitude_rad
    ) * math.cos(solar_decl_rad) * math.cos(local_hour_angle_rad)


def solar_correct_data(data, dataset) -> float:
    # Apply solar angle correction to the data for a dataset.
    # See for example http://gsp.humboldt.edu/olm_2015/Courses/GSP_216_Online/lesson4-1/radiometric.html
    native_x = (dataset.bounds.right + dataset.bounds.left) / 2.0
    native_y = (dataset.bounds.top + dataset.bounds.bottom) / 2.0
    pt = geom.point(native_x, native_y, dataset.crs)
    geo_pt = pt.to_crs("epsg:4326")
    data_time = dataset.center_time.astimezone(timezone.utc)
    data_lon, data_lat = geo_pt.coords[0]

    csz = cosine_of_solar_zenith(data_lat, data_lon, data_time)

    return data / csz


def wofls_fuser(dest: numpy.ndarray, src: numpy.ndarray) -> numpy.ndarray:
    where_nodata = (src & 1) == 0
    numpy.copyto(dest, src, where=where_nodata)
    return dest


def item_fuser(dest: numpy.ndarray, src: numpy.ndarray) -> numpy.ndarray:
    where_combined = numpy.isnan(dest) | (dest == -6666.0)
    numpy.copyto(dest, src, where=where_combined)
    return dest
