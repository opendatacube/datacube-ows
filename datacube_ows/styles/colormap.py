# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import io
import logging
from datetime import datetime
from typing import List, MutableMapping, Optional, Union, cast

import numpy
from colour import Color
from datacube.utils.masking import make_mask
from matplotlib import patches as mpatches
from matplotlib import pyplot as plt
from xarray import DataArray, Dataset, merge

from datacube_ows.config_utils import CFG_DICT, ConfigException, OWSConfigEntry
from datacube_ows.styles.base import StyleDefBase

_LOG = logging.getLogger(__name__)


class ValueMapRule(OWSConfigEntry):
    """
    A Value Map Rule.

    Construct a ValueMap rule-set with ValueMapRule.value_map_from_config
    """
    def __init__(self, style_def: "ColorMapStyleDef", band: str, cfg: CFG_DICT) -> None:
        """
        Construct a Value Map Rule

        :param style_def: The owning ColorMapStyleDef object
        :param band: The name of the flag-band the rules apply to
        :param cfg: The rule specification
        """
        super().__init__(cfg)
        cfg = cast(CFG_DICT, self._raw_cfg)
        self.style = style_def
        self.band = style_def.local_band(band)

        self.title = cast(str, cfg["title"])
        self.abstract = cast(str, cfg.get("abstract"))
        if self.title and self.abstract:
            self.label: Optional[str] = f"{self.title} - {self.abstract}"
        elif self.title:
            self.label = self.title
        elif self.abstract:
            self.label = self.abstract
        else:
            self.label = None
        self.color_str = cast(str, cfg["color"])
        self.rgb = Color(self.color_str)
        if cfg.get("mask", False):
            self.alpha: float = 0.0
        else:
            self.alpha = float(cast(Union[float, int, str], cfg.get("alpha", 1.0)))

        if "flags" in cfg:
            flags = cast(CFG_DICT, cfg["flags"])
            self.or_flags: bool = False
            if "or" in flags and "and" in flags:
                raise ConfigException(f"ValueMap rule in style {self.style.name} of layer {self.style.product.name} combines 'and' and 'or' rules")
            elif "or" in flags:
                self.or_flags = True
                flags = cast(CFG_DICT, flags["or"])
            elif "and" in flags:
                flags = cast(CFG_DICT, flags["and"])
            self.flags: Optional[CFG_DICT] = flags
        else:
            self.flags = None
            self.or_flags = False
        if "values" in cfg:
            self.values: Optional[List[int]] = cast(List[int], cfg["values"])
        else:
            self.values = None
        if not self.flags and not self.values:
            raise ConfigException(f"Value map rule in style {style_def.name} of layer {style_def.product.name} must have a non-empty 'flags' or 'values' section.")
        if self.flags and self.values:
            raise ConfigException(f"Value map rule in style {style_def.name} of layer {style_def.product.name} has both a 'flags' and a 'values' section - choose one.")

    def create_mask(self, data: DataArray) -> DataArray:
        """
        Create a mask from raw flag band data.

        :param data: Raw flag data, assumed to be for this rule's flag band.
        :return: A boolean DataArray, True where the data matches this rule
        """
        if self.values:
            mask: Optional[DataArray] = None
            for v in cast(List[int], self.values):
                vmask = data == v
                if mask is None:
                    mask = vmask
                else:
                    mask |= vmask
        elif self.or_flags:
            mask = None
            for f in cast(CFG_DICT, self.flags).items():
                f = {f[0]: f[1]}
                if mask is None:
                    mask = make_mask(data, **f)
                else:
                    mask |= make_mask(data, **f)
        else:
            mask = make_mask(data, **cast(CFG_DICT, self.flags))
        return mask

    @classmethod
    def value_map_from_config(cls,
                              style: "ColorMapStyleDef",
                              cfg: CFG_DICT) -> MutableMapping[str, List["ValueMapRule"]]:
        """
        Create a value map rule set from a config specification

        :param style: The parent style definition object
        :param cfg: The specification for the value map.

        :return: A value map ruleset dictionary.
        """
        vmap: MutableMapping[str, List["ValueMapRule"]] = {}
        for band_name, rules in cfg.items():
            band_rules = [cls(style, band_name, rule) for rule in cast(List[CFG_DICT], rules)]
            vmap[band_name] = band_rules
        return vmap


