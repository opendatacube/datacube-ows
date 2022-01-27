# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import io
import logging
from datetime import datetime
from typing import Callable, List, MutableMapping, Optional, Union, cast

import numpy
import xarray
from colour import Color
from datacube.utils.masking import make_mask
from matplotlib import patches as mpatches
from matplotlib import pyplot as plt
from xarray import DataArray, Dataset

from datacube_ows.config_utils import (CFG_DICT, AbstractMaskRule,
                                       ConfigException, OWSMetadataConfig)
from datacube_ows.styles.base import StyleDefBase

_LOG = logging.getLogger(__name__)


class AbstractValueMapRule(AbstractMaskRule):
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
        self.style = style_def
        super().__init__(band, cfg, mapper=style_def.local_band)
        cfg = cast(CFG_DICT, self._raw_cfg)

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
        self.parse_color(cfg)

    @property
    def context(self) -> str:
        return f"style {self.style.name} in layer {self.style.product.name} valuemap rule"

    def parse_color(self, cfg: CFG_DICT):
        self.color_str = cast(str, cfg["color"])
        self.rgb = Color(self.color_str)
        if cfg.get("mask"):
            self.alpha = 0.0
        else:
            self.alpha = float(cast(Union[float, int, str], cfg.get("alpha", 1.0)))

    @classmethod
    def value_map_from_config(cls,
                          style_or_mdh: Union["ColorMapStyleDef", "ColorMapStyleDef.MultiDateHandler"],
                          cfg: CFG_DICT
                              ) -> MutableMapping[str, List["AbstractValueMapRule"]]:
        """
        Create a multi-date value map rule set from a config specification

        :param style: The parent style definition object
        :param cfg: The specification for the multi-date value map.

        :return: A value map ruleset dictionary.
        """
        if isinstance(style_or_mdh, ColorMapStyleDef):
            typ = ValueMapRule
        else:
            mdh = cast(ColorMapStyleDef.MultiDateHandler, style_or_mdh)
            if mdh.aggregator:
                style_or_mdh = mdh.style
                typ = ValueMapRule
            else:
                if mdh.min_count != mdh.max_count:
                    raise ConfigException(
                        "MultiDate value map only supported on multi-date handlers with min_count and max_count equal.")
                typ = MultiDateValueMapRule
        vmap: MutableMapping[str, List["AbstractValueMapRule"]] = {}
        for band_name, rules in cfg.items():
            band_rules = [typ(style_or_mdh, band_name, rule) for rule in cast(List[CFG_DICT], rules)]
            vmap[band_name] = band_rules
        return vmap


class ValueMapRule(AbstractValueMapRule):
    """
    A Value Map Rule.

    Construct a ValueMap rule-set with ValueMapRule.value_map_from_config
    """
    def __init__(self, style_cfg: "ColorMapStyleDef", band: str,
                 cfg: CFG_DICT) -> None:
        """
        Construct a Multi-date Value Map Rule

        :param mdh: The owning ColorMapStyleDef object
        :param band: The name of the flag-band the rules apply to
        :param cfg: The rule specification
        """
        super().__init__(style_def=style_cfg, band=band, cfg=cfg)


