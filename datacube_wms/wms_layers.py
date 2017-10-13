from .wms_cfg import layer_cfg
import datacube

class ProductLayerDef(object):
    def __init__(self, product_cfg, platform_def, dc=None):
        self.platform = platform_def
        self.name = product_cfg["name"]
        self.product_label = product_cfg["label"]
        self.product_type = product_cfg["type"]
        self.product_variant = product_cfg["variant"]
        if not dc:
            dc = datacube.Datacube(app="wms")
        self.product = dc.index.products.get_by_name(self.name)
        self.definition = self.product.definition
        self.title = "%s %s %s (%s)" % (platform_def.title, 
                self.product_variant,
                self.product_type,
                self.product_label)

class PlatformLayerDef(object):
    def __init__(self, platform_cfg, prod_idx, dc=None):
        self.name = platform_cfg["name"]
        self.title = platform_cfg["title"]
        self.abstract = platform_cfg["abstract"]
        self.styles = platform_cfg["styles"]
        self.products = []
        for prod_cfg in platform_cfg["products"]:
            prod = ProductLayerDef(prod_cfg, self, dc=dc)
            self.products.append(prod)
            prod_idx[prod.name] = prod

class LayerDefs(object):
    def __init__(self, platforms_cfg, dc=None):
        self.platforms = []
        self.platform_index = {}
        self.product_index = {}
        for platform_cfg in platforms_cfg:
            platform = PlatformLayerDef(platform_cfg, self.product_index, dc=dc)
            self.platforms.append(platform)
            self.platform_index[platform.name] = platform
    def __iter__(self):
        for p in self.platforms:
            yield p
    def __getitem__(self, name):
        if isinstance(name, int):
            return self.platforms[name]
        else:
            return self.platform_index[name]

# TODO: This is not scalable
def get_layers(dc=None):
    return LayerDefs(layer_cfg, dc=dc)

