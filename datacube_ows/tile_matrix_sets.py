

class TileMatrixSet:
    def __init__(self, identifier, crs_name,
                 top_left, tile_size,
                 scale_set,
                 unit_coefficients=(1.0, -1.0),
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
        self.unit_coefficients = unit_coefficients

    @property
    def crs_display(self):
        if self.force_raw_crs_name:
            return self.crs_name
        if self.crs_name[:5] == "EPSG:":
            return f"urn:ogc:def:crs:EPSG::{self.crs_name[5:]}"
        return self.crs_name

    def exponent(self, idx, scale_no):
        init = self.initial_matrix_exponents[idx]
        exponent = scale_no - init
        if exponent < 0:
            return 0
        return exponent

    def width_exponent(self, scale_no):
        return self.exponent(0, scale_no)

    def height_exponent(self, scale_no):
        return self.exponent(1, scale_no)

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

vicgrid_geocortex_scale_set = [
    7559538.928601667,
    3779769.4643008336,
    1889884.7321504168,
    944942.3660752084,
    472471.1830376042,
    236235.5915188021,
    94494.23660752083,
    47247.11830376041,
    23623.559151880207,
    9449.423660752083,
    4724.711830376042,
    2362.355915188021,
    1181.1779575940104,
    755.9538928601667,
]

google_web_mercator = TileMatrixSet(
    "WholeWorld_WebMercator",
    "EPSG:3857",
    (-20037508.3427892, 20037508.3427892),
    (256, 256),
    webmerc_scale_set,
    wkss="urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible",
)

vicgrid_geocortex_compatible = TileMatrixSet(
    "EPSG:3111",
    "EPSG:3111",
    (1786000.0, 3081000.0),
    (512, 512),
    vicgrid_geocortex_scale_set,
    initial_matrix_exponents=(-1, 0),
)

supportable_tile_matrix_sets = [
    google_web_mercator,
    vicgrid_geocortex_compatible,
]