class MultiDateValueMapRule(AbstractValueMapRule):
    """
    A  Multi-Date Value Map Rule.

    Construct a Multi-Date ValueMap rule-set with MultiDateValueMapRule.value_map_from_config
    """
    def __init__(self, mdh: "ColorMapStyleDef.MultiDateHandler", band: str,
                 cfg: CFG_DICT) -> None:
        """
        Construct a Multi-date Value Map Rule

        :param mdh: The owning ColorMapStyleDef object
        :param band: The name of the flag-band the rules apply to
        :param cfg: The rule specification
        """
        self.mdh = mdh
        self.invert: List[bool] = []
        self.flags: Optional[List[CFG_DICT]] = []
        self.or_flags: Optional[List[bool]] = []
        self.values: Optional[List[List[int]]] = []
        super().__init__(style_def=mdh.style, band=band, cfg=cfg)

    def parse_rule_spec(self, cfg: CFG_DICT):
        if "invert" in cfg:
            self.invert = [bool(b) for b in cfg["invert"]]
        else:
            self.invert = [False] * self.mdh.max_count
        if len(self.invert) != self.mdh.max_count:
            raise ConfigException(f"Invert entry has wrong number of rule sets for date count")
        if "flags" in cfg:
            date_flags = cast(CFG_DICT, cfg["flags"])
            if len(date_flags) != self.mdh.max_count:
                raise ConfigException(f"Flags entry has wrong number of rule sets for date count")
            for flags in date_flags:
                or_flag: bool = False
                if "or" in flags and "and" in flags:
                    raise ConfigException(f"MultiDateValueMap rule in {self.mdh.style.name} of layer {self.mdh.style.product.name} combines 'and' and 'or' rules")
                elif "or" in flags:
                    or_flag = True
                    flags = cast(CFG_DICT, flags["or"])
                elif "and" in flags:
                    flags = cast(CFG_DICT, flags["and"])
                self.flags.append(flags)
                self.or_flags.append(or_flag)
        else:
            self.flags = None
            self.or_flags = None
        if "values" in cfg:
            self.values = cast(List[List[int]], list(cfg["values"]))
        else:
            self.values = None
        if not self.flags and not self.values:
            raise ConfigException(f"Multi-Date Value map rule in {self.context} must have a non-empty 'flags' or 'values' section.")
        if self.flags and self.values:
            raise ConfigException(f"Multi-Date Value map rule in {self.context} has both a 'flags' and a 'values' section - choose one.")

    def create_mask(self, data: DataArray) -> DataArray:
        """
        Create a mask from raw flag band data.

        :param data: Multi-date Raw flag data, assumed to be for this rule's flag band.
        :return: A boolean dateless DataArray, True where the data matches this rule
        """
        date_slices = (data.sel(time=dt) for dt in data.coords["time"].values)
        mask: Optional[DataArray] = None
        if self.values:
            for d_slice, vals, invert in zip(date_slices, self.values, self.invert):
                d_mask: Optional[DataArray] = None
                if len(vals) == 0:
                    d_mask = d_slice == d_slice
                else:
                    for v in cast(List[int], vals):
                        vmask = d_slice == v
                        if d_mask is None:
                            d_mask = vmask
                        else:
                            d_mask |= vmask
                if d_mask is not None and invert:
                    d_mask = ~d_mask # pylint: disable=invalid-unary-operand-type
                if mask is None:
                    mask = d_mask
                else:
                    mask &= d_mask
        else:
            for d_slice, flags, or_flags, invert in zip(date_slices, self.flags, self.or_flags, self.invert):
                d_mask: Optional[DataArray] = None
                if not flags:
                    d_mask = d_slice == d_slice
                elif or_flags:
                    for f in cast(CFG_DICT, flags).items():
                        f = {f[0]: f[1]}
                        if d_mask is None:
                            d_mask = make_mask(d_slice, **f)
                        else:
                            d_mask |= make_mask(d_slice, **f)
                else:
                    d_mask = make_mask(d_slice, **cast(CFG_DICT, flags))
                if invert:
                    d_mask = ~d_mask # pylint: disable=invalid-unary-operand-type
                if mask is None:
                    mask = d_mask
                else:
                    mask &= d_mask
        return mask


def convert_to_uint8(fval):
    scaled = int(fval * 255.0 + 0.5)
    clipped = min(max(scaled, 0), 255)
    return clipped


def apply_value_map(value_map: MutableMapping[str, List[AbstractValueMapRule]],
                    data: Dataset,
                    band_mapper: Callable[[str], str]) -> Dataset:
    imgdata = Dataset(coords={k: v for k, v in data.coords.items() if k != "time"})
    shape = list(imgdata.dims.values())
    for channel in ("red", "green", "blue", "alpha"):
        c = numpy.full(shape, 0, dtype="uint8")
        imgdata[channel] = DataArray(c, coords=imgdata.coords)
    for cfg_band, rules in value_map.items():
        # Run through each item
        band = band_mapper(cfg_band)
        bdata = cast(DataArray, data[band])
        if bdata.dtype.kind == 'f':
            # Convert back to int for bitmasking
            bdata = ColorMapStyleDef.reint(bdata)
        for rule in reversed(rules):
            mask = rule.create_mask(bdata)
            if mask.data.any():
                for channel in ("red", "green", "blue", "alpha"):
                    if channel == "alpha":
                        val = convert_to_uint8(rule.alpha)
                    else:
                        val = convert_to_uint8(getattr(rule.rgb, channel))
                    imgdata[channel] = xarray.where(mask, val, imgdata[channel])
    return imgdata


