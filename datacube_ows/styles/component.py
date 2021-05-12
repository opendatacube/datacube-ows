# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import numpy as np
from xarray import DataArray, Dataset

from datacube_ows.ogc_utils import ConfigException, FunctionWrapper
from datacube_ows.styles.base import StyleDefBase

# pylint: disable=abstract-method


class ComponentStyleDef(StyleDefBase):
    def __init__(self, product, style_cfg,
                 stand_alone=False, defer_multi_date=False, user_defined=False):
        super().__init__(product, style_cfg,
                         stand_alone=stand_alone, defer_multi_date=defer_multi_date, user_defined=user_defined)
        style_cfg = self._raw_cfg
        self.raw_rgb_components = {}
        for imgband in ["red", "green", "blue", "alpha"]:
            components = style_cfg["components"].get(imgband)
            if components is None:
                if imgband == "alpha":
                    continue
                else:
                    raise ConfigException(f"No components defined for {imgband} band in style {self.name}, layer {product.name}")
            if callable(components) or "function" in components:
                self.raw_rgb_components[imgband] = FunctionWrapper(self.product, components,
                                                                   stand_alone=self.stand_alone)
                if not self.stand_alone:
                    if "additional_bands" not in style_cfg:
                        raise ConfigException(f"Style with a function component must declare additional_bands.")
                    for b in style_cfg.get("additional_bands", set()):
                        self.raw_needed_bands.add(b)
            else:
                self.raw_rgb_components[imgband] = components
                for k in components.keys():
                    if k != "scale_range":
                        self.raw_needed_bands.add(k)
        self.declare_unready("rgb_components")

        self.scale_factor = style_cfg.get("scale_factor")
        if "scale_range" in style_cfg:
            self.scale_min, self.scale_max = style_cfg["scale_range"]
        elif self.scale_factor:
            self.scale_min = 0.0
            self.scale_max = 255.0 * self.scale_factor
        else:
            self.scale_min = None
            self.scale_max = None

        self.component_scale_ranges = {}
        for cn, cd in style_cfg["components"].items():
            if not callable(cd) and "scale_range" in cd:
                self.component_scale_ranges[cn] = {
                    "min": cd["scale_range"][0],
                    "max": cd["scale_range"][1],
                }
            else:
                self.component_scale_ranges[cn] = {
                    "min": self.scale_min,
                    "max": self.scale_max,
                }

    # pylint: disable=attribute-defined-outside-init
    def make_ready(self, dc, *args, **kwargs):
        self.rgb_components = {}
        for band, component in self.raw_rgb_components.items():
            if not component or callable(component):
                self.rgb_components[band] = component
            else:
                self.rgb_components[band] = self.dealias_components(component)
        super().make_ready(dc, *args, **kwargs)

    def dealias_components(self, comp_in):
        if self.stand_alone:
            return comp_in
        elif comp_in is None:
            return None
        else:
            return {self.product.band_idx.band(self.local_band(band_alias)): value for band_alias, value in comp_in.items() if band_alias not in ['scale_range']}

    def compress_band(self, component_name, imgband_data):
        sc_min = self.component_scale_ranges[component_name]["min"]
        sc_max = self.component_scale_ranges[component_name]["max"]
        clipped = imgband_data.clip(sc_min, sc_max)
        normalized = (clipped - sc_min) / (sc_max - sc_min)
        return normalized * 255


    def transform_single_date_data(self, data):
        imgdata = {}
        for imgband, components in self.rgb_components.items():
            if callable(components):
                imgband_data = components(data)
                dims = imgband_data.dims
                imgband_data = imgband_data.astype('uint8')
                imgdata[imgband] = imgband_data
            else:
                imgband_data = None
                for band, intensity in components.items():
                    if callable(intensity):
                        imgband_component = intensity(data[band], band, imgband)
                    elif band == "scale_range":
                        continue
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
                imgdata[imgband] = imgband_data.astype("uint8")

        image_dataset = Dataset(imgdata)
        return image_dataset


StyleDefBase.register_subclass(ComponentStyleDef, "components")