class ColorMapStyleDef(StyleDefBase):
    """
    Style subclass for value-map styles
    """
    auto_legend = True

    def __init__(self,
                 product: "datacube_ows.ows_configuration.OWSNamedLayer",
                 style_cfg: CFG_DICT,
                 stand_alone: bool = False,
                 user_defined: bool = False) -> None:
        """"
        Constructor - refer to StyleDefBase
        """
        super().__init__(product, style_cfg, stand_alone=stand_alone, user_defined=user_defined)
        style_cfg = cast(CFG_DICT, self._raw_cfg)
        self.value_map = ValueMapRule.value_map_from_config(self, cast(CFG_DICT, style_cfg["value_map"]))
        for band in self.value_map.keys():
            self.raw_needed_bands.add(band)

    @staticmethod
    def reint(data: DataArray) -> DataArray:
        """
        Convert a data-array to int.

        :param data: input data (potentially non-integer)
        :return: same data cast to integer
        """
        inted = data.astype("int")
        if hasattr(data, "attrs"):
            attrs = data.attrs
            inted.attrs = attrs
        return inted

    @staticmethod
    def create_colordata(data: DataArray, rgb: Color, alpha: float, mask: DataArray) -> Dataset:
        """Colour a mask with a given colour/alpha"""
        target = Dataset(coords=data.coords)
        colors = ["red", "green", "blue", "alpha"]
        for color in colors:
            val = alpha if color == "alpha" else getattr(rgb, color)
            c = numpy.full(data.shape, val)
            target[color] = DataArray(c, dims=data.dims, coords=data.coords)
        # pyre-ignore[6]
        masked = target.where(mask).where(numpy.isfinite(data))  # remask
        return masked

    def transform_single_date_data(self, data: Dataset) -> Dataset:
        """
        Apply style to raw data to make an RGBA image xarray (single time slice only)

        :param data: Raw data, all bands.
        :return: RGBA uint8 xarray
        """
        # pylint: disable=too-many-locals, too-many-branches
        # extent mask data per band to preseve nodata
        _LOG.debug("transform begin %s", datetime.now())
        # if extent_mask is not None:
        #    for band in data.data_vars:
        # try:
        #            data[band] = data[band].where(extent_mask, other=data[band].attrs['nodata'])
        #        except AttributeError:
        #            data[band] = data[band].where(extent_mask)

        imgdata = Dataset(coords=data.coords)
        for cfg_band, rules in self.value_map.items():
            # Run through each item
            band = self.product.band_idx.band(cfg_band)
            bdata = cast(DataArray, data[band])
            band_data = Dataset()
            if bdata.dtype.kind == 'f':
                # Convert back to int for bitmasking
                bdata = ColorMapStyleDef.reint(bdata)
            for rule in rules:
                mask = rule.create_mask(bdata)

                masked = ColorMapStyleDef.create_colordata(bdata, rule.rgb, rule.alpha, mask)
                band_data = masked if len(band_data.data_vars) == 0 else band_data.combine_first(masked)

            imgdata = band_data if len(imgdata.data_vars) == 0 else merge([imgdata, band_data])

        imgdata *= 255
        return imgdata.astype('uint8')

    def single_date_legend(self, bytesio: io.BytesIO) -> None:
        """
        Write a legend into a bytes buffer as a PNG image.

        :param bytesio:  io.BytesIO byte buffer.
        """
        patches = []
        for band in self.value_map.keys():
            for rule in reversed(self.value_map[band]):
                # only include values that are not transparent (and that have a non-blank title or abstract)
                if rule.alpha > 0.001 and rule.label:
                    try:
                        patch = mpatches.Patch(color=rule.rgb.hex_l, label=rule.label)
                    # pylint: disable=broad-except
                    except Exception as e:
                        print("Error creating patch?", e)
                    patches.append(patch)
        cfg = self.legend_cfg
        plt.rcdefaults()
        if cfg.get("rcParams", None) is not None:
            plt.rcParams.update(cfg.get("rcParams"))
        figure = plt.figure(figsize=(cfg.get("width", 3),
                                     cfg.get("height", 1.25)))
        plt.axis('off')
        legend = plt.legend(handles=patches, loc='center', frameon=False)
        plt.savefig(bytesio, format='png')


# Register ColorMapStyleDef as a style subclass.
StyleDefBase.register_subclass(ColorMapStyleDef, "value_map")
