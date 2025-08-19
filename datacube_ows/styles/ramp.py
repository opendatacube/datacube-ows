# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import io
import logging
from collections import defaultdict
from collections.abc import Hashable, Iterable, MutableMapping
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from math import isclose
from typing import Any, Union, cast

import matplotlib
import numpy
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_hex, to_rgba
from numpy import ubyte
from typing_extensions import override
from xarray import DataArray, Dataset

from datacube_ows.config_utils import (
    CFG_DICT,
    ConfigException,
    FunctionWrapper,
    OWSMetadataConfig,
)
from datacube_ows.styles.base import StyleDefBase
from datacube_ows.styles.expression import Expression

TYPE_CHECKING = False
if TYPE_CHECKING:
    from datacube_ows.ows_configuration import OWSNamedLayer

_LOG: logging.Logger = logging.getLogger(__name__)


@dataclass
class RampNode:
    value: int | float
    color: str
    alpha: int | float | None = None

    @property
    def rgba(self) -> tuple[float, float, float, float]:
        return to_rgba(self.color, self.alpha)

    def with_value(self, value: int | float) -> "RampNode":
        return RampNode(value, self.color, self.alpha)


RAMP_SPEC = list[CFG_DICT]
RampRepr = list[RampNode]


def make_ramp_representation(ramp_spec: RAMP_SPEC, style_name: str) -> RampRepr:
    rep: RampRepr = []
    for node in ramp_spec:
        if "value" not in node:
            raise ConfigException(
                f"Color ramp element without a value in style {style_name}"
            )
        if "color" not in node:
            raise ConfigException(
                f"Color ramp element without a color in style {style_name}"
            )
        if "legend" in node:
            raise ConfigException(
                f"Style {style_name} uses a no-longer supported format for legend configuration.  "
                + "Please refer to the documentation and update your config"
            )
        rep.append(
            RampNode(
                float(cast(float | str | int, node["value"])),
                cast(str, node["color"]),
                alpha=None
                if node.get("alpha") is None
                else float(cast(str | int | float, node["alpha"])),
            )
        )
    return rep


UNSCALED_DEFAULT_RAMP = [
    RampNode(-1e-24, "#000080", alpha=0.0),
    RampNode(0.0, "#000080"),
    RampNode(0.1, "#0000FF"),
    RampNode(0.3, "#00FFFF"),
    RampNode(0.5, "#00FF00"),
    RampNode(0.7, "#FFFF00"),
    RampNode(0.9, "#FF0000"),
    RampNode(1.0, "#800000"),
]


def scale_unscaled_ramp(
    rmin: int | float | str, rmax: int | float | str, unscaled: RampRepr
) -> RampRepr:
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
    return [u.with_value((nmax - nmin) * float(u.value) + nmin) for u in unscaled]


def crack_ramp(
    ramp: RampRepr,
) -> tuple[list[float], list[float], list[float], list[float], list[float]]:
    """
    Split a colour ramp into separate (input) value and (output) RGBA lists.

    :param ramp: input (scaled) colour-ramp definition
    :return: A tuple of four lists of floats: representing values, red, green, blue, alpha.
    """
    values = cast(list[float], [])
    red = cast(list[float], [])
    green = cast(list[float], [])
    blue = cast(list[float], [])
    alpha = cast(list[float], [])
    for r in ramp:
        values.append(float(r.value))
        cr, cg, cb, ca = r.rgba
        red.append(cr)
        green.append(cg)
        blue.append(cb)
        alpha.append(ca)

    return values, red, green, blue, alpha


