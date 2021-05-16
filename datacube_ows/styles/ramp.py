# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import logging
from collections import defaultdict
from decimal import ROUND_HALF_UP, Decimal
from math import isclose

import matplotlib
import numpy
from colour import Color
from matplotlib import pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_hex
from xarray import Dataset

matplotlib.use('Agg')

from datacube_ows.ogc_utils import ConfigException, FunctionWrapper
from datacube_ows.styles.base import StyleDefBase
from datacube_ows.styles.expression import Expression

_LOG = logging.getLogger(__name__)

UNSCALED_DEFAULT_RAMP = [
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


def scale_unscaled_ramp(rmin, rmax, unscaled):
    if isinstance(rmin, str):
        rmin = float(rmin)
    if isinstance(rmax, str):
        rmax = float(rmax)
    return [
        {
            "value": (rmax - rmin) * u["value"] + rmin,
            "color": u["color"],
            "alpha": u.get("alpha", 1.0)
        } for u in unscaled
    ]


def crack_ramp(ramp):
    values = []
    red = []
    green = []
    blue = []
    alpha = []
    for r in ramp:
        values.append(float(r["value"]))
        color = Color(r["color"])
        red.append(color.red)
        green.append(color.green)
        blue.append(color.blue)
        alpha.append(r.get("alpha", 1.0))

    return (values, red, green, blue, alpha)


def read_mpl_ramp(mpl_ramp: str):
    unscaled_cmap = []
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


def colour_ramp_legend(bytesio, legend_cfg, colour_ramp, map_name,
                       default_title):
    if colour_ramp.legend_legacy:
        return legacy_colour_ramp_legend(bytesio, legend_cfg,
                                  colour_ramp, map_name,
                                  default_title)

    def create_cdict_ticks(cfg, ramp):
        normalize_factor = ramp.legend_end - ramp.legend_begin

        cdict = dict()
        bands = defaultdict(list)
        started = False
        finished = False
        for index, ramp_point in enumerate(ramp.ramp):
            if finished:
                continue

            value = ramp_point.get("value")
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
            cdict[band] = tuple(blist)

        ticks = dict()
        for tick, tick_lbl in zip(ramp.ticks, ramp.tick_labels):
            value = float(tick)
            normalized = (value - float(ramp.legend_begin)) / float(normalize_factor)
            ticks[normalized] = tick_lbl

        if len(ticks) == 0:
            ticks = None
        return cdict, ticks

    cdict, ticks = create_cdict_ticks(legend_cfg, colour_ramp)

    plt.rcdefaults()
    if colour_ramp.legend_mpl_rcparams:
        plt.rcParams.update(colour_ramp.legend_mpl_rcparams)
    fig = plt.figure(figsize=(colour_ramp.legend_width,
                              colour_ramp.legend_height))
    ax = fig.add_axes(colour_ramp.legend_strip_location)
    custom_map = LinearSegmentedColormap(map_name, cdict)
    color_bar = matplotlib.colorbar.ColorbarBase(
        ax,
        cmap=custom_map,
        orientation="horizontal")

    if ticks is not None:
        color_bar.set_ticks(list(ticks.keys()))
        color_bar.set_ticklabels(list(ticks.values()))

    title = colour_ramp.legend_title if colour_ramp.legend_title else default_title
    if colour_ramp.legend_units:
        title = title + "(" + colour_ramp.legend_units + ")"

    color_bar.set_label(title)

    plt.savefig(bytesio, format='png')


def legacy_colour_ramp_legend(bytesio, legend_cfg, colour_ramp, map_name,
                       default_title):
    def custom_label(label, custom_config):
        prefix = custom_config.get("prefix", "")
        l = custom_config.get("label", label)
        suffix = custom_config.get("suffix", "")
        return f"{prefix}{l}{suffix}"

    # Create custom cdict for matplotlib colorramp
    # Matplot lib color dicts must start at 0 and end at 1
    # because of this we normalize the values
    # Also create tick labels based on configuration
    # ticks are also normalized between 0 - 1.0
    # so they are position correctly on the colorbar
    def create_cdict_ticks(cfg, ramp):
        generate = (cfg.get("major_ticks", None) is not None or
                    cfg.get("scale_by", None) is not None or
                    cfg.get("radix_point", None) is not None)

        return from_definition(cfg, ramp, generate)

    def find_clc(ramp, last=False):
        l = ramp.ramp if not last else reversed(ramp.ramp)
        for index, value in enumerate(l):
            fwd_index = index if not last else (len(ramp.ramp) - (index + 1))
            if "legend" in value:
                return fwd_index
        return 0 if not last else (len(ramp.ramp) - 1)

    def from_definition(cfg, ramp, generate):
        tick_mod = cfg.get("major_ticks", 1)
        tick_offset = cfg.get("offset", 0)
        tick_scale = cfg.get("scale_by", 1)
        places = cfg.get("radix_point", 1)

        start_index = find_clc(ramp) if not generate else 0
        stop_index = find_clc(ramp, last=True) if not generate else (len(ramp.ramp) - 1)

        start = ramp.ramp[start_index].get("value")
        stop = ramp.ramp[stop_index].get("value")
        normalize_factor = stop - start

        ticks = dict()
        cdict = dict()
        bands = defaultdict(list)
        for index, ramp_val in enumerate(ramp.ramp):
            if index < start_index or index > stop_index:
                continue

            value = ramp_val.get("value")
            normalized = (value - start) / normalize_factor
            custom_legend_cfg = ramp_val.get("legend", None)

            mod_close = False
            mod_equal = False
            if generate:
                mod_close = isclose((value * tick_scale + tick_offset) % (tick_mod * tick_scale), 0.0, abs_tol=1e-8)
                mod_equal = value % tick_mod == 0

            if mod_close or mod_equal:
                label = value * tick_scale + tick_offset
                label = round(label, places) if places > 0 else int(label)
                ticks[normalized] = label

            if custom_legend_cfg is not None:
                label = custom_label(value, custom_legend_cfg)
                ticks[normalized] = label

            for band, intensity in ramp.components.items():
                bands[band].append((normalized, intensity[index], intensity[index]))

        for band, blist in bands.items():
            cdict[band] = tuple(blist)

        if len(ticks) == 0:
            ticks = None
        return cdict, ticks

    cdict, ticks = create_cdict_ticks(legend_cfg, colour_ramp)

    # TODO: Potentially short-circuit this if using string based mpl_ramp
    # custom_map = plt.get_cmap(style_cfg["mpl_ramp"]) should return a LinearSegmentedColormap

    plt.rcdefaults()
    if legend_cfg.get("rcParams", None) is not None:
        plt.rcParams.update(legend_cfg.get("rcParams"))
    fig = plt.figure(figsize=(legend_cfg.get("width", 4),
                              legend_cfg.get("height", 1.25)))
    ax_pos = legend_cfg.get("axes_position", [0.05, 0.5, 0.9, 0.15])
    ax = fig.add_axes(ax_pos)
    custom_map = LinearSegmentedColormap(map_name, cdict)
    color_bar = matplotlib.colorbar.ColorbarBase(
        ax,
        cmap=custom_map,
        orientation="horizontal")

    if ticks is not None:
        color_bar.set_ticks(list(ticks.keys()))
        color_bar.set_ticklabels([str(l) for l in ticks.values()])

    title = legend_cfg.get("title", default_title)
    unit = legend_cfg.get("units", "unitless")
    title = title + "(" + unit + ")"

    color_bar.set_label(title)

    plt.savefig(bytesio, format='png')


class ColorRamp:
    def __init__(self, style, ramp_cfg):
        self.style = style
        if "color_ramp" in ramp_cfg:
            raw_scaled_ramp = ramp_cfg["color_ramp"]
        else:
            rmin, rmax = ramp_cfg["range"]
            unscaled_ramp = UNSCALED_DEFAULT_RAMP
            if "mpl_ramp" in ramp_cfg:
                unscaled_ramp = read_mpl_ramp(ramp_cfg["mpl_ramp"])
            raw_scaled_ramp = scale_unscaled_ramp(
                rmin, rmax, unscaled_ramp)
        self.ramp = raw_scaled_ramp
        legend_cfg = ramp_cfg.get("legend", {})
        if legend_cfg.get("show_legend", True) and not legend_cfg.get("url"):
            self.parse_legend(legend_cfg)
        else:
            self.auto_legend = False

        self.crack_ramp()

        if self.auto_legend and not self.legend_legacy:
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

    def crack_ramp(self):
        values, r, g, b, a = crack_ramp(self.ramp)
        self.values = values
        self.components = {
            "red": r,
            "green": g,
            "blue": b,
            "alpha": a
        }

    def parse_legend(self, cfg):
        def rounder_str(prec):
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
        self.legend_legacy = any(
            legent in cfg
            for legent in ["major_ticks", "offset", "scale_by", "radix_point"]
        )
        if not self.legend_legacy and all(
            legent not in cfg
            for legent in ["begin", "end", "decimal_places", "ticks_every", "tick_count", "tick_labels", "ticks"]
        ):
            # No legacy entries, but no new entries either.
            # Check ramp for legend tips
            for r in self.ramp:
                if "legend" in r:
                    self.legend_legacy = True
                    break
        if self.legend_legacy:
            _LOG.warning("Style %s uses deprecated legend configuration.  Please refer to the documentation and update your config",
                         self.style.name)

    def parse_legend_range(self, cfg):
        # pylint: disable=attribute-defined-outside-init
        self.legend_begin = None
        # pylint: disable=attribute-defined-outside-init
        self.legend_end = None
        if "begin" in cfg:
            self.legend_begin = Decimal(cfg["begin"])
        else:
            for col_def in self.ramp:
                if isclose(col_def.get("alpha", 1.0), 1.0, abs_tol=1e-9):
                    self.legend_begin = Decimal(col_def["value"])
                    break
            if self.legend_begin is None:
                self.legend_begin = Decimal(self.ramp[0]["value"])
        if "end" in cfg:
            self.legend_end = Decimal(cfg["end"])
        else:
            for col_def in reversed(self.ramp):
                if col_def.get("alpha", 1.0) == 1.0:
                    self.legend_end = Decimal(col_def["value"])
                    break
            if self.legend_end is None:
                self.legend_end = Decimal(self.ramp[-1]["value"])

    def parse_legend_ticks(self, cfg):
        # Ticks
        ticks = []
        if "ticks_every" in cfg:
            if "tick_count" in cfg:
                raise ConfigException("Cannot use tick count and ticks_every in the same legend")
            if "ticks" in cfg:
                raise ConfigException("Cannot use ticks and ticks_every in the same legend")
            delta = Decimal(cfg["ticks_every"])
            tickval = self.legend_begin
            while tickval < self.legend_end:
                ticks.append(tickval)
                tickval += delta
            ticks.append(tickval)
        if "ticks" in cfg:
            if "tick_count" in cfg:
                raise ConfigException("Cannot use tick count and ticks in the same legend")
            ticks = [Decimal(t) for t in cfg["ticks"]]
        if not ticks:
            count = int(cfg.get("tick_count", 1))
            if count < 0:
                raise ConfigException("tick_count cannot be negative")
            delta = self.legend_end - self.legend_begin
            dcount = Decimal(count)

            for i in range(0, count + 1):
                tickval = self.legend_begin + (Decimal(i) / dcount) * delta
                ticks.append(tickval.quantize(self.rounder, rounding=ROUND_HALF_UP))
        # pylint: disable=attribute-defined-outside-init
        self.ticks = ticks

    def parse_legend_tick_labels(self, cfg):
        labels = cfg.get("tick_labels", {})
        defaults = labels.get("default", {})
        default_prefix = defaults.get("prefix", "")
        default_suffix = defaults.get("suffix", "")
        # pylint: disable=attribute-defined-outside-init
        self.tick_labels = []
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
    def parse_legend_matplotlib_args(self, cfg):
        # pylint: disable=attribute-defined-outside-init
        self.legend_mpl_rcparams = cfg.get("rcParams", {})
        self.legend_width = cfg.get("width", 4)
        self.legend_height = cfg.get("height", 1.25)
        self.legend_strip_location = cfg.get("strip_location",
                                      [0.05, 0.5, 0.9, 0.15])

    def get_value(self, data, band):
        return numpy.interp(data, self.values, self.components[band])

    def get_8bit_value(self, data, band):
        val = self.get_value(data, band)
        return (val * 255).astype("uint8")

    def apply(self, data):
        imgdata = {}
        for band in self.components:
            imgdata[band] = (data.dims, self.get_8bit_value(data, band))
        imgdataset = Dataset(imgdata, coords=data.coords)
        return imgdataset

    def color_alpha_at(self, val):
        color = Color(
            rgb=(
                self.get_value(val, "red").item(),
                self.get_value(val, "green").item(),
                self.get_value(val, "blue").item(),
            )
        )
        alpha = self.get_value(val, "alpha")

        return color, alpha


class ColorRampDef(StyleDefBase):
    auto_legend = True
    def __init__(self, product, style_cfg, stand_alone=False, defer_multi_date=False, user_defined=False):
        super(ColorRampDef, self).__init__(product, style_cfg,
                           stand_alone=stand_alone, defer_multi_date=defer_multi_date, user_defined=user_defined)
        style_cfg = self._raw_cfg
        self.color_ramp = ColorRamp(self, style_cfg)
        self.include_in_feature_info = style_cfg.get("include_in_feature_info", True)

        if "index_function" in style_cfg:
            self.index_function = FunctionWrapper(self,
                                                  style_cfg["index_function"],
                                                  stand_alone=self.stand_alone)
            if not self.stand_alone:
                for band in style_cfg["needed_bands"]:
                    self.raw_needed_bands.add(band)
        elif "index_expression" in style_cfg:
            self.index_function = Expression(self, style_cfg["index_expression"])
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

    def apply_index(self, data):
        index_data = self.index_function(data)
        data['index_function'] = (index_data.dims, index_data)
        return data["index_function"]

    def transform_single_date_data(self, data):
        d = self.apply_index(data)
        return self.color_ramp.apply(d)

    def single_date_legend(self, bytesio):
        colour_ramp_legend(bytesio,
                           self.legend_cfg,
                           self.color_ramp,
                           self.product.name,
                           self.title
                           )

    class MultiDateHandler(StyleDefBase.MultiDateHandler):
        auto_legend = True
        def __init__(self, style, cfg):
            super().__init__(style, cfg)
            self.feature_info_label = cfg.get("feature_info_label", None)

            self.color_ramp = ColorRamp(style, cfg)

        def transform_data(self, data):
            xformed_data = self.style.apply_index(data)
            agg = self.aggregator(xformed_data)
            return self.color_ramp.apply(agg)

        def legend(self, bytesio):
            title = self.legend_cfg.get("title", self.range_str() + " Dates")
            name = self.style.product.name + f"_{self.min_count}"
            colour_ramp_legend(bytesio,
                               self.legend_cfg,
                               self.color_ramp,
                               name,
                               title
                               )
            return True

StyleDefBase.register_subclass(ColorRampDef,
                               ("range", "color_ramp")
)
