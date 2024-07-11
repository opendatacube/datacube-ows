# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Callable, Hashable, cast

import numpy as np
from xarray import DataArray, Dataset

from datacube_ows.config_utils import (CFG_DICT, ConfigException,
                                       FunctionWrapper)
from datacube_ows.styles.base import StyleDefBase

TYPE_CHECKING = False
if TYPE_CHECKING:
    from datacube_ows.ows_configuration import OWSNamedLayer

# pylint: disable=abstract-method

LINEAR_COMP_DICT = dict[str, float | list[float]]


class ComponentStyleDef(StyleDefBase):
    """
    Style Subclass that allows the behaviour of each component (red, green, blue, alpha) to be
    specified independently.
    """
    def __init__(self, product: "OWSNamedLayer",
                 style_cfg: CFG_DICT,
                 stand_alone: bool = False,
                 defer_multi_date: bool = False,
                 user_defined: bool = False) -> None:
        """
        See superclass
        """
        super().__init__(product, style_cfg,
                         stand_alone=stand_alone, defer_multi_date=defer_multi_date, user_defined=user_defined)
        style_cfg: CFG_DICT = cast(CFG_DICT, self._raw_cfg)
        self.raw_rgb_components: dict[str, Callable | LINEAR_COMP_DICT] = {}
        raw_components = cast(dict[str, Callable | LINEAR_COMP_DICT], style_cfg["components"])
        for imgband in ["red", "green", "blue", "alpha"]:
            components = cast(Callable | LINEAR_COMP_DICT | CFG_DICT | None, raw_components.get(imgband))
            if components is None:
                if imgband == "alpha":
                    continue
                else:
                    raise ConfigException(f"No components defined for {imgband} band in style {self.name}, layer {product.name}")
            elif callable(components) or "function" in components:
                self.raw_rgb_components[imgband] = FunctionWrapper(self.product, cast(CFG_DICT | Callable, components),
                                                                   stand_alone=self.stand_alone)
                if not self.stand_alone:
                    if "additional_bands" not in style_cfg:
                        raise ConfigException(f"Style with a function component must declare additional_bands.")
                    for b in cast(list[str], style_cfg.get("additional_bands", [])):
                        self.raw_needed_bands.add(b)
            else:
                components = cast(LINEAR_COMP_DICT, components)
                self.raw_rgb_components[imgband] = components
                for k in components.keys():
                    if k != "scale_range":
                        self.raw_needed_bands.add(k)
        self.rgb_components = cast(dict[str, None | Callable | LINEAR_COMP_DICT], {})

        self.scale_factor = cast(float, style_cfg.get("scale_factor"))
        if "scale_range" in style_cfg:
            self.scale_min, self.scale_max = cast(list[float | None], style_cfg["scale_range"])
        elif self.scale_factor:
            self.scale_min = 0.0
            self.scale_max = 255.0 * self.scale_factor
        else:
            self.scale_min = None
            self.scale_max = None

        self.component_scale_ranges: dict[str, dict[str, float]] = {}
        for cn, cd in raw_components.items():
            if not callable(cd) and "scale_range" in cd:
                scale_range = cast(list[float], cd["scale_range"])
                self.component_scale_ranges[cn] = {
                    "min": scale_range[0],
                    "max": scale_range[1],
                }
            else:
                self.component_scale_ranges[cn] = {
                    "min": cast(float, self.scale_min),
                    "max": cast(float, self.scale_max),
                }

    # pylint: disable=attribute-defined-outside-init
    def make_ready(self, *args: Any, **kwargs: Any) -> None:
        """
        Second-phase (db aware) initialisation

        Mostly sorting out bands, esp flag bands.

        :param dc: A datacube object
        """
        self.rgb_components = cast(dict[str, None | Callable | LINEAR_COMP_DICT], {})
        for band, component in self.raw_rgb_components.items():
            if not component or callable(component):
                self.rgb_components[band] = component
            else:
                self.rgb_components[band] = self.dealias_components(component)
        super().make_ready(*args, **kwargs)
        self.raw_rgb_components = {}

    def dealias_components(self, comp_in: LINEAR_COMP_DICT | None) -> LINEAR_COMP_DICT | None:
        """
        Convert a component dictionary with band aliases to a component dictionary using canonical band names.

        :param comp_in: A linear component dictionary with band aliases
        :return: Equivalent linear component dictionary with canonical band names.
        """
        if self.stand_alone:
            return comp_in
        elif comp_in is None:
            return None
        else:
            return {
                self.product.band_idx.band(self.local_band(band_alias)): value
                for band_alias, value in comp_in.items() if band_alias not in ['scale_range']
            }

    def compress_band(self, component_name: str, imgband_data: DataArray) -> DataArray:
        """
        Compress dynamic range of a component data array to uint8 range (0-255)

        :param component_name: The name of the component being compressed (i.e. 'red', 'green', 'blue' or 'alpha')
        :param imgband_data: The input, uncompressed DataArray for the component
        :return:
        """
        sc_min: float = self.component_scale_ranges[component_name]["min"]
        sc_max: float = self.component_scale_ranges[component_name]["max"]
        clipped = imgband_data.clip(sc_min, sc_max)
        normalized = (clipped - sc_min) / (sc_max - sc_min)
        return normalized * 255


    def transform_single_date_data(self, data: Dataset) -> Dataset:
        """
        Apply style to raw data to make an RGBA image xarray (single time slice only)

        :param data: Raw data, all bands.
        :return: RGBA uint8 xarray
        """
        imgdata = cast(dict[Hashable, Any], {})
        for imgband, components in cast(dict[str, Callable | LINEAR_COMP_DICT], self.rgb_components).items():
            if callable(components):
                imgband_data = components(data)
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
                    null_np = np.zeros(tuple(data.sizes.values()), 'float64')
                    imgband_data = DataArray(null_np, data.coords, tuple(data.sizes.keys()))
                if imgband != "alpha":
                    imgband_data = self.compress_band(imgband, imgband_data)
                imgdata[imgband] = imgband_data.astype("uint8")

        image_dataset = Dataset(imgdata)
        return image_dataset


# Register ComponentStyleDef as a Style subclass.
StyleDefBase.register_subclass(ComponentStyleDef, "components")
