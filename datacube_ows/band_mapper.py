from __future__ import absolute_import, division, print_function
from xarray import Dataset, DataArray, merge
import numpy
from colour import Color
from collections import defaultdict

from datacube.storage.masking import make_mask

import logging
from datetime import datetime
from threading import Lock

# pylint: disable=wrong-import-position
import matplotlib
# Do not use X Server backend
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, to_hex
import matplotlib.patches as mpatches
from textwrap import fill

from math import isclose

from datacube_ows.ogc_utils import FunctionWrapper, ConfigException

_LOG = logging.getLogger(__name__)


# Matplotlib is not thread-safe.  All usage of the matplotlib library should
# be serialised through this lock.
MPL_LOCK = Lock()


class StyleMask(object):
    def __init__(self, flags, invert=False):
        self.flags = flags
        self.invert = invert


class StyleDefBase(object):
    auto_legend = False
    include_in_feature_info = False

    def __init__(self, product, style_cfg):
        self.product = product
        self.name = style_cfg["name"]
        self.title = style_cfg["title"]
        self.abstract = style_cfg["abstract"]
        self.masks = [StyleMask(**mask_cfg) for mask_cfg in style_cfg.get("pq_masks", [])]
        self.needed_bands = set()
        for band in self.product.always_fetch_bands:
            self.needed_bands.add(band)

        self.parse_legend_cfg(style_cfg.get("legend", {}))
        self.legend_cfg = style_cfg.get("legend", dict())

    def apply_masks(self, data, pq_data):
        if pq_data is not None:
            net_mask = None
            for mask in self.masks:
                odc_mask = make_mask(pq_data, **mask.flags)
                mask_data = getattr(odc_mask, self.product.pq_band)
                if mask.invert:
                    mask_data = ~mask_data
                for band in data.data_vars:
                    data[band] = data[band].where(mask_data)
        return data

    def transform_data(self, data, pq_data, extent_mask, *masks):
        pass

    def safe_legend(self, bytesio):
        if not self.auto_legend:
            return None
        with MPL_LOCK:
            return self.legend(bytesio)

    def parse_legend_cfg(self, cfg):
        self.show_legend = cfg.get("show_legend", self.auto_legend)
        self.legend_url_override = cfg.get('url', None)
        self.legend_cfg = cfg

    def legend(self, bytesio):
        raise NotImplementedError()

    def legend_override_with_url(self):
        return self.legend_url_override


# pylint: disable=abstract-method
class DynamicRangeCompression(StyleDefBase):
    def __init__(self, product, style_cfg):
        super(DynamicRangeCompression, self).__init__(product, style_cfg)
        self.scale_factor = style_cfg.get("scale_factor")
        if "scale_range" in style_cfg:
            self.scale_min, self.scale_max = style_cfg["scale_range"]
        else:
            self.scale_min = 0.0
            self.scale_max = 255.0 * style_cfg["scale_factor"]

    def compress_band(self, imgband_data):
        clipped = imgband_data.clip(self.scale_min, self.scale_max)
        normalized = (clipped - self.scale_min) / (self.scale_max - self.scale_min)
        return normalized * 255

