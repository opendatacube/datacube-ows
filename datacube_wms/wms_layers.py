try:
    from datacube_wms.wms_cfg_local import layer_cfg
except:
    from datacube_wms.wms_cfg import layer_cfg
from datacube_wms.product_ranges import get_ranges, get_sub_ranges
from datacube_wms.cube_pool import get_cube, release_cube
from datacube_wms.band_mapper import StyleDef


def accum_min(a, b):
    if a is None:
        return b
    elif b is None:
        return a
    else:
        return min(a, b)


def accum_max(a, b):
    if a is None:
        return b
    elif b is None:
        return a
    else:
        return max(a, b)


class ProductLayerDef(object):
    def __init__(self, product_cfg, platform_def, dc):
        self.platform = platform_def
        self.name = product_cfg["name"]
        self.product_name = product_cfg["product_name"]
        if "__" in self.product_name:
            raise Exception("Product names cannot have a double underscore '__' in them.")
        self.product_label = product_cfg["label"]
        self.product_type = product_cfg["type"]
        self.product_variant = product_cfg["variant"]
        self.product = dc.index.products.get_by_name(self.product_name)
        self.definition = self.product.definition
        self.title = "%s %s %s (%s)" % (platform_def.title,
                                        self.product_variant,
                                        self.product_type,
                                        self.product_label)
        self.ranges = get_ranges(dc, self.product)
        self.sub_ranges = get_sub_ranges(dc, self.product)
        self.pq_name = product_cfg.get("pq_dataset")
        self.pq_band = product_cfg.get("pq_band")
        self.min_zoom = product_cfg.get("min_zoom_factor", 300.0)
        self.zoom_fill = product_cfg.get("zoomed_out_fill_colour", [150, 180, 200])
        self.ignore_flags_info = product_cfg.get("ignore_flags_info", [])
        self.always_fetch_bands = product_cfg.get("always_fetch_bands", [])
        self.data_manual_merge = product_cfg.get("data_manual_merge", False)
        self.band_drill = product_cfg.get("band_drill", [])
        self.solar_correction = product_cfg.get("apply_solar_corrections", False)
        self.sub_product_extractor = product_cfg.get("sub_product_extractor", None)
        self.sub_product_label = product_cfg.get("sub_product_label", None)
        if self.pq_name:
            self.pq_product = dc.index.products.get_by_name(self.pq_name)
            self.info_mask = ~0
            fd = self.pq_product.measurements[self.pq_band]["flags_definition"]
            for bitname in self.ignore_flags_info:
                bit = fd[bitname]["bits"]
                if not isinstance(bit, int):
                    continue
                flag = 1 << bit
                self.info_mask &= ~flag
        else:
            self.pq_product = None
        self.time_zone = product_cfg.get("time_zone", 9)
        self.styles = product_cfg["styles"]
        self.default_style = product_cfg["default_style"]
        self.style_index = {s["name"]: StyleDef(self, s) for s in self.styles}
        try:
            i = iter(product_cfg["extent_mask_func"])
            self.extent_mask_func = product_cfg["extent_mask_func"]
        except TypeError:
            self.extent_mask_func = [product_cfg["extent_mask_func"]]
        self.pq_manual_merge = product_cfg.get("pq_manual_merge", False)

class PlatformLayerDef(object):
    def __init__(self, platform_cfg, prod_idx, dc=None):
        self.name = platform_cfg["name"]
        self.title = platform_cfg["title"]
        self.abstract = platform_cfg["abstract"]

        self.products = []
        for prod_cfg in platform_cfg["products"]:
            prod = ProductLayerDef(prod_cfg, self, dc=dc)
            self.products.append(prod)
            prod_idx[prod.name] = prod


class LayerDefs(object):
    _instance = None
    initialised = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LayerDefs, cls).__new__(cls)
        return cls._instance

    def __init__(self, platforms_cfg, refresh=False):
        if not self.initialised or refresh:
            self.initialised = True
            self.platforms = []
            self.platform_index = {}
            self.product_index = {}
            dc = get_cube()
            for platform_cfg in platforms_cfg:
                platform = PlatformLayerDef(platform_cfg, self.product_index, dc=dc)
                self.platforms.append(platform)
                self.platform_index[platform.name] = platform
            release_cube(dc)

    def __iter__(self):
        for p in self.platforms:
            yield p

    def __getitem__(self, name):
        if isinstance(name, int):
            return self.platforms[name]
        else:
            return self.platform_index[name]


def get_layers(refresh = False):
    return LayerDefs(layer_cfg, refresh)