def read_mpl_ramp(mpl_ramp: str) -> RampRepr:
    """
    Extract a named colour ramp from Matplotlib as a normalised OWS-compatible ramp specification

    :param mpl_ramp: The name of Matplotlib colour ramp
    :return: A normalised ramp specification.
    """
    unscaled_cmap: RampRepr = []
    try:
        cmap = plt.get_cmap(mpl_ramp)
    except Exception:
        raise ConfigException(f"Invalid Matplotlib name: {mpl_ramp}") from None
    val_range = numpy.arange(0.1, 1.1, 0.1)
    rgba_hex = to_hex(cmap(0.0))
    unscaled_cmap.append(RampNode(0.0, rgba_hex))
    for val in val_range:
        rgba_hex = to_hex(cast(tuple[float, float, float, float], cmap(val)))
        unscaled_cmap.append(RampNode(float(val), rgba_hex))
    return unscaled_cmap


class ColorRamp:
    """
    Represents a colour ramp for image and legend rendering purposes
    """

    def __init__(
        self, style: StyleDefBase, ramp_cfg: CFG_DICT, legend: "RampLegendBase"
    ) -> None:
        """
        :param style: The style owning the ramp
        :param ramp_cfg: Style config
        """
        self.style = style
        if "color_ramp" in ramp_cfg:
            raw_scaled_ramp = make_ramp_representation(
                cast(RAMP_SPEC, ramp_cfg["color_ramp"]), self.style.name
            )
        else:
            rmin, rmax = cast(list[float], ramp_cfg["range"])
            unscaled_ramp = UNSCALED_DEFAULT_RAMP
            if "mpl_ramp" in ramp_cfg:
                unscaled_ramp = read_mpl_ramp(cast(str, ramp_cfg["mpl_ramp"]))
            raw_scaled_ramp = scale_unscaled_ramp(rmin, rmax, unscaled_ramp)
        self.ramp = raw_scaled_ramp

        self.values = cast(list[float], [])
        self.components = cast(MutableMapping[str, list[float]], {})
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
                col_val = col_point.value
                if not leg_begin_in_ramp and leg_begin_before_idx is None:
                    if isclose(col_val, fleg_begin, abs_tol=1e-9):
                        leg_begin_in_ramp = True
                    elif col_val > fleg_begin:
                        leg_begin_before_idx = idx
                if not leg_end_in_ramp and leg_end_before_idx is None:
                    if isclose(col_val, fleg_end, abs_tol=1e-9):
                        leg_end_in_ramp = True
                    elif col_val > fleg_end:
                        leg_end_before_idx = idx
            if not leg_begin_in_ramp:
                rgba = self.rgba_at(fleg_begin)
                begin_col_point = RampNode(fleg_begin, to_hex(rgba))
                if leg_begin_before_idx is None:
                    self.ramp.append(begin_col_point)
                else:
                    self.ramp.insert(leg_begin_before_idx, begin_col_point)
                if leg_end_before_idx is not None:
                    leg_end_before_idx += 1
            if not leg_end_in_ramp:
                rgba = self.rgba_at(fleg_end)
                end_col_point = RampNode(fleg_end, to_hex(rgba))
                if leg_end_before_idx is None:
                    self.ramp.append(end_col_point)
                else:
                    self.ramp.insert(leg_end_before_idx, end_col_point)
            if not leg_end_in_ramp or not leg_begin_in_ramp:
                self.crack_ramp()

    def crack_ramp(self) -> None:
        values, r, g, b, a = crack_ramp(self.ramp)
        self.values = values
        self.components = {"red": r, "green": g, "blue": b, "alpha": a}

    def get_value(self, data: float | DataArray, band: str) -> numpy.ndarray | float:
        return numpy.interp(data, self.values, self.components[band])

    def get_8bit_value(self, data: DataArray, band: str) -> numpy.ndarray:
        val = cast(numpy.ndarray, self.get_value(data, band))
        val = val * 255
        # Is there a way to stop this raising a runtime warning?
        return val.astype(ubyte)

    def apply(self, data: DataArray) -> Dataset:
        imgdata = cast(MutableMapping[Hashable, Any], {})
        for band in self.components:
            imgdata[band] = (data.dims, self.get_8bit_value(data, band))
        return Dataset(imgdata, coords=data.coords)

    def rgba_at(self, val: float) -> tuple[float, float, float, float]:
        return (
            float(self.get_value(val, "red")),
            float(self.get_value(val, "green")),
            float(self.get_value(val, "blue")),
            float(self.get_value(val, "alpha")),
        )


