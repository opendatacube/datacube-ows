# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from xarray import Dataset

from datacube_ows.styles.base import StyleDefBase
from datacube_ows.styles.component import ComponentStyleDef
from datacube_ows.styles.ramp import ColorRampDef


class HybridStyleDef(ColorRampDef, ComponentStyleDef):
    auto_legend = False
    def __init__(self, product, style_cfg, defer_multi_date=False, stand_alone=False, user_defined=False):
        super(HybridStyleDef, self).__init__(product, style_cfg,
                                             defer_multi_date=defer_multi_date,
                                             stand_alone=stand_alone,
                                             user_defined=user_defined)
        style_cfg = self._raw_cfg
        self.component_ratio = style_cfg["component_ratio"]

    def transform_single_date_data(self, data):
        #pylint: disable=too-many-locals
        if self.index_function is not None:
            data['index_function'] = (data.dims, self.index_function(data))

        imgdata = Dataset(coords=data)

        d = data['index_function']
        for band, intensity in self.rgb_components.items():
            rampdata = self.color_ramp.get_value(d, band)
            component_band_data = None
            if band in self.rgb_components:
                for c_band, c_intensity in self.rgb_components[band].items():
                    if callable(c_intensity):
                        imgband_component_data = c_intensity(data[c_band], c_band, band)
                    else:
                        imgband_component_data = data[c_band] * c_intensity
                    if component_band_data is not None:
                        component_band_data += imgband_component_data
                    else:
                        component_band_data = imgband_component_data
                    if band != "alpha":
                        component_band_data = self.compress_band(band, component_band_data)
                img_band_data = (rampdata * 255.0 * (1.0 - self.component_ratio)
                                 + self.component_ratio * component_band_data)
            else:
                img_band_data = rampdata * 255.0
            imgdata[band] = (d.dims, img_band_data.astype("uint8"))

        return imgdata


StyleDefBase.register_subclass(HybridStyleDef, "component_ratio", priority=True)