class RGBAMappedStyleDef(StyleDefBase):
    auto_legend = True

    def __init__(self, product, style_cfg):
        super(RGBAMappedStyleDef, self).__init__(product, style_cfg)
        self.value_map = style_cfg["value_map"]
        for band in self.value_map.keys():
            self.needed_bands.add(self.product.band_idx.band(band))

    @staticmethod
    def reint(data):
        inted = data.astype("int")
        if hasattr(data, "attrs"):
            attrs = data.attrs
            inted.attrs = attrs
        return inted

    @staticmethod
    def create_colordata(data, rgb, alpha, mask):
        target = Dataset()
        colors = ["red", "green", "blue", "alpha"]
        for color in colors:
            val = alpha if color == "alpha" else getattr(rgb, color)
            c = numpy.full(data.shape, val)
            target[color] = DataArray(c, dims=data.dims, coords=data.coords)
        masked = target.where(mask).where(numpy.isfinite(data))  # remask
        return masked

    @staticmethod
    def create_mask(data, flags):
        if "or" in flags:
            fs = flags["or"]
            mask = None
            for f in fs.items():
                f = {f[0]: f[1]}
                if mask is None:
                    mask = make_mask(data, **f)
                else:
                    mask |= make_mask(data, **f)
        else:
            fs = flags if "and" not in flags else flags["and"]
            mask = make_mask(data, **fs)
        return mask


    def transform_data(self, data, pq_data, extent_mask, *masks):
        # pylint: disable=too-many-locals, too-many-branches
        # extent mask data per band to preseve nodata
        _LOG.debug("transform begin %s", datetime.now())
        if extent_mask is not None:
            for band in data.data_vars:
                try:
                    data[band] = data[band].where(extent_mask, other=data[band].attrs['nodata'])
                except AttributeError:
                    data[band] = data[band].where(extent_mask)

        _LOG.debug("extent mask complete %d", datetime.now())
        data = self.apply_masks(data, pq_data)
        _LOG.debug("mask complete %d", datetime.now())
        imgdata = Dataset()
        for cfg_band, values in self.value_map.items():
            # Run through each item
            band = self.product.band_idx.band(cfg_band)
            band_data = Dataset()
            bdata = data[band]
            if bdata.dtype.kind == 'f':
                # Convert back to int for bitmasking
                bdata = RGBAMappedStyleDef.reint(bdata)
            for value in values:
                flags = value["flags"]
                rgb = Color(value["color"])
                alpha = value.get("alpha", 1.0)
                mask_source_band = value.get("mask", False)

                mask = RGBAMappedStyleDef.create_mask(bdata, flags)

                if mask_source_band:
                    # disable checking on the use of ~mask
                    # pylint: disable=invalid-unary-operand-type
                    bdata = bdata.where(~mask)
                    bdata = RGBAMappedStyleDef.reint(bdata)
                else:
                    masked = RGBAMappedStyleDef.create_colordata(bdata, rgb, alpha, mask)
                    band_data = masked if len(band_data.data_vars) == 0 else band_data.combine_first(masked)

            imgdata = band_data if len(imgdata.data_vars) == 0 else merge([imgdata, band_data])

        imgdata *= 255
        return imgdata.astype('uint8')

    def legend(self, bytesio):
        patches = []
        for band in self.value_map.keys():
            for value in self.value_map[band]:
                # only include values that have a title set
                if "title" in value and "abstract" in value and "color" in value and value["title"]:
                    rgb = Color(value["color"])
                    label = fill(value["title"] + " - " + value["abstract"], 30)
                    try:
                        patch = mpatches.Patch(color=rgb.hex_l, label=label)
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


# pylint: disable=abstract-method
class LinearStyleDef(DynamicRangeCompression):
    def __init__(self, product, style_cfg):
        super(LinearStyleDef, self).__init__(product, style_cfg)
        self.red_components = self.dealias_components(style_cfg["components"]["red"])
        self.green_components = self.dealias_components(style_cfg["components"]["green"])
        self.blue_components = self.dealias_components(style_cfg["components"]["blue"])
        self.alpha_components = self.dealias_components(style_cfg["components"].get("alpha", None))
        for band in self.red_components.keys():
            self.needed_bands.add(band)
        for band in self.green_components.keys():
            self.needed_bands.add(band)
        for band in self.blue_components.keys():
            self.needed_bands.add(band)

        if self.alpha_components is not None:
            for band in self.alpha_components.keys():
                self.needed_bands.add(band)

    def dealias_components(self, comp_in):
        if comp_in is None:
            return None
        else:
            return { self.product.band_idx.band(band_alias): value for band_alias, value in comp_in.items() }

    @property
    def rgb_components(self):
        if self.alpha_components is not None:
            return {
                "red": self.red_components,
                "green": self.green_components,
                "blue": self.blue_components,
                "alpha": self.alpha_components,
            }

        return {
            "red": self.red_components,
            "green": self.green_components,
            "blue": self.blue_components,
        }

    def transform_data(self, data, pq_data, extent_mask, *masks):
        if extent_mask is not None:
            data = data.where(extent_mask)
        data = self.apply_masks(data, pq_data)
        imgdata = Dataset()
        for imgband, components in self.rgb_components.items():
            imgband_data = None
            for band, intensity in components.items():
                if callable(intensity):
                    imgband_component = intensity(data[band], band, imgband)
                else:
                    imgband_component = data[band] * intensity

                if imgband_data is not None:
                    imgband_data += imgband_component
                else:
                    imgband_data = imgband_component
            dims = imgband_data.dims
            if imgband == "alpha":
                imgband_data = imgband_data.astype('uint8').values
            else:
                imgband_data = self.compress_band(imgband_data).astype('uint8')
            imgdata[imgband] = (dims, imgband_data)
        return imgdata


