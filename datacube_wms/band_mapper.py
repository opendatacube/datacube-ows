from xarray import Dataset
import numpy

from datacube.storage.masking import make_mask


class StyleMask(object):
    def __init__(self, flags, invert=False):
        self.flags = flags
        self.invert = invert

class StyleDefBase(object):
    def __init__(self, product, style_cfg):
        self.product = product
        self.name = style_cfg["name"]
        self.title = style_cfg["title"]
        self.abstract = style_cfg["abstract"]
        self.masks = [ StyleMask(**mask_cfg) for mask_cfg in style_cfg.get("pq_masks", []) ]
        self.needed_bands = set()
        for band in self.product.always_fetch_bands:
            self.needed_bands.add(band)

    def apply_masks(self, data, pq_data):
        if pq_data:
            net_mask = None
            for mask in self.masks:
                odc_mask = make_mask(pq_data, **mask.flags)
                mask_data = getattr(odc_mask, self.product.pq_band)
                if mask.invert:
                    mask_data = ~mask_data
                data = data.where(mask_data)
        return data

    def transform_data(self, data, extent_mask, *masks):
        pass


class LinearStyleDef(StyleDefBase):
    def __init__(self, product, style_cfg):
        super(LinearStyleDef, self).__init__(product, style_cfg)
        self.red_components = style_cfg["components"]["red"]
        self.green_components = style_cfg["components"]["green"]
        self.blue_components = style_cfg["components"]["blue"]
        self.scale_factor = style_cfg["scale_factor"]
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

    def transform_data(self, data, pq_data, extent_mask):
        data = data.where(extent_mask)
        data = self.apply_masks(data, pq_data)
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
            imgband_data = numpy.clip(imgband_data.values / self.scale_factor, -1, 254) + 1
            imgband_data = imgband_data.astype('uint8')
            imgdata[imgband] = (dims, imgband_data)
        return imgdata


def hm_index_to_blue(val, rmin, rmax, nan_mask=True):
    scaled = (val - rmin) / (rmax - rmin)
    if scaled < 0.0:
        if nan_mask:
            return float("nan")
        else:
            return 0.0
    elif scaled > 0.5:
        return 0.0
    elif scaled < 0.1:
        return 0.5 + scaled * 5.0
    elif scaled > 0.3:
        return 2.5 - scaled * 5.0
    else:
        return 1.0


def hm_index_to_green(val, rmin, rmax, nan_mask=True):
    scaled = (val - rmin) / (rmax - rmin)
    if scaled < 0.0:
        if nan_mask:
            return float("nan")
        else:
            return 0.0
    elif scaled > 0.9:
        return 0.0
    elif scaled < 0.1:
        return 0.0
    elif scaled < 0.3:
        return -0.5 + scaled * 5.0
    elif scaled > 0.7:
        return 4.5 - scaled * 5.0
    else:
        return 1.0


def hm_index_to_red(val, rmin, rmax, nan_mask=True):
    scaled = (val - rmin) / (rmax - rmin)
    if scaled < 0.0:
        if nan_mask:
            return float("nan")
        else:
            return 0.0
    elif scaled < 0.5:
        return 0.0
    elif scaled < 0.7:
        return -2.5 + scaled * 5.0
    elif scaled > 0.9:
        return 5.5 - scaled * 5.0
    else:
        return 1.0


def hm_index_func_for_range(func, rmin, rmax, nan_mask=True):
    def hm_index_func(val):
        return func(val, rmin, rmax, nan_mask=nan_mask)

    return hm_index_func


class HeatMappedStyleDef(StyleDefBase):
    def __init__(self, product, style_cfg):
        super(HeatMappedStyleDef, self).__init__(product, style_cfg)
        for b in style_cfg["needed_bands"]:
            self.needed_bands.add(b)
        self._index_function = style_cfg["index_function"]
        self.range = style_cfg["range"]

    def transform_data(self, data, pq_data, extent_mask):
        hm_index_data = self._index_function(data)
        dims = data[list(self.needed_bands)[0]].dims
        imgdata = Dataset()
        for band, map_func in [
                ("red", hm_index_to_red),
                ("green", hm_index_to_green),
                ("blue", hm_index_to_blue),
        ]:
            f = numpy.vectorize(
                hm_index_func_for_range(
                    map_func,
                    self.range[0],
                    self.range[1]
                )
            )
            img_band_raw_data = f(hm_index_data)
            img_band_data = numpy.clip(img_band_raw_data * 255.0, 0, 255).astype("uint8")
            imgdata[band] = (dims, img_band_data)
        imgdata = imgdata.where(extent_mask)
        imgdata = self.apply_masks(imgdata, pq_data)
        imgdata = imgdata.astype("uint8")
        return imgdata


class HybridStyleDef(HeatMappedStyleDef, LinearStyleDef):
    def __init__(self, product, style_cfg):
        super(HybridStyleDef, self).__init__(product, style_cfg)
        self.component_ratio = style_cfg["component_ratio"]

    def transform_data(self, data, pq_data, extent_mask):
        hm_index_data = self._index_function(data)
        hm_mask = hm_index_data != float("nan")
        data = self.apply_masks(data, pq_data)

        dims = data[list(self.needed_bands)[0]].dims
        imgdata = Dataset()
        for band, map_func in [
                ("red", hm_index_to_red),
                ("green", hm_index_to_green),
                ("blue", hm_index_to_blue),
        ]:
            components = self.components[band]
            component_band_data = None
            for c_band, c_intensity in components.items():
                imgband_component_data = data[c_band] * c_intensity
                if component_band_data is not None:
                    component_band_data += imgband_component_data
                else:
                    component_band_data = imgband_component_data
            f = numpy.vectorize(
                hm_index_func_for_range(
                    map_func,
                    self.range[0],
                    self.range[1],
                    nan_mask=False
                )
            )
            hmap_raw_data = f(hm_index_data)
            unclipped_band_data = hmap_raw_data * 255.0 * (
                1.0 - self.component_ratio) + self.component_ratio / self.scale_factor * imgband_component_data
            img_band_data = numpy.clip(unclipped_band_data, 1, 254) + 1
            img_band_data = img_band_data.astype("uint8")
            imgdata[band] = (dims, img_band_data)
        imgdata = imgdata.where(extent_mask)
        imgdata = imgdata.where(hm_mask)
        imgdata = self.apply_masks(imgdata, pq_data)
        imgdata = imgdata.astype("uint8")
        return imgdata


def StyleDef(product, cfg):
    if cfg.get("component_ratio", False):
        return HybridStyleDef(product, cfg)
    if cfg.get("heat_mapped", False):
        return HeatMappedStyleDef(product, cfg)
    elif cfg.get("components", False):
        return LinearStyleDef(product, cfg)
