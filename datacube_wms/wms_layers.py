from datacube_wms.wms_cfg import service_cfg, layer_cfg
from xarray import Dataset
import numpy
import datacube
from datacube_wms.product_ranges import get_ranges
from datacube_wms.cube_pool import get_cube, release_cube

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
        self.product_label = product_cfg["label"]
        self.product_type = product_cfg["type"]
        self.product_variant = product_cfg["variant"]
        self.product = dc.index.products.get_by_name(self.name)
        self.definition = self.product.definition
        self.title = "%s %s %s (%s)" % (platform_def.title,
                                        self.product_variant,
                                        self.product_type,
                                        self.product_label)
        self.ranges = get_ranges(dc, self.product)


class StyleDef(object):
    def __init__(self, style_cfg):
        self.name = style_cfg["name"]
        self.title = style_cfg["title"]
        self.abstract = style_cfg["abstract"]
        self.red_components = style_cfg["components"]["red"]
        self.green_components = style_cfg["components"]["green"]
        self.blue_components = style_cfg["components"]["blue"]
        self.scale_factor = style_cfg["scale_factor"]
        self.needed_bands = set()
        for band in self.red_components.keys():
            self.needed_bands.add(band)
        for band in self.green_components.keys():
            self.needed_bands.add(band)
        for band in self.blue_components.keys():
            self.needed_bands.add(band)

    @property
    def components(self):
        return {
            "red": self.red_components,
            "green": self.green_components,
            "blue": self.blue_components,
        }

    def transform_data(self, data):
        imgdata = Dataset()
        for imgband, components in self.components.items():
            imgband_data = None
            for band, intensity in components.items():
                imgband_component = data[band] * intensity
                if imgband_data is not None:
                    imgband_data += imgband_component
                else:
                    imgband_data = imgband_component
            dims = imgband_data.dims
            imgband_data = numpy.clip(imgband_data.values[::-1] / self.scale_factor, 0, 255).astype('uint8')
            imgdata[imgband] = (dims, imgband_data)
        return imgdata


class PlatformLayerDef(object):
    def __init__(self, platform_cfg, prod_idx, dc=None):
        self.name = platform_cfg["name"]
        self.title = platform_cfg["title"]
        self.abstract = platform_cfg["abstract"]
        self.styles = platform_cfg["styles"]
        self.default_style = platform_cfg["default_style"]
        self.style_index = {s["name"]: StyleDef(s) for s in self.styles}
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

    def __init__(self, platforms_cfg):
        if not self.initialised:
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


def get_layers():
    return LayerDefs(layer_cfg)
