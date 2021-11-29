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

from datacube_ows.config_utils import CFG_DICT
from datacube_ows.ogc_utils import ConfigException, FunctionWrapper
from datacube_ows.styles.base import StyleDefBase
from datacube_ows.styles.expression import Expression

_LOG = logging.getLogger(__name__)
matplotlib.use('Agg')

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


def colour_ramp_legend(bytesio: io.BytesIO,
                       legend_cfg: CFG_DICT,
                       colour_ramp: "ColorRamp",
                       map_name: str,
                       default_title: str) -> None:
    """
    Generate a matplotlib legend for a colour ramp

    :param bytesio: A BytesIO object to write the legend image into
    :param legend_cfg: Legend configuration
    :param colour_ramp: A ColorRamp object
    :param map_name: a name for the transient MPL colourmap object
    :param default_title: The default title to use (used if no title is set in legend_cfg)
    """
    def create_cdict_ticks(cfg: CFG_DICT, ramp: "ColorRamp") -> Tuple[
        MutableMapping[str, List[Tuple[float, float, float]]],
        MutableMapping[float, str],
    ]:
        normalize_factor = float(ramp.legend_end) - float(ramp.legend_begin)

        cdict = cast(MutableMapping[str, List[Tuple[float, float, float]]], dict())
        bands = cast(MutableMapping[str, List[Tuple[float, float, float]]], defaultdict(list))
        started = False
        finished = False
        for index, ramp_point in enumerate(ramp.ramp):
            if finished:
                continue

            value = cast(Union[float, int], ramp_point.get("value"))
            normalized = (value - float(ramp.legend_begin)) / float(normalize_factor)

            if not started:
                if isclose(value, float(ramp.legend_begin), abs_tol=1e-9):
                    started = True
                else:
                    continue
            if not finished:
                if isclose(value, float(ramp.legend_end), abs_tol=1e-9):
                    finished = True

            for band, intensity in ramp.components.items():
                bands[band].append((normalized, intensity[index], intensity[index]))

        for band, blist in bands.items():
            cdict[band] = blist

        ticks = cast(MutableMapping[float, str], dict())
        for tick, tick_lbl in zip(ramp.ticks, ramp.tick_labels):
            value = float(tick)
            normalized = (value - float(ramp.legend_begin)) / float(normalize_factor)
            ticks[normalized] = tick_lbl   # REVISIT: map on float???

        return cdict, ticks

    cdict, ticks = create_cdict_ticks(legend_cfg, colour_ramp)

    plt.rcdefaults()
    if colour_ramp.legend_mpl_rcparams:
        plt.rcParams.update(colour_ramp.legend_mpl_rcparams)
    fig = plt.figure(figsize=(colour_ramp.legend_width, colour_ramp.legend_height))
    ax = fig.add_axes(colour_ramp.legend_strip_location)
    custom_map = LinearSegmentedColormap(map_name, cdict)
    color_bar = matplotlib.colorbar.ColorbarBase(
        ax,
        cmap=custom_map,
        orientation="horizontal")

    color_bar.set_ticks(list(ticks.keys()))
    color_bar.set_ticklabels(list(ticks.values()))

    title = colour_ramp.legend_title if colour_ramp.legend_title else default_title
    if colour_ramp.legend_units:
        title = title + "(" + colour_ramp.legend_units + ")"

    color_bar.set_label(title)

    plt.savefig(bytesio, format='png')


