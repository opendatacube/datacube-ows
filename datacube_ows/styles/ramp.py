# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import io
import logging
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from math import isclose
from typing import (Any, Hashable, List, MutableMapping, Optional, Tuple,
                    Union, cast)

import matplotlib
import numpy
from colour import Color
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_hex

try:
    from numpy.typing import NDArray
except ImportError:
    NDArray = numpy.ndarray

from xarray import Dataset

from datacube_ows.config_utils import CFG_DICT, OWSMetadataConfig
from datacube_ows.ogc_utils import ConfigException, FunctionWrapper
from datacube_ows.styles.base import StyleDefBase
from datacube_ows.styles.expression import Expression

_LOG = logging.getLogger(__name__)

RAMP_SPEC = List[CFG_DICT]

UNSCALED_DEFAULT_RAMP = cast(RAMP_SPEC,
                             [
                                {
                                    "value": -1e-24,
                                    "color": "#000080",
                                    "alpha": 0.0
                                },
                                {
                                    "value": 0.0,
                                    "color": "#000080",
                                },
                                {
                                    "value": 0.1,
                                    "color": "#0000FF",
                                },
                                {
                                    "value": 0.3,
                                    "color": "#00FFFF",
                                },
                                {
                                    "value": 0.5,
                                    "color": "#00FF00",
                                },
                                {
                                    "value": 0.7,
                                    "color": "#FFFF00",
                                },
                                {
                                    "value": 0.9,
                                    "color": "#FF0000",
                                },
                                {
                                    "value": 1.0,
                                    "color": "#800000",
                                },
                             ]
)


def scale_unscaled_ramp(rmin: Union[int, float, str], rmax: Union[int, float, str], unscaled: RAMP_SPEC) -> RAMP_SPEC:
    """
    Take a unscaled (normalised) ramp that covers values from 0.0 to 1.0 and scale it linearly to cover the
    provided range.

    :param rmin: The new minimum value for the ramp range.
    :param rmax: The new maximum value for the ramp range.
    :param unscaled: The unscaled (normalised) ramp.
    :return: The scaled ramp.
    """
    if isinstance(rmin, float):
        nmin: float = rmin
    else:
        nmin = float(rmin)
    if isinstance(rmax, float):
        nmax: float = rmax
    else:
        nmax = float(rmax)
    return [
        {
            # pyre-ignore[6]
            "value": (nmax - nmin) * cast(float, u["value"]) + nmin,
            "color": u["color"],
            "alpha": u.get("alpha", 1.0)
        } for u in unscaled
    ]


def crack_ramp(ramp: RAMP_SPEC) -> Tuple[
    List[float],
    List[float], List[float],
    List[float], List[float],
]:
    """
    Split a colour ramp into separate (input) value and (output) RGBA lists.

    :param ramp: input (scaled) colour-ramp definition
    :return: A tuple of four lists of floats: representing values, red, green, blue, alpha.
    """
    values = cast(List[float], [])
    red = cast(List[float], [])
    green = cast(List[float], [])
    blue = cast(List[float], [])
    alpha = cast(List[float], [])
    for r in ramp:
        if isinstance(r["value"], float):
            value: float = cast(float, r["value"])
        else:
            value = float(cast(Union[int, str], r["value"]))
        values.append(value)
        color = Color(r["color"])
        red.append(color.red)
        green.append(color.green)
        blue.append(color.blue)
        alpha.append(float(cast(Union[float, int, str], r.get("alpha", 1.0))))

    return values, red, green, blue, alpha


def read_mpl_ramp(mpl_ramp: str) -> RAMP_SPEC:
    """
    Extract a named colour ramp from Matplotlib as a normalised OWS-compatible ramp specification

    :param mpl_ramp: The name of Matplotlib colour ramp
    :return: A normalised ramp specification.
    """
    unscaled_cmap = cast(RAMP_SPEC, [])
    try:
        cmap = plt.get_cmap(mpl_ramp)
    except:
        raise ConfigException(f"Invalid Matplotlib name: {mpl_ramp}")
    val_range = numpy.arange(0.1, 1.1, 0.1)
    rgba_hex = to_hex(cmap(0.0))
    unscaled_cmap.append(
        {
            "value": 0.0,
            "color": rgba_hex,
            "alpha": 1.0
        }
    )
    for val in val_range:
        rgba_hex = to_hex(cmap(val))
        unscaled_cmap.append(
            {
                "value": float(val),
                "color": rgba_hex
            }
        )
    return unscaled_cmap