class RampLegendBase(StyleDefBase.Legend, OWSMetadataConfig):
    METADATA_ABSTRACT: bool = False
    METADATA_LEGEND_UNITS: bool = True
    METADATA_TICK_LABELS: bool = True

    def __init__(
        self, style_or_mdh: Union["StyleDefBase", "StyleDefBase.Legend"], cfg: CFG_DICT
    ) -> None:
        super().__init__(style_or_mdh, cfg)
        raw_cfg = cast(CFG_DICT, self._raw_cfg)
        # Range - defaults deferred until we have parsed the associated ramp
        if "begin" not in raw_cfg:
            self.begin = Decimal("nan")
        else:
            self.begin = Decimal(cast(str | float | int, raw_cfg["begin"]))
        if "end" not in raw_cfg:
            self.end = Decimal("nan")
        else:
            self.end = Decimal(cast(str | float | int, raw_cfg["end"]))

        # decimal_places, rounder
        def rounder_str(prec: int) -> str:
            rstr = "1"
            if prec == 0:
                return rstr
            rstr += "."
            for _ in range(prec - 1):
                rstr += "0"
            rstr += "1"
            return rstr

        self.decimal_places = cast(int, raw_cfg.get("decimal_places", 1))
        if self.decimal_places < 0:
            raise ConfigException("decimal_places cannot be negative")
        self.rounder = Decimal(rounder_str(self.decimal_places))

        # Ticks - Non-explicit tick values deferred until we have parsed the associated ramp
        ticks_handled = False
        self.ticks_every: Decimal | None = None
        self.tick_count: int | None = None
        self.ticks: list[Decimal] = []
        if "ticks_every" in raw_cfg:
            if "tick_count" in raw_cfg:
                raise ConfigException(
                    "Cannot use tick count and ticks_every in the same legend"
                )
            if "ticks" in raw_cfg:
                raise ConfigException(
                    "Cannot use ticks and ticks_every in the same legend"
                )
            self.ticks_every = Decimal(cast(int | float | str, raw_cfg["ticks_every"]))
            if self.ticks_every.is_zero() or self.ticks_every.is_signed():
                raise ConfigException("ticks_every must be greater than zero")
            ticks_handled = True
        if "ticks" in raw_cfg:
            if "tick_count" in raw_cfg:
                raise ConfigException(
                    "Cannot use tick count and ticks in the same legend"
                )
            self.ticks = [
                Decimal(t) for t in cast(list[str | int | float], raw_cfg["ticks"])
            ]
            ticks_handled = True
        if not ticks_handled:
            self.tick_count = int(cast(str | int, raw_cfg.get("tick_count", 1)))
            if self.tick_count < 0:
                raise ConfigException("tick_count cannot be negative")
        # prepare for tick labels
        self.cfg_labels = cast(
            MutableMapping[str, MutableMapping[str, str]],
            raw_cfg.get("tick_labels", {}),
        )
        defaults = self.cfg_labels.get("default", {})
        self.lbl_default_prefix = defaults.get("prefix", "")
        self.lbl_default_suffix = defaults.get("suffix", "")
        self.tick_labels: list[str] = []
        # handle matplotlib args
        self.strip_location = cast(
            tuple[float, float, float, float],
            tuple(
                cast(
                    Iterable[float],
                    raw_cfg.get("strip_location", [0.05, 0.5, 0.9, 0.15]),
                )
            ),
        )
        # throw error on legacy syntax
        self.fail_legacy()

    def fail_legacy(self) -> None:
        if any(
            legent in cast(CFG_DICT, self._raw_cfg)
            for legent in ["major_ticks", "offset", "scale_by", "radix_point"]
        ):
            raise ConfigException(
                f"Style {self.style.name} uses a no-longer supported format for legend configuration.  "
                + "Please refer to the documentation and update your config"
            )

    def register_ramp(self, ramp: ColorRamp) -> None:
        if self.begin.is_nan():
            for col_def in ramp.ramp:
                if isclose(col_def.rgba[-1], 1.0, abs_tol=1e-9):
                    self.begin = Decimal(col_def.value)
                    break
            if self.begin.is_nan():
                self.begin = Decimal(ramp.ramp[0].value)
        if self.end.is_nan():
            for col_def in reversed(ramp.ramp):
                if isclose(col_def.rgba[-1], 1.0, abs_tol=1e-9):
                    self.end = Decimal(col_def.value)
                    break
            if self.end.is_nan():
                self.end = Decimal(ramp.ramp[-1].value)
        for t in self.ticks:
            if t < self.begin or t > self.end:
                raise ConfigException(
                    "Explicit ticks must all be within legend begin/end range"
                )
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
                    self.ticks.append(
                        tickval.quantize(self.rounder, rounding=ROUND_HALF_UP)
                    )

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
        self.parse_metadata(cast(CFG_DICT, self._raw_cfg))

    def tick_label(self, tick: Decimal) -> str | None:
        try:
            tick_idx = self.ticks.index(tick)
            metaval = self.read_local_metadata(f"lbl_{tick}")
            if metaval:
                return metaval
            return self.tick_labels[tick_idx]
        except ValueError:
            _LOG.error("'%s' is a not a valid tick", tick)
            return None

    def create_cdict_ticks(
        self,
    ) -> tuple[
        MutableMapping[str, list[tuple[float, float, float]]],
        MutableMapping[float, str],
    ]:
        normalize_factor = float(self.end) - float(self.begin)
        cdict = cast(MutableMapping[str, list[tuple[float, float, float]]], {})
        bands = cast(
            MutableMapping[str, list[tuple[float, float, float]]], defaultdict(list)
        )
        started = False
        finished = False
        for index, ramp_node in enumerate(self.style_or_mdh.color_ramp.ramp):
            if finished:
                break

            value = ramp_node.value
            normalized = (value - float(self.begin)) / float(normalize_factor)

            if not started:
                if isclose(value, float(self.begin), abs_tol=1e-9):
                    started = True
                else:
                    continue
            if not finished and isclose(value, float(self.end), abs_tol=1e-9):
                finished = True

            for band, intensity in self.style_or_mdh.color_ramp.components.items():
                bands[band].append((normalized, intensity[index], intensity[index]))

        for band, blist in bands.items():
            cdict[band] = blist

        ticks = cast(MutableMapping[float, str], {})
        for tick in self.ticks:
            value = float(tick)
            normalized = (value - float(self.begin)) / float(normalize_factor)
            ticks[normalized] = cast(str, self.tick_label(tick))

        return cdict, ticks

    def display_title(self) -> str:
        if self.units:
            return f"{self.title}({self.units})"
        return self.title

    def plot_name(self) -> str:
        return f"{self.style.product.name}_{self.style.name}"

    @override
    def render(self, bytesio: io.BytesIO) -> None:
        cdict, ticks = self.create_cdict_ticks()
        plt.rcdefaults()
        if self.mpl_rcparams:
            plt.rcParams.update(self.mpl_rcparams)
        fig = plt.figure(figsize=(self.width, self.height))
        ax = fig.add_axes(self.strip_location)
        custom_map = LinearSegmentedColormap(self.plot_name(), cdict)  # type: ignore[arg-type]
        color_bar = matplotlib.colorbar.ColorbarBase(
            ax, cmap=custom_map, orientation="horizontal"
        )
        color_bar.set_ticks(list(ticks.keys()))
        color_bar.set_ticklabels(list(ticks.values()))
        color_bar.set_label(self.display_title())
        plt.savefig(bytesio, format="png")

    # For MetadataConfig
    @property
    @override
    def default_title(self) -> str | None:
        return self.style.title


