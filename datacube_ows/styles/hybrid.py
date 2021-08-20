# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from typing import Optional, Union, cast

from xarray import DataArray, Dataset

from datacube_ows.config_utils import CFG_DICT
from datacube_ows.ogc_utils import ConfigException
from datacube_ows.styles.base import StyleDefBase
from datacube_ows.styles.component import ComponentStyleDef
from datacube_ows.styles.ramp import ColorRampDef


class HybridStyleDef(ColorRampDef, ComponentStyleDef):
    """
    Hybrid component/colour ramp style type.

    Returns a linear blend of a component image and colour ramp image
    """
    auto_legend = False

    def __init__(self,
                 product: "datacube_ows.ows_configuration.OWSNamedLayer",
                 style_cfg: CFG_DICT,
                 defer_multi_date: bool = False,
                 stand_alone: bool = False,
                 user_defined: bool = False) -> None:
        """
        See StyleBaseDef
        """
        super().__init__(product, style_cfg,
                                 defer_multi_date=defer_multi_date,
                                 stand_alone=stand_alone,
                                 user_defined=user_defined)
        style_cfg = cast(CFG_DICT, self._raw_cfg)
        self.component_ratio = float(cast(Union[float, str], style_cfg["component_ratio"]))
        if self.component_ratio < 0.0 or self.component_ratio > 1.0:
            raise ConfigException("Component ratio must be a floating point number between 0 and 1")

    def transform_single_date_data(self, data: "xarray.Dataset") -> "xarray.Dataset":
        """
        Apply style to raw data to make an RGBA image xarray (single time slice only)

        :param data: Raw data, all bands.
        :return: RGBA uint8 xarray
        """
        #pylint: disable=too-many-locals
        if self.index_function is not None:
            data['index_function'] = (data.dims, self.index_function(data).data)

        imgdata = Dataset(coords=data)

        d: DataArray = data['index_function']
        for band, intensity in self.rgb_components.items():
            rampdata = DataArray(self.color_ramp.get_value(d, band),
                                 coords=d.coords,
                                 dims=d.dims)
            component_band_data: Optional[DataArray] = None
            for c_band, c_intensity in self.rgb_components[band].items():
                if callable(c_intensity):
                    imgband_component_data = cast(DataArray, c_intensity(data[c_band], c_band, band))
                else:
                    imgband_component_data = cast(DataArray, data[c_band] * cast(DataArray, c_intensity))
                if component_band_data is not None:
                    component_band_data += imgband_component_data
                else:
                    component_band_data = imgband_component_data
                if band != "alpha":
                    component_band_data = self.compress_band(band, component_band_data)
            img_band_data = (rampdata * 255.0 * (1.0 - self.component_ratio)
                             + self.component_ratio * cast(DataArray,
                                                           component_band_data))
            imgdata[band] = (d.dims, img_band_data.astype("uint8").data)

        return imgdata

# Register HybridStyleDef as a priority subclass of StyleDefBase
#    (priority means takes precedence over ComponentStyleDef and ColourRampDef)
StyleDefBase.register_subclass(HybridStyleDef, "component_ratio", priority=True)
