from xarray import Dataset, DataArray
import numpy as np

from datacube_ows.ogc_utils import ConfigException, FunctionWrapper
from datacube_ows.styles.base import StyleDefBase

# pylint: disable=abstract-method
class ComponentStyleDef(StyleDefBase):
    def __init__(self, product, style_cfg, local_band_map=None):
        super().__init__(product, style_cfg, local_band_map)
        self.rgb_components = {}
        for imgband in ["red", "green", "blue", "alpha"]:
            components = style_cfg["components"].get(imgband)
            if components is None:
                if imgband == "alpha":
                    continue
                else:
                    raise ConfigException(f"No components defined for {imgband} band in style {self.name}, layer {product.name}")
            if "function" in components:
                self.rgb_components[imgband] = FunctionWrapper(self.product, components)
                for b in style_cfg["additional_bands"]:
                    self.needed_bands.add(self.local_band(b))
            else:
                self.rgb_components[imgband] = self.dealias_components(components)

        self.scale_factor = style_cfg.get("scale_factor")
        if "scale_range" in style_cfg:
            self.scale_min, self.scale_max = style_cfg["scale_range"][-2:]
        elif self.scale_factor:
            self.scale_min = 0.0
            self.scale_max = 255.0 * self.scale_factor
        else:
            self.scale_min = None
            self.scale_max = None

        self.component_scale_ranges = {}
        for cn, cd in style_cfg["components"].items():
            if "scale_range" in cd:
                self.component_scale_ranges[cn] = {
                    "min": cd["scale_range"][0],
                    "max": cd["scale_range"][1],
                }
            else:
                self.component_scale_ranges[cn] = {
                    "min": self.scale_min,
                    "max": self.scale_max,
                }

        for imgband in ["red", "green", "blue", "alpha" ]:
            if imgband in self.rgb_components and not callable(self.rgb_components[imgband]):
                for band in self.rgb_components[imgband].keys():
                    self.needed_bands.add(band)

    def dealias_components(self, comp_in):
        if comp_in is None:
            return None
        else:
            return { self.product.band_idx.band(self.local_band(band_alias)): value for band_alias, value in comp_in.items() if band_alias not in [ 'scale_range'] }

    def compress_band(self, component_name, imgband_data):
        sc_min = self.component_scale_ranges[component_name]["min"]
        sc_max = self.component_scale_ranges[component_name]["max"]
        clipped = imgband_data.clip(sc_min, sc_max)
        normalized = (clipped - sc_min) / (sc_max - sc_min)
        return normalized * 255


    def transform_single_date_data(self, data):
        imgdata = Dataset()
        for imgband, components in self.rgb_components.items():
            if callable(components):
                imgband_data = components(data)
                dims = imgband_data.dims
                imgband_data = imgband_data.astype('uint8')
                imgdata[imgband] = (dims, imgband_data)
            else:
                imgband_data = None
                for band, intensity in components.items():
                    if callable(intensity):
                        imgband_component = intensity(data[band], band, imgband)
                    else:
                        imgband_component = data[band] * intensity

                    if imgband_data is not None:
                        imgband_data += imgband_component
                    else:
                        imgband_data = imgband_component
                if imgband_data is None:
                    imgband_data = np.zeros(list(data.dims.values()), 'uint8')
                    imgband_data = DataArray(imgband_data, data.coords, data.dims.keys())
                if imgband != "alpha":
                    imgband_data = self.compress_band(imgband, imgband_data)
                imgdata[imgband] = (imgband_data.dims,
                                    imgband_data.astype("uint8"))
        return imgdata


StyleDefBase.register_subclass(ComponentStyleDef, "components")