UNSCALED_DEFAULT_RAMP = [
    # TODO: -0.0 is not really different number to 0.0 (does this indicate a specific limit case)
    {
        "value": -0.0,
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
    return [
        {
            "value": (rmax - rmin)*u["value"] + rmin,
            "color": u["color"],
            "alpha": u.get("alpha", 1.0)
        } for u in unscaled
    ]

def read_mpl_ramp(mpl_ramp : str):
    unscaled_cmap = []
    cmap = plt.get_cmap(mpl_ramp)
    val_range = numpy.arange(0.1, 1.1, 0.1)
    rgba_hex = to_hex(cmap(0.0))
    unscaled_cmap.append(
        {
            "value" : 0.0,
            "color" : rgba_hex,
            "alpha" : 1.0
        }
    )
    for val in val_range:
        rgba_hex = to_hex(cmap(val))
        unscaled_cmap.append(
            {
                "value" : float(val),
                "color" : rgba_hex
            }
        )
    return unscaled_cmap


class RgbaColorRampDef(StyleDefBase):
    auto_legend = True
    def __init__(self, product, style_cfg):
        super(RgbaColorRampDef, self).__init__(product, style_cfg)

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

        if "color_ramp" in style_cfg:
            self.color_ramp = style_cfg["color_ramp"]
        else:
            rmin, rmax = style_cfg["range"]
            unscaled_ramp = UNSCALED_DEFAULT_RAMP
            if "mpl_ramp" in style_cfg:
                unscaled_ramp = read_mpl_ramp(style_cfg["mpl_ramp"])
            self.color_ramp = scale_unscaled_ramp(
                    rmin, rmax, unscaled_ramp)
        values, r, g, b, a = crack_ramp(self.color_ramp)
        self.values = values
        self.components = {
            "red": r,
            "green": g,
            "blue": b,
            "alpha": a
        }
        for band in style_cfg["needed_bands"]:
            self.needed_bands.add(self.product.band_idx.band(band))

        self.include_in_feature_info = style_cfg.get("include_in_feature_info", True)

        if "index_function" in style_cfg:
            self.index_function = FunctionWrapper(self.product, style_cfg["index_function"])
        else:
            raise ConfigException("Index function is required for index and hybrid styles. Style %s in layer %s" % (
                self.name,
                self.product.name
            ) )

    def get_value(self, data, values, intensities):
        return numpy.interp(data, values, intensities)

    def transform_data(self, data, pq_data, extent_mask, *masks):
        if extent_mask is not None:
            data = data.where(extent_mask)
        data = self.apply_masks(data, pq_data)

        data_bands = self.needed_bands

        if self.index_function is not None:
            data_bands = ['index_function']
            data[data_bands[0]] = (data.dims, self.index_function(data))

        imgdata = Dataset()
        for data_band in data_bands:
            d = data[data_band]
            for band, intensity in self.components.items():
                imgdata[band] = (d.dims, self.get_value(d, self.values, intensity))
        imgdata *= 255
        imgdata = imgdata.astype("uint8")
        return imgdata


    def legend(self, bytesio):
        #pylint: disable=too-many-locals, too-many-statements
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
        def create_cdict_ticks(components, cfg):
            generate = (cfg.get("major_ticks", None) is not None or \
               cfg.get("scale_by", None) is not None or \
               cfg.get("radix_point", None) is not None)

            return from_definition(components, cfg, generate)


        def find_clc(ramp, last=False):
            l = ramp if not last else reversed(ramp)
            for index, value in enumerate(l):
                fwd_index = index if not last else (len(ramp) - (index + 1))
                if "legend" in value:
                    return fwd_index
            return 0 if not last else (len(ramp) - 1)


        def from_definition(components, cfg, generate):
            tick_mod = cfg.get("major_ticks", 1)
            tick_scale = cfg.get("scale_by", 1)
            places = cfg.get("radix_point", 1)
            ramp = cfg.get("ramp")

            start_index = find_clc(ramp) if not generate else 0
            stop_index = find_clc(ramp, last=True) if not generate else (len(ramp) - 1)

            start = ramp[start_index].get("value")
            stop = ramp[stop_index].get("value")
            normalize_factor = stop - start

            ticks = dict()
            cdict = dict()
            bands = defaultdict(list)
            for index, ramp_val in enumerate(ramp):
                if index < start_index or index > stop_index:
                    continue

                value = ramp_val.get("value")
                normalized = (value - start) / normalize_factor
                custom_legend_cfg = ramp_val.get("legend", None)

                mod_close = False
                mod_equal = False
                if generate:
                    mod_close = isclose((value * tick_scale) % (tick_mod * tick_scale), 0.0, abs_tol=1e-8)
                    mod_equal = value % tick_mod == 0

                if mod_close or mod_equal:
                    label = value * tick_scale
                    label = round(label, places) if places > 0 else int(label)
                    ticks[normalized] = label

                if custom_legend_cfg is not None:
                    label = custom_label(value, custom_legend_cfg)
                    ticks[normalized] = label

                for band, intensity in components.items():
                    bands[band].append((normalized, intensity[index], intensity[index]))

            for band, blist in bands.items():
                cdict[band] = tuple(blist)

            if len(ticks) == 0:
                ticks = None
            return cdict, ticks


        combined_cfg = self.legend_cfg
        combined_cfg["ramp"] = self.color_ramp

        cdict, ticks = create_cdict_ticks(self.components, combined_cfg)
        
        # TODO: Potentially short-circuit this if using string based mpl_ramp
        # custom_map = plt.get_cmap(style_cfg["mpl_ramp"]) should return a LinearSegmentedColormap

        plt.rcdefaults()
        if combined_cfg.get("rcParams", None) is not None:
            plt.rcParams.update(combined_cfg.get("rcParams"))
        fig = plt.figure(figsize=(combined_cfg.get("width", 4),
                                  combined_cfg.get("height", 1.25)))
        ax_pos = combined_cfg.get("axes_position", [0.05, 0.5, 0.9, 0.15])
        ax = fig.add_axes(ax_pos)
        custom_map = LinearSegmentedColormap(self.product.name, cdict)
        color_bar = matplotlib.colorbar.ColorbarBase(
            ax,
            cmap=custom_map,
            orientation="horizontal")

        if ticks is not None:
            color_bar.set_ticks(list(ticks.keys()))
            color_bar.set_ticklabels([str(l) for l in ticks.values()])

        title = self.legend_cfg.get("title", self.title)
        unit = self.legend_cfg.get("units", "unitless")
        title = title + "(" + unit + ")"

        color_bar.set_label(title)

        plt.savefig(bytesio, format='png')


class HybridStyleDef(RgbaColorRampDef, LinearStyleDef):
    auto_legend = False
    def __init__(self, product, style_cfg):
        super(HybridStyleDef, self).__init__(product, style_cfg)
        self.component_ratio = style_cfg["component_ratio"]

    def transform_data(self, data, pq_data, extent_mask, *masks):
        #pylint: disable=too-many-locals
        if extent_mask is not None:
            data = data.where(extent_mask)
        data = self.apply_masks(data, pq_data)

        data_bands = self.needed_bands

        if self.index_function is not None:
            data_bands = ['index_function']
            data[data_bands[0]] = (data.dims, self.index_function(data))
        imgdata = Dataset()
        for data_band in data_bands:
            d = data[data_band]
            for band, intensity in self.components.items():
                rampdata = self.get_value(d, self.values, intensity)
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
                            component_band_data = self.compress_band(component_band_data)
                    img_band_data = (rampdata * 255.0 * (1.0 - self.component_ratio)
                                     + self.component_ratio * component_band_data)
                else:
                    img_band_data = rampdata * 255.0
                imgdata[band] = (d.dims, img_band_data.astype("uint8"))

        return imgdata


#pylint: disable=invalid-name, inconsistent-return-statements
def StyleDef(product, cfg):
    try:
        if "component_ratio" in cfg:
            return HybridStyleDef(product, cfg)
        elif cfg.get("components", False):
            return LinearStyleDef(product, cfg)
        elif cfg.get("value_map", False):
            return RGBAMappedStyleDef(product, cfg)
        elif cfg.get("color_ramp", False) or cfg.get("range", False):
            return RgbaColorRampDef(product, cfg)
    except KeyError:
        raise ConfigException("Required field missing in style %s of layer %s" % (
            cfg.get("name", ""),
            product.name
        ))
