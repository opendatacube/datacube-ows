from .wms_cfg import service_cfg, layer_cfg
import datacube

def accum_min(a, b):
    if a is None:
        return b
    elif b is None:
        return a
    else:
        return min(a,b)

def accum_max(a, b):
    if a is None:
        return b
    elif b is None:
        return a
    else:
        return max(a,b)

class ProductLayerDef(object):
    def __init__(self, product_cfg, platform_def, dc=None):
        self.platform = platform_def
        self.name = product_cfg["name"]
        self.product_label = product_cfg["label"]
        self.product_type = product_cfg["type"]
        self.product_variant = product_cfg["variant"]
        if not dc:
            dc = datacube.Datacube(app="wms")
        self.dc = dc
        self.product = dc.index.products.get_by_name(self.name)
        self.definition = self.product.definition
        self.title = "%s %s %s (%s)" % (platform_def.title, 
                self.product_variant,
                self.product_type,
                self.product_label)
        self._ranges = None

    @property
    def ranges(self):
        # TODO: This will not scale.
        if self._ranges is None:
            self._ranges = self._determine_ranges()
        return self._ranges

    def _determine_ranges(self):
        r = {
            "lat": {
                "min": None,
                "max": None
            },
            "lon": {
                "min": None,
                "max": None
            },
            "time_set": set(),
            "extents": { crs: None for crs in service_cfg["published_CRSs"] }
        }
        crses = { crs: datacube.utils.geometry.CRS(crs) for crs in service_cfg["published_CRSs"] }

        for ds in self.dc.find_datasets(product=self.name):
            r["lat"]["min"] = accum_min(r["lat"]["min"], ds.metadata.lat.begin)
            r["lat"]["max"] = accum_max(r["lat"]["max"], ds.metadata.lat.end)
            r["lon"]["min"] = accum_min(r["lon"]["min"], ds.metadata.lon.begin)
            r["lon"]["max"] = accum_max(r["lon"]["max"], ds.metadata.lon.end)

            r["time_set"].add(ds.center_time.date())
            
            for crsid in service_cfg["published_CRSs"]:
                crs = crses[crsid]
                ext = ds.extent
                if ext.crs != crs:
                    ext = ext.to_crs(crs)
                if r["extents"][crsid] is None:
                    r["extents"][crsid] = ext
                else:
                    r["extents"][crsid] = r["extents"][crsid].union(ext)
                
        r["times"] = sorted(r["time_set"])
        r["bboxes"] = { crsid: r["extents"][crsid].boundingbox for crsid in service_cfg["published_CRSs"] }
        return r

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