class ColorRamp:
    """
    Represents a colour ramp for image and legend rendering purposes
    """
    def __init__(self, style: StyleDefBase, ramp_cfg: CFG_DICT) -> None:
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
        legend_cfg = cast(CFG_DICT, ramp_cfg.get("legend", {}))

        # Legend typing
        self.legend_begin = Decimal("nan")
        self.legend_end = Decimal("nan")
        self.ticks = cast(List[Decimal], [])
        self.tick_labels = cast(List[str], [])
        self.legend_mpl_rcparams = cast(MutableMapping[str, str], {})
        self.legend_width = 0.0
        self.legend_height = 0.0
        self.legend_strip_location = cast(List[float], [])
        self.legend_title = ""
        self.legend_units = ""
        self.legend_decimal_places = Decimal("nan")
        self.rounder = Decimal("nan")
        if legend_cfg.get("show_legend", True) and not legend_cfg.get("url"):
            self.parse_legend(legend_cfg)
        else:
            self.auto_legend = False

        self.values = cast(List[float], [])
        self.components = cast(MutableMapping[str, List[float]], {})
        self.crack_ramp()

        if self.auto_legend:
            fbegin = float(self.legend_begin)
            fend = float(self.legend_end)
            begin_in_ramp = False
            end_in_ramp = False
            begin_before_idx = None
            end_before_idx = None
            for idx, col_point in enumerate(self.ramp):
                col_val = col_point["value"]
                if not begin_in_ramp and begin_before_idx is None:
                    if isclose(col_val, fbegin, abs_tol=1e-9):
                        begin_in_ramp = True
                    elif col_val > fbegin:
                        begin_before_idx = idx
                if not end_in_ramp and end_before_idx is None:
                    if isclose(col_val, fend, abs_tol=1e-9):
                        end_in_ramp = True
                    elif col_val > fend:
                        end_before_idx = idx
            if not begin_in_ramp:
                color, alpha = self.color_alpha_at(fbegin)
                begin_col_point = {
                    "value": fbegin,
                    "color": color.get_hex(),
                    "alpha": alpha
                }
                if begin_before_idx is None:
                    self.ramp.append(begin_col_point)
                else:
                    self.ramp.insert(begin_before_idx, begin_col_point)
                if end_before_idx is not None:
                    end_before_idx += 1
            if not end_in_ramp:
                color, alpha = self.color_alpha_at(fend)
                end_col_point = {
                    "value": fend,
                    "color": color.get_hex(),
                    "alpha": alpha
                }
                if end_before_idx is None:
                    self.ramp.append(end_col_point)
                else:
                    self.ramp.insert(end_before_idx, end_col_point)
            if not end_in_ramp or not begin_in_ramp:
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

    def parse_legend(self, cfg: CFG_DICT) -> None:
        def rounder_str(prec: int) -> str:
            rstr = "1"
            if prec == 0:
                return rstr
            rstr += "."
            for i in range(prec - 1):
                rstr += "0"
            rstr += "1"
            return rstr

        self.auto_legend = True
        self.legend_title = cfg.get("title")
        self.legend_units = cfg.get("units", "")
        self.legend_decimal_places = cfg.get("decimal_places", 1)
        if self.legend_decimal_places < 0:
            raise ConfigException("decimal_places cannot be negative")
        self.rounder = Decimal(rounder_str(self.legend_decimal_places))
        self.parse_legend_range(cfg)
        self.parse_legend_ticks(cfg)
        self.parse_legend_tick_labels(cfg)
        self.parse_legend_matplotlib_args(cfg)
        # Check for old style config - was deprecated, now not supported
        legend_legacy = any(
            legent in cfg
            for legent in ["major_ticks", "offset", "scale_by", "radix_point"]
        )
        if not legend_legacy and all(
            legent not in cfg
            for legent in ["begin", "end", "decimal_places", "ticks_every", "tick_count", "tick_labels", "ticks"]
        ):
            # No legacy entries, but no new entries either.
            # Check ramp for legend tips
            for r in self.ramp:
                if "legend" in r:
                    legend_legacy = True
                    break
        if legend_legacy:
            raise ConfigException(
                        "Style %s uses a no-longer supported format for legend configuration.  " +
                        "Please refer to the documentation and update your config" % self.style.name)

    def parse_legend_range(self, cfg: CFG_DICT) -> None:
        if "begin" in cfg:
            self.legend_begin = Decimal(cast(Union[str, float, int], cfg["begin"]))
        else:
            for col_def in self.ramp:
                if isclose(col_def.get("alpha", 1.0), 1.0, abs_tol=1e-9):
                    self.legend_begin = Decimal(col_def["value"])
                    break
            if self.legend_begin.is_nan():
                self.legend_begin = Decimal(self.ramp[0]["value"])
        if "end" in cfg:
            self.legend_end = Decimal(cast(Union[str, float, int], cfg["end"]))
        else:
            for col_def in reversed(self.ramp):
                if col_def.get("alpha", 1.0) == 1.0:
                    self.legend_end = Decimal(col_def["value"])
                    break
            if self.legend_end.is_nan():
                self.legend_end = Decimal(self.ramp[-1]["value"])

    def parse_legend_ticks(self, cfg: CFG_DICT) -> None:
        # Ticks
        ticks_handled = False
        if "ticks_every" in cfg:
            if "tick_count" in cfg:
                raise ConfigException("Cannot use tick count and ticks_every in the same legend")
            if "ticks" in cfg:
                raise ConfigException("Cannot use ticks and ticks_every in the same legend")
            delta = Decimal(cast(Union[int, float, str], cfg["ticks_every"]))
            tickval = self.legend_begin
            while tickval < self.legend_end:
                self.ticks.append(tickval)
                tickval += delta
            self.ticks.append(tickval)
            ticks_handled = True
        if "ticks" in cfg:
            if "tick_count" in cfg:
                raise ConfigException("Cannot use tick count and ticks in the same legend")
            self.ticks = [Decimal(t) for t in cast(List[Union[str, int, float]], cfg["ticks"])]
            ticks_handled = True
        if not ticks_handled:
            count = int(cast(Union[str, int], cfg.get("tick_count", 1)))
            if count < 0:
                raise ConfigException("tick_count cannot be negative")
            elif count == 0:
                self.ticks.append(self.legend_begin)
            else:
                delta = self.legend_end - self.legend_begin
                dcount = Decimal(count)

                for i in range(0, count + 1):
                    tickval = self.legend_begin + (Decimal(i) / dcount) * delta
                    self.ticks.append(tickval.quantize(self.rounder, rounding=ROUND_HALF_UP))

    def parse_legend_tick_labels(self, cfg: CFG_DICT) -> None:
        labels = cast(MutableMapping[str, MutableMapping[str, str]], cfg.get("tick_labels", {}))
        defaults = labels.get("default", {})
        default_prefix = defaults.get("prefix", "")
        default_suffix = defaults.get("suffix", "")
        # pylint: disable=attribute-defined-outside-init
        for tick in self.ticks:
            label_cfg = labels.get(str(tick))
            if label_cfg:
                prefix = label_cfg.get("prefix", default_prefix)
                suffix = label_cfg.get("suffix", default_suffix)
                label  = label_cfg.get("label", str(tick))
                self.tick_labels.append(prefix + label + suffix)
            else:
                self.tick_labels.append(
                    default_prefix + str(tick) + default_suffix
                )

    def parse_legend_matplotlib_args(self, cfg: CFG_DICT) -> None:
        self.legend_mpl_rcparams = cast(MutableMapping[str, str], cfg.get("rcParams", {}))
        self.legend_width = cast(float, cfg.get("width", 4.0))
        self.legend_height = cast(float, cfg.get("height", 1.25))
        self.legend_strip_location = cast(List[float],
                                          cfg.get("strip_location", [0.05, 0.5, 0.9, 0.15]))

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
        self.color_ramp = ColorRamp(self, style_cfg)
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

    def single_date_legend(self, bytesio: io.BytesIO) -> None:
        """
        Write a legend into a bytes buffer as a PNG image.

        :param bytesio:  io.BytesIO byte buffer.
        """
        colour_ramp_legend(bytesio,
                           self.legend_cfg,
                           self.color_ramp,
                           self.product.name,
                           self.title      # pyre-ignore[16]
                           )

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
                self.color_ramp = ColorRamp(style, cfg)

        def transform_data(self, data: "xarray.Dataset") -> "xarray.Dataset":
            """
            Apply image transformation

            :param data: Raw data
            :return: RGBA image xarray.  May have a time dimension
            """
            xformed_data = cast("ColorRampDef", self.style).apply_index(data)
            agg = self.aggregator(xformed_data)
            return self.color_ramp.apply(agg)

        def legend(self, bytesio: io.BytesIO) -> None:
            """
            Write a legend as a png to a bytesio buffer.

            :param bytesio:
            """
            if self.animate and not self.legend_cfg:
                self.style.single_date_legend(bytesio)
            else:
                title = self.legend_cfg.get("title", self.range_str() + " Dates")
                name = self.style.product.name + f"_{self.min_count}"
                colour_ramp_legend(bytesio,
                                   self.legend_cfg,
                                   self.color_ramp,
                                   name,
                                   title
                                   )

# Register ColorRampDef as Style subclass.
StyleDefBase.register_subclass(ColorRampDef, ("range", "color_ramp"))