class ColorRamp:
    """
    Represents a colour ramp for image and legend rendering purposes
    """
    def __init__(self, style: StyleDefBase,
                       ramp_cfg: CFG_DICT,
                       legend: "RampLegendBase") -> None:
        """
        :param style: The style owning the ramp
        :param ramp_cfg: Style config
        """
        self.style = style
        if "color_ramp" in ramp_cfg:
            raw_scaled_ramp = ramp_cfg["color_ramp"]
        else:
            rmin, rmax = cast(List[float], ramp_cfg["range"])
            unscaled_ramp = UNSCALED_DEFAULT_RAMP
            if "mpl_ramp" in ramp_cfg:
                unscaled_ramp = read_mpl_ramp(cast(str, ramp_cfg["mpl_ramp"]))
            raw_scaled_ramp = scale_unscaled_ramp(rmin, rmax, unscaled_ramp)
        self.ramp = raw_scaled_ramp

        self.values = cast(List[float], [])
        self.components = cast(MutableMapping[str, List[float]], {})
        self.crack_ramp()

        # Handle the mutual interdepencies between the ramp and the legend
        # 1. Let legend read its defaults from this ramp if needed
        legend.register_ramp(self)
        # 2. Extend our colour ramp to support legend if needed
        if self.style.auto_legend:
            fleg_begin = float(legend.begin)
            fleg_end = float(legend.end)
            leg_begin_in_ramp = False
            leg_end_in_ramp = False
            leg_begin_before_idx = None
            leg_end_before_idx = None
            for idx, col_point in enumerate(self.ramp):
                col_val = col_point["value"]
                if not leg_begin_in_ramp and leg_begin_before_idx is None:
                    if isclose(col_val, fleg_begin, abs_tol=1e-9):
                        leg_begin_in_ramp = True
                    elif col_val > fleg_begin:
                        leg_begin_before_idx = idx
                if not leg_end_in_ramp and leg_end_before_idx is None:
                    if isclose(col_val, fleg_end, abs_tol=1e-9):
                        end_in_ramp = True
                    elif col_val > fleg_end:
                        end_before_idx = idx
            if not leg_begin_in_ramp:
                color, alpha = self.color_alpha_at(fleg_begin)
                begin_col_point = {
                    "value": fleg_begin,
                    "color": color.get_hex(),
                    "alpha": alpha
                }
                if leg_begin_before_idx is None:
                    self.ramp.append(begin_col_point)
                else:
                    self.ramp.insert(leg_begin_before_idx, begin_col_point)
                if leg_end_before_idx is not None:
                    leg_end_before_idx += 1
            if not leg_end_in_ramp:
                color, alpha = self.color_alpha_at(fleg_end)
                end_col_point = {
                    "value": fleg_end,
                    "color": color.get_hex(),
                    "alpha": alpha
                }
                if leg_end_before_idx is None:
                    self.ramp.append(end_col_point)
                else:
                    self.ramp.insert(leg_end_before_idx, end_col_point)
            if not leg_end_in_ramp or not leg_begin_in_ramp:
                self.crack_ramp()

    def crack_ramp(self) -> None:
        values, r, g, b, a = crack_ramp(self.ramp)
        self.values = values
        self.components = {
            "red": r,
            "green": g,
            "blue": b,
            "alpha": a
        }

    def get_value(self, data: Union[float, "xarray.DataArray"], band: str) -> NDArray:
        return numpy.interp(data, self.values, self.components[band])

    def get_8bit_value(self, data: "xarray.DataArray", band: str) -> NDArray:
        val: NDArray = self.get_value(data, band)
        val = cast(NDArray, val * 255)
        return val.astype("uint8")

    def apply(self, data: "xarray.DataArray") -> "xarray.Dataset":
        imgdata = cast(MutableMapping[Hashable, Any], {})
        for band in self.components:
            imgdata[band] = (data.dims, self.get_8bit_value(data, band))
        imgdataset = Dataset(imgdata, coords=data.coords)
        return imgdataset

    def color_alpha_at(self, val: float) -> Tuple[Color, float]:
        color = Color(
            rgb=(
                self.get_value(val, "red").item(),
                self.get_value(val, "green").item(),
                self.get_value(val, "blue").item(),
            )
        )
        alpha = cast(float, self.get_value(val, "alpha"))
        return color, alpha