class ColorRampDef(StyleDefBase):
    """
    Colour ramp Style subclass
    """

    auto_legend = True

    def __init__(
        self,
        product: "OWSNamedLayer",
        style_cfg: CFG_DICT,
        stand_alone: bool = False,
        defer_multi_date: bool = False,
        user_defined: bool = False,
    ) -> None:
        """
        Constructor - refer to StyleDefBase
        """
        super().__init__(
            product,
            style_cfg,
            stand_alone=stand_alone,
            defer_multi_date=True,
            user_defined=user_defined,
        )
        style_cfg = cast(CFG_DICT, self._raw_cfg)
        self.color_ramp = ColorRamp(
            self, style_cfg, cast(ColorRampDef.Legend, self.legend_cfg)
        )
        self.include_in_feature_info = bool(
            style_cfg.get("include_in_feature_info", True)
        )

        if "index_function" in style_cfg:
            self.index_function: FunctionWrapper | Expression = FunctionWrapper(
                self,
                cast(CFG_DICT, style_cfg["index_function"]),
                stand_alone=self.stand_alone,
            )
            if not self.stand_alone:
                for band in cast(list[str], style_cfg["needed_bands"]):
                    self.raw_needed_bands.add(band)
        elif "index_expression" in style_cfg:
            self.index_function = Expression(
                self, cast(str, style_cfg["index_expression"])
            )
            for band in self.index_function.needed_bands:
                self.raw_needed_bands.add(band)
            if self.stand_alone:
                self.needed_bands = {self.local_band(b) for b in self.raw_needed_bands}
                self.flag_bands = set()
        else:
            raise ConfigException(
                "Index function is required for index and hybrid styles. "
                f"Style {self.name} in layer {self.product.name}"
            )
        if not defer_multi_date:
            self.parse_multi_date(style_cfg)

    def apply_index(self, data: Dataset) -> DataArray:
        """
        Caclulate index value across data.

        :param data: Input dataset
        :return: Matching dataarray carrying the index value
        """
        index_data = self.index_function(data)
        data["index_function"] = (index_data.dims, index_data.data)
        return data["index_function"]

    @override
    def transform_single_date_data(self, data: Dataset) -> Dataset:
        """
        Apply style to raw data to make an RGBA image xarray (single time slice only)

        :param data: Raw data, all bands.
        :return: RGBA ubyte xarray
        """
        d = self.apply_index(data)
        return self.color_ramp.apply(d)

    class Legend(RampLegendBase):
        @override
        def plot_name(self) -> str:
            return f"{self.style.product.name}_{self.style.name}_{self.style_or_mdh.min_count}"

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
                self.feature_info_label: str | None = None
                self.color_ramp = style.color_ramp
                self.pass_raw_data = False
            else:
                self.feature_info_label = cast(
                    str | None, cfg.get("feature_info_label", None)
                )
                self.color_ramp = ColorRamp(
                    style, cfg, cast(ColorRampDef.Legend, self.legend_cfg)
                )
                self.pass_raw_data = bool(cfg.get("pass_raw_data", False))

        @override
        def transform_data(self, data: Dataset) -> Dataset:
            """
            Apply image transformation

            :param data: Raw data
            :return: RGBA image xarray.  May have a time dimension
            """
            if self.pass_raw_data:
                assert self.aggregator is not None  # For type-checker
                agg = self.aggregator(data)
            else:
                xformed_data = cast("ColorRampDef", self.style).apply_index(data)
                agg = cast(FunctionWrapper, self.aggregator)(xformed_data)
            return self.color_ramp.apply(agg)

        class Legend(RampLegendBase):
            pass


# Register ColorRampDef as Style subclass.
StyleDefBase.register_subclass(ColorRampDef, ("range", "color_ramp"))
