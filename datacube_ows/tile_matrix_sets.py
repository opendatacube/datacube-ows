

class TileMatrixSet:
    def __init__(self, identifier, crs_name,
                 top_left, tile_size,
                 scale_set,
                 layer_suffix,
                 initial_matrix_exponents=(0,0),
                 wkss=None,
                 force_raw_crs_name=False,):
        self.identifier = identifier
        self.crs_name = crs_name
        self.force_raw_crs_name = force_raw_crs_name
        self.wkss = wkss
        self.top_left = top_left
        self.scale_set = scale_set
        self.tile_size = tile_size
        self.initial_matrix_exponents = initial_matrix_exponents
        self.layer_suffix = layer_suffix

    @property
    def crs_display(self):
        if self.force_raw_crs_name:
            return self.crs_name
        if self.crs_name[:5] == "EPSG:":
            return f"urn:ogc:def:crs:EPSG::{self.crs_name[5:]}"
        return self.crs_name

# Scale denominators for WebMercator QuadTree Scale Set, starting from zoom level 0.
# Currently goes to zoom level 14, where the pixel size at the equator is ~10m (i.e. Sentinel2 resolution)
# Taken from the WMTS 1.0.0 spec, Annex E.4
# Don't even think about changing these numbers unless you really, really know what you are doing.

WebMercScaleSet = [
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

google_web_mercator = TileMatrixSet(
    "WholeWorld_WebMercator",
    "EPSG:3857",
    (-20037508.3427892, 20037508.3427892),
    (256, 256),
    WebMercScaleSet,
    "webmerc",
    wkss="urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible",
)

supported_tile_matrix_sets = [
    google_web_mercator,
]