class RampLegendBase(StyleDefBase.Legend, OWSMetadataConfig):
    METADATA_ABSTRACT: bool = False
    METADATA_LEGEND_UNITS: bool = True
    METADATA_TICK_LABELS: bool = True

    def __init__(self, style_or_mdh: Union["StyleDefBase", "StyleDefBase.Legend"], cfg: CFG_DICT) -> None:
        super().__init__(style_or_mdh, cfg)
        raw_cfg = cast(CFG_DICT, self._raw_cfg)
        # Range - defaults deferred until we have parsed the associated ramp
        if "begin" not in raw_cfg:
            self.begin = Decimal("nan")
        else:
            self.begin = Decimal(cast(Union[str, float, int], raw_cfg["begin"]))
        if "end" not in raw_cfg:
            self.end = Decimal("nan")
        else:
            self.end = Decimal(cast(Union[str, float, int], raw_cfg["end"]))

        # decimal_places, rounder
        def rounder_str(prec: int) -> str:
            rstr = "1"
            if prec == 0:
                return rstr
            rstr += "."
            for i in range(prec - 1):
                rstr += "0"
            rstr += "1"
            return rstr

        self.decimal_places = raw_cfg.get("decimal_places", 1)
        if self.decimal_places < 0:
            raise ConfigException("decimal_places cannot be negative")
        self.rounder = Decimal(rounder_str(self.decimal_places))

        # Ticks - Non-explicit tick values deferred until we have parsed the associated ramp
        ticks_handled = False
        self.ticks_every: Optional[Decimal] = None
        self.tick_count: Optional[int] = None
        self.ticks: List[Decimal] = []
        if "ticks_every" in raw_cfg:
            if "tick_count" in raw_cfg:
                raise ConfigException("Cannot use tick count and ticks_every in the same legend")
            if "ticks" in raw_cfg:
                raise ConfigException("Cannot use ticks and ticks_every in the same legend")
            self.ticks_every = Decimal(cast(Union[int, float, str], raw_cfg["ticks_every"]))
            if self.ticks_every.is_zero() or self.ticks_every.is_signed():
                raise ConfigException("ticks_every must be greater than zero")
            ticks_handled = True
        if "ticks" in raw_cfg:
            if "tick_count" in raw_cfg:
                raise ConfigException("Cannot use tick count and ticks in the same legend")
            self.ticks = [Decimal(t) for t in cast(List[Union[str, int, float]], raw_cfg["ticks"])]
            ticks_handled = True
        if not ticks_handled:
            self.tick_count = int(cast(Union[str, int], raw_cfg.get("tick_count", 1)))
            if self.tick_count < 0:
                raise ConfigException("tick_count cannot be negative")
        # prepare for tick labels
        self.cfg_labels = cast(MutableMapping[str, MutableMapping[str, str]], raw_cfg.get("tick_labels", {}))
        defaults = self.cfg_labels.get("default", {})
        self.lbl_default_prefix = defaults.get("prefix", "")
        self.lbl_default_suffix = defaults.get("suffix", "")
        self.tick_labels: List[str] = []
        # handle matplotlib args
        self.strip_location = cast(List[float],
                                   raw_cfg.get("strip_location", [0.05, 0.5, 0.9, 0.15]))
        # throw error on legacy syntax
        self.fail_legacy()

    def fail_legacy(self) -> None:
        if any(
                legent in self._raw_cfg
                for legent in ["major_ticks", "offset", "scale_by", "radix_point"]
        ):
            raise ConfigException(
                f"Style {self.style.name} uses a no-longer supported format for legend configuration.  " +
                "Please refer to the documentation and update your config")

    def register_ramp(self, ramp: ColorRamp) -> None:
        if self.begin.is_nan():
            for col_def in ramp.ramp:
                if isclose(col_def.get("alpha", 1.0), 1.0, abs_tol=1e-9):
                    self.begin = Decimal(col_def["value"])
                    break
            if self.begin.is_nan():
                self.begin = Decimal(ramp.ramp[0]["value"])
        if self.end.is_nan():
            for col_def in reversed(ramp.ramp):
                if isclose(col_def.get("alpha", 1.0), 1.0, abs_tol=1e-9):
                    self.end = Decimal(col_def["value"])
                    break
            if self.end.is_nan():
                self.end = Decimal(ramp.ramp[-1]["value"])
        for t in self.ticks:
            if t < self.begin or t > self.end:
                raise ConfigException("Explicit ticks must all be within legend begin/end range")
        if self.ticks_every is not None:
            tickval = self.begin
            while tickval < self.end:
                self.ticks.append(tickval)
                tickval += self.ticks_every
            self.ticks.append(self.end)
        elif self.tick_count is not None:
            if self.tick_count == 0:
                self.ticks.append(self.begin)
            else:
                delta = self.end - self.begin
                dcount = Decimal(self.tick_count)
                for i in range(0, self.tick_count + 1):
                    tickval = self.begin + (Decimal(i) / dcount) * delta
                    self.ticks.append(tickval.quantize(self.rounder, rounding=ROUND_HALF_UP))

        # handle tick labels
        for tick in self.ticks:
            label_cfg = self.cfg_labels.get(str(tick))
            if label_cfg:
                prefix = label_cfg.get("prefix", self.lbl_default_prefix)
                suffix = label_cfg.get("suffix", self.lbl_default_suffix)
                label = label_cfg.get("label", str(tick))
                self.tick_labels.append(prefix + label + suffix)
            else:
                self.tick_labels.append(
                    self.lbl_default_prefix + str(tick) + self.lbl_default_suffix
                )
        self.parse_metadata(self._raw_cfg)

        # Check for legacy legend tips in ramp:
        for r in ramp.ramp:
            if "legend" in r:
                raise ConfigException(
                    f"Style {self.style.name} uses a no-longer supported format for legend configuration.  " +
                    "Please refer to the documentation and update your config")

    def tick_label(self, tick):
        try:
            tick_idx = self.ticks.index(tick)
            metaval = self.read_local_metadata(f"lbl_{tick}")
            if metaval:
                return metaval
            else:
                return self.tick_labels[tick_idx]
        except ValueError:
            _LOG.error("'%s' is a not a valid tick", tick)
            return None

    def create_cdict_ticks(self) -> Tuple[
        MutableMapping[str, List[Tuple[float, float, float]]],
        MutableMapping[float, str],
    ]:
        normalize_factor = float(self.end) - float(self.begin)
        cdict = cast(MutableMapping[str, List[Tuple[float, float, float]]], dict())
        bands = cast(MutableMapping[str, List[Tuple[float, float, float]]], defaultdict(list))
        started = False
        finished = False
        for index, ramp_point in enumerate(self.style_or_mdh.color_ramp.ramp):
            if finished:
                break

            value = cast(Union[float, int], ramp_point.get("value"))
            normalized = (value - float(self.begin)) / float(normalize_factor)

            if not started:
                if isclose(value, float(self.begin), abs_tol=1e-9):
                    started = True
                else:
                    continue
            if not finished:
                if isclose(value, float(self.end), abs_tol=1e-9):
                    finished = True

            for band, intensity in self.style_or_mdh.color_ramp.components.items():
                bands[band].append((normalized, intensity[index], intensity[index]))

        for band, blist in bands.items():
            cdict[band] = blist

        ticks = cast(MutableMapping[float, str], dict())
        for tick in self.ticks:
            value = float(tick)
            normalized = (value - float(self.begin)) / float(normalize_factor)
            ticks[normalized] = self.tick_label(tick)

        return cdict, ticks

    def display_title(self):
        if self.units:
            return f"{self.title}({self.units})"
        else:
            return self.title

    def plot_name(self):
        return f"{self.style.product.name}_{self.style.name}"

    def render(self, bytesio: io.BytesIO) -> None:
        cdict, ticks = self.create_cdict_ticks()
        plt.rcdefaults()
        if self.mpl_rcparams:
            plt.rcParams.update(self.mpl_rcparams)
        fig = plt.figure(figsize=(self.width, self.height))
        ax = fig.add_axes(self.strip_location)
        custom_map = LinearSegmentedColormap(self.plot_name(), cdict)
        color_bar = matplotlib.colorbar.ColorbarBase(
            ax,
            cmap=custom_map,
            orientation="horizontal")
        color_bar.set_ticks(list(ticks.keys()))
        color_bar.set_ticklabels(list(ticks.values()))
        color_bar.set_label(self.display_title())
        plt.savefig(bytesio, format='png')

    # For MetadataConfig
    @property
    def default_title(self) -> Optional[str]:
        return self.style.title