class PatchTemplate:
    def __init__(self, idx: int, rule: AbstractValueMapRule) -> None:
        self.idx = idx
        self.colour = rule.rgb.hex_l
        self.label = rule.label


class ColorMapLegendBase(StyleDefBase.Legend, OWSMetadataConfig):
    METADATA_ABSTRACT: bool = False
    METADATA_VALUE_RULES: bool = True

    def __init__(self, style_or_mdh: Union["StyleDefBase", "StyleDefBase.Legend"], cfg: CFG_DICT) -> None:
        super().__init__(style_or_mdh, cfg)
        raw_cfg = cast(CFG_DICT, self._raw_cfg)
        self.ncols = int(raw_cfg.get("ncols", 1))
        if self.ncols < 1:
            raise ConfigException("ncols must be a positive integer")
        self.patches: List[PatchTemplate] = []

    def register_value_map(self, value_map: MutableMapping[str, List["AbstractValueMapRule"]]) -> None:
        for band in value_map.keys():
            for idx, rule in reversed(list(enumerate(value_map[band]))):
                # only include values that are not transparent (and that have a non-blank title or abstract)
                if rule.alpha > 0.001 and rule.label:
                    self.patches.append(PatchTemplate(idx, rule))
        self.parse_metadata(self._raw_cfg)

    def render(self, bytesio: io.BytesIO) -> None:
        patches = [
            mpatches.Patch(color=pt.colour, label=self.patch_label(pt.idx))
            for pt in self.patches
        ]
        plt.rcdefaults()
        if self.mpl_rcparams:
            plt.rcParams.update(self.mpl_rcparams)
        plt.figure(figsize=(self.width, self.height))
        plt.axis('off')
        if self.title:
            plt.legend(handles=patches,
                       loc='center',
                       ncol=self.ncols,
                       frameon=False,
                       title=self.title)
        else:
            plt.legend(handles=patches,
                       loc='center',
                       ncol=self.ncols,
                       frameon=False)
        plt.savefig(bytesio, format='png')

    def patch_label(self, idx: int):
        return self.read_local_metadata(f"rule_{idx}")

    # For MetadataConfig
    @property
    def default_title(self) -> Optional[str]:
        return ""



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
        self.value_map = AbstractValueMapRule.value_map_from_config(self, cast(CFG_DICT, style_cfg["value_map"]))
        self.legend_cfg.register_value_map(self.value_map)
        for mdh in self.multi_date_handlers:
            mdh.legend_cfg.register_value_map(mdh.value_map)
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
        return apply_value_map(self.value_map, data, self.product.band_idx.band)

    class Legend(ColorMapLegendBase):
        pass

    class MultiDateHandler(StyleDefBase.MultiDateHandler):
        auto_legend = True
        non_animate_requires_aggregator = False

        def __init__(self, style: "ColorMapStyleDef", cfg: CFG_DICT) -> None:
            """
            First stage initialisation

            :param style: The parent style object
            :param cfg: The multidate handler configuration
            """
            super().__init__(style, cfg)
            self._value_map: Optional[MutableMapping[str, AbstractValueMapRule]] = None
            if self.animate:
                if "value_map" in self._raw_cfg:
                    raise ConfigException("Multidate value maps not supported for animation handlers")
            else:
                self._value_map = AbstractValueMapRule.value_map_from_config(self,
                                                        cast(CFG_DICT, self._raw_cfg["value_map"]))

        @property
        def value_map(self):
            if self._value_map is None:
                self._value_map = self.style.value_map
            return self._value_map

        def transform_data(self, data: "xarray.Dataset") -> "xarray.Dataset":
            """
            Apply image transformation

            :param data: Raw data
            :return: RGBA image xarray.  May have a time dimension
            """
            if self.aggregator is None:
                return apply_value_map(self.value_map, data, self.style.product.band_idx.band)
            else:
                agg = self.aggregator(data)
                return apply_value_map(self.value_map, agg, self.style.product.band_idx.band)

        class Legend(ColorMapLegendBase):
            pass

# Register ColorMapStyleDef as a style subclass.
StyleDefBase.register_subclass(ColorMapStyleDef, "value_map")
