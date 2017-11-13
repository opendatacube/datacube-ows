from xarray import Dataset
import numpy

class StyleDefBase(object):
    def __init__(self, style_cfg):
        self.name = style_cfg["name"]
        self.title = style_cfg["title"]
        self.abstract = style_cfg["abstract"]

    def transform_data(self, data):
        pass

class LinearStyleDef(StyleDefBase):
    def __init__(self, style_cfg):
        super(LinearStyleDef, self).__init__(style_cfg)
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
            imgband_data = numpy.clip(imgband_data.values / self.scale_factor, 0, 255).astype('uint8')
            imgdata[imgband] = (dims, imgband_data)
        return imgdata

def hm_index_to_blue(val, rmin, rmax):
    scaled = (val - rmin)/(rmax-rmin)
    if scaled < 0.0:
        return float("nan")
    elif scaled > 0.5:
        return 0.0
    elif scaled < 0.1:
        return 0.5 + scaled * 5.0
    elif scaled > 0.3:
        return 2.5 - scaled * 5.0
    else:
        return 1.0

def hm_index_to_green(val, rmin, rmax):
    scaled = (val - rmin)/(rmax-rmin)
    if scaled < 0.0:
        return float("nan")
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

def hm_index_to_red(val, rmin, rmax):
    scaled = (val - rmin)/(rmax-rmin)
    if scaled < 0.0:
        return float("nan")
    elif scaled < 0.5:
        return 0.0
    elif scaled < 0.7:
        return -2.5 + scaled * 5.0
    elif scaled > 0.9:
        return 5.5 - scaled * 5.0
    else:
        return 1.0

def hm_index_func_for_range(func, rmin, rmax):
    def hm_index_func(val):
        return func(val, rmin, rmax)
    return hm_index_func

class HeatMappedStyleDef(StyleDefBase):
    def __init__(self, style_cfg):
        super(HeatMappedStyleDef, self).__init__(style_cfg)
        self.needed_bands = set()
        for b in style_cfg["needed_bands"]:
            self.needed_bands.add(b)
        self._index_function = style_cfg["index_function"]
        self.range = style_cfg["range"]
    def _masked_index_function(self, data):
        result_mask = None
        # This forces the result to be highly negative when any included band is not available.
        for band in list(self.needed_bands):
            band_mask = data[band] - abs(data[band])
            if result_mask is None:
                result_mask = band_mask
            else:
                result_mask *= band_mask
        return self._index_function(data) + band_mask
    def transform_data(self, data):
        hm_index_data = self._masked_index_function(data).values
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
            img_band_data = numpy.clip(img_band_raw_data*255.0, 0, 255).astype("uint8")
            imgdata[band] = (dims, img_band_data)
        return imgdata

def StyleDef(cfg):
    if cfg.get("heat_mapped", False):
        return HeatMappedStyleDef(cfg)
    else:
        return LinearStyleDef(cfg)