class ColorRampDef(StyleDefBase):
    """
    Colour ramp Style subclass
    """
    auto_legend = True

    def __init__(self,
                 product: "datacube_ows.ows_configuration.OWSNamedLayer",
                 style_cfg: CFG_DICT,
                 stand_alone: bool = False,
                 defer_multi_date: bool = False,
                 user_defined: bool = False) -> None:
        """"
        Constructor - refer to StyleDefBase
        """
        super(ColorRampDef, self).__init__(product, style_cfg,
                           stand_alone=stand_alone, defer_multi_date=True, user_defined=user_defined)
        style_cfg = cast(CFG_DICT, self._raw_cfg)
        self.color_ramp = ColorRamp(self, style_cfg, self.legend_cfg)
        self.include_in_feature_info = bool(style_cfg.get("include_in_feature_info", True))

        if "index_function" in style_cfg:
            self.index_function = FunctionWrapper(self,
                                                  cast(CFG_DICT, style_cfg["index_function"]),
                                                  stand_alone=self.stand_alone)
            if not self.stand_alone:
                for band in cast(List[str], style_cfg["needed_bands"]):
                    self.raw_needed_bands.add(band)
        elif "index_expression" in style_cfg:
            self.index_function = Expression(self, cast(str, style_cfg["index_expression"]))
            for band in self.index_function.needed_bands:
                self.raw_needed_bands.add(band)
            if self.stand_alone:
                self.needed_bands = [self.local_band(b) for b in self.raw_needed_bands]
                self.flag_bands = []
        else:
            raise ConfigException("Index function is required for index and hybrid styles. Style %s in layer %s" % (
                self.name,
                self.product.name
            ))
        if not defer_multi_date:
            self.parse_multi_date(style_cfg)

    def apply_index(self, data: "xarray.Dataset") -> "xarray.DataArray":
        """
        Caclulate index value across data.

        :param data: Input dataset
        :return: Matching dataarray carrying the index value
        """
        index_data = self.index_function(data)
        data['index_function'] = (index_data.dims, index_data.data)
        return data["index_function"]

    def transform_single_date_data(self, data: "xarray.Dataset") -> "xarray.Dataset":
        """
        Apply style to raw data to make an RGBA image xarray (single time slice only)

        :param data: Raw data, all bands.
        :return: RGBA uint8 xarray
        """
        d = self.apply_index(data)
        return self.color_ramp.apply(d)

    class Legend(RampLegendBase):
        pass

    class MultiDateHandler(StyleDefBase.MultiDateHandler):
        auto_legend = True

        def __init__(self, style: "ColorRampDef", cfg: CFG_DICT) -> None:
            """
            First stage initialisation

            :param style: The parent style object
            :param cfg: The multidate handler configuration
            """
            super().__init__(style, cfg)
            if self.animate:
                self.feature_info_label: Optional[str] = None
                self.color_ramp = style.color_ramp
            else:
                self.feature_info_label = cast(Optional[str], cfg.get("feature_info_label", None))
                self.color_ramp = ColorRamp(style, cfg, self.legend_cfg)

        def transform_data(self, data: "xarray.Dataset") -> "xarray.Dataset":
            """
            Apply image transformation

            :param data: Raw data
            :return: RGBA image xarray.  May have a time dimension
            """
            xformed_data = cast("ColorRampDef", self.style).apply_index(data)
            agg = self.aggregator(xformed_data)
            return self.color_ramp.apply(agg)

        class Legend(RampLegendBase):
            def plot_name(self):
                return f"{self.style.product.name}_{self.style.name}_{self.style_or_mdh.min_count}"

# Register ColorRampDef as Style subclass.
StyleDefBase.register_subclass(ColorRampDef, ("range", "color_ramp"))
