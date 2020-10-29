from datacube_ows.ogc_utils import ConfigException
from datacube_ows.config_utils import OWSConfigEntry

# Scale denominators for WebMercator QuadTree Scale Set, starting from zoom level 0.
# Currently goes to zoom level 14, where the pixel size at the equator is ~10m (i.e. Sentinel2 resolution)
# Taken from the WMTS 1.0.0 spec, Annex E.4
# Don't even think about changing these numbers unless you really, really know what you are doing.

webmerc_scale_set = [
    559082264.0287178,
    279541132.0143589,
    139770566.0071794,
    69885283.00358972,
    34942641.50179486,
    17471320.75089743,
    8735660.375448715,
    4367830.187724357,
    2183915.093862179,
    1091957.546931089,
    545978.7734655447,
    272989.3867327723,
    136494.6933663862,
    68247.34668319309,
    34123.67334159654,
]


def validate_2d_array(array, id, label, typ):
    try:
        if len(array) != 2:
            raise ConfigException(f"In tile matrix set {id}, {label} must have two values: f{array}")
        validate_array_typ(array, id, label, typ)
    except TypeError:
        raise ConfigException(f"In tile matrix set {id}, {label} must be a list of two values: f{array}")


def validate_array_typ(array, id, label, typ):
    for elem in array:
        if not isinstance(elem, typ):
            raise ConfigException(f"In tile matrix set {id}, {label} has non-{typ.__name__} value of type {elem.__class__.__name__}: {elem}")


class TileMatrixSet(OWSConfigEntry):
    default_tm_sets = {
        "WholeWorld_WebMercator": {
            "crs": "EPSG:3857",
            "matrix_origin": (-20037508.3427892, 20037508.3427892),
            "tile_size": (256, 256),
            "scale_set": webmerc_scale_set,
            "wkss": "urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible",
        },
    }

    def __init__(self, identifier, cfg, global_cfg):
        super().__init__(cfg)
        self.global_cfg = global_cfg
        self.identifier = identifier

        self.crs_name = cfg["crs"]
        if self.crs_name not in self.global_cfg.published_CRSs:
            raise ConfigException(f"Tile matrix set {identifier} has unpublished CRS: {self.crs_name}")
        self.top_left = cfg["matrix_origin"]
        validate_2d_array(self.top_left, identifier, "Matrix origin", float)
        self.tile_size = cfg["tile_size"]
        validate_2d_array(self.tile_size, identifier, "Tile size", int)
        self.scale_set = cfg["scale_set"]
        try:
            validate_array_typ(self.scale_set, identifier, "Scale set", float)
        except TypeError:
            raise ConfigException(f"In tile matrix set {identifier}, scale_set is not a list")
        if len(self.scale_set) < 1:
            raise ConfigException(f"Tile matrix set {identifier} has no scale denominators in scale_set")
        self.force_raw_crs_name = bool(cfg.get("force_raw_crs_name", False))
        self.wkss = cfg.get("wkss")
        self.initial_matrix_exponents = cfg.get("initial_matrix_exponents", (0,0))
        validate_2d_array(self.initial_matrix_exponents, identifier, "Initial matrix exponents", int)
        self.unit_coefficients = cfg.get("unit_coefficients", (1.0, -1.0))
        validate_2d_array(self.unit_coefficients, identifier, "Unit coefficients", float)

    @property
    def crs_display(self):
        if self.force_raw_crs_name:
            return self.crs_name
        if self.crs_name[:5] == "EPSG:":
            return f"urn:ogc:def:crs:EPSG::{self.crs_name[5:]}"
        return self.crs_name

    def exponent(self, idx, scale_no):
        init = self.initial_matrix_exponents[idx]
        exponent = scale_no + init
        if exponent < 0:
            return 0
        return exponent

    def width_exponent(self, scale_no):
        return self.exponent(0, scale_no)

    def height_exponent(self, scale_no):
        return self.exponent(1, scale_no)

