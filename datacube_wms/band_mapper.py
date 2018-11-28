from __future__ import absolute_import, division, print_function
from xarray import Dataset, DataArray, merge
import numpy
from colour import Color
from collections import defaultdict

from datacube.storage.masking import make_mask

import logging
from datetime import datetime

# pylint: disable=wrong-import-position
import matplotlib
# Do not use X Server backend
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.patches as mpatches
import io
from textwrap import fill

from math import isclose

_LOG = logging.getLogger(__name__)

class StyleMask(object):
    def __init__(self, flags, invert=False):
        self.flags = flags
        self.invert = invert

class StyleDefBase(object):
    def __init__(self, product, style_cfg):
        self.product = product
        self.name = style_cfg["name"]
        self.title = style_cfg["title"]
        self.abstract = style_cfg["abstract"]
        self.masks = [StyleMask(**mask_cfg) for mask_cfg in style_cfg.get("pq_masks", [])]
        self.needed_bands = set()
        for band in self.product.always_fetch_bands:
            self.needed_bands.add(band)

        self.legend_cfg = style_cfg.get("legend", dict())

    def apply_masks(self, data, pq_data):
        if pq_data is not None:
            net_mask = None
            for mask in self.masks:
                odc_mask = make_mask(pq_data, **mask.flags)
                mask_data = getattr(odc_mask, self.product.pq_band)
                if mask.invert:
                    mask_data = ~mask_data
                data = data.where(mask_data)
        return data

    def transform_data(self, data, pq_data, extent_mask, *masks):
        pass

    def legend(self, bytesio):
        pass

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

class RGBMappedStyleDef(StyleDefBase):
    def __init__(self, product, style_cfg):
        super(RGBMappedStyleDef, self).__init__(product, style_cfg)
        self.value_map = style_cfg["value_map"]
        for band in self.value_map.keys():
            self.needed_bands.add(self.product.band_idx.band(band))


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
            band = self.product.band_idx.band(cfg_band)
            band_data = Dataset()
            for value in values:
                target = Dataset()
                flags = value["flags"]
                rgb = Color(value["color"])
                dims = data[band].dims
                coords = data[band].coords
                bdata = data[band]
                colors = ["red", "green", "blue"]
                for color in colors:
                    c = numpy.full(data[band].shape, getattr(rgb, color))
                    target[color] = DataArray(c, dims=dims, coords=coords)

                if "or" in flags:
                    fs = flags["or"]
                    mask = None
                    for f in fs.items():
                        f = {f[0]: f[1]}
                        if mask is None:
                            mask = make_mask(bdata, **f)
                        else:
                            mask |= make_mask(bdata, **f)
                else:
                    fs = flags if "and" not in flags else flags["and"]
                    mask = make_mask(bdata, **fs)

                masked = target.where(mask)

                if len(band_data.data_vars) == 0:
                    band_data = masked
                else:
                    band_data = band_data.combine_first(masked)

            if len(imgdata.data_vars) == 0:
                imgdata = band_data
            else:
                imgdata = merge([imgdata, band_data])
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
                    patch = mpatches.Patch(color=rgb.hex, label=label)
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
    def components(self):
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
        for imgband, components in self.components.items():
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


def hm_index_to_blue(val, rmin, rmax, nan_mask=True):
    scaled = (val - rmin) / (rmax - rmin)
    if scaled < 0.0:
        if nan_mask:
            return float("nan")
        else:
            return 0.0
    elif scaled > 0.5:
        return 0.0
    elif scaled < 0.1:
        return 0.5 + scaled * 5.0
    elif scaled > 0.3:
        return 2.5 - scaled * 5.0
    else:
        return 1.0


def hm_index_to_green(val, rmin, rmax, nan_mask=True):
    scaled = (val - rmin) / (rmax - rmin)
    if scaled < 0.0:
        if nan_mask:
            return float("nan")
        else:
            return 0.0
    elif scaled > 0.9:
        return 0.0
    elif scaled < 0.1:
        return 0.0
    elif scaled < 0.3:
        return -0.5 + scaled * 5.0
    elif scaled > 0.7:
        return 4.5 - scaled * 5.0
    else:
        return 1.0


def hm_index_to_red(val, rmin, rmax, nan_mask=True):
    scaled = (val - rmin) / (rmax - rmin)
    if scaled < 0.0:
        if nan_mask:
            return float("nan")
        else:
            return 0.0
    elif scaled < 0.5:
        return 0.0
    elif scaled < 0.7:
        return -2.5 + scaled * 5.0
    elif scaled > 0.9:
        return 5.5 - scaled * 5.0
    else:
        return 1.0


def hm_index_func_for_range(func, rmin, rmax, nan_mask=True):
    def hm_index_func(val):
        return func(val, rmin, rmax, nan_mask=nan_mask)

    return hm_index_func


# TODO HeatMapped Styles are deprecated and will be removed - Use RGBa Colour Ramp Styles instead
class HeatMappedStyleDef(StyleDefBase):
    def __init__(self, product, style_cfg):
        super(HeatMappedStyleDef, self).__init__(product, style_cfg)
        for b in style_cfg["needed_bands"]:
            self.needed_bands.add(self.product.band_idx.band(b))
        self._index_function = style_cfg["index_function"]
        self.range = style_cfg["range"]

    def transform_data(self, data, pq_data, extent_mask, *masks):
        hm_index_data = self._index_function(data)
        dims = data[list(self.needed_bands)[0]].dims
        imgdata = Dataset()
        for band, map_func in [
                ("red", hm_index_to_red),
                ("green", hm_index_to_green),
                ("blue", hm_index_to_blue),
        ]:
            f = numpy.vectorize(
                hm_index_func_for_range(
                    map_func,
                    self.range[0],
                    self.range[1]
                )
            )
            img_band_raw_data = f(hm_index_data)
            img_band_data = numpy.clip(img_band_raw_data * 255.0, 0, 255).astype("uint8")
            imgdata[band] = (dims, img_band_data)
        if extent_mask is not None:
            imgdata = imgdata.where(extent_mask)
        imgdata = self.apply_masks(imgdata, pq_data)
        imgdata = imgdata.astype("uint8")
        return imgdata


# TODO Hybrid Styles should be removed or converted to share code with RGBa Colour Ramp Styles instead of HeatMaps.
class HybridStyleDef(HeatMappedStyleDef, LinearStyleDef):
    def __init__(self, product, style_cfg):
        super(HybridStyleDef, self).__init__(product, style_cfg)
        self.component_ratio = style_cfg["component_ratio"]

    def transform_data(self, data, pq_data, extent_mask, *masks):
        #pylint: disable=too-many-locals
        hm_index_data = self._index_function(data)
        hm_mask = hm_index_data != float("nan")
        data = self.apply_masks(data, pq_data)

        dims = data[list(self.needed_bands)[0]].dims
        imgdata = Dataset()
        for band, map_func in [
                ("red", hm_index_to_red),
                ("green", hm_index_to_green),
                ("blue", hm_index_to_blue),
        ]:
            components = self.components[band]
            component_band_data = None
            for c_band, c_intensity in components.items():
                imgband_component_data = data[c_band] * c_intensity
                if component_band_data is not None:
                    component_band_data += imgband_component_data
                else:
                    component_band_data = imgband_component_data
            f = numpy.vectorize(
                hm_index_func_for_range(
                    map_func,
                    self.range[0],
                    self.range[1],
                    nan_mask=False
                )
            )
            hmap_raw_data = f(hm_index_data)
            component_band_data = self.compress_band(component_band_data)
            img_band_data = (hmap_raw_data * 255.0 * (1.0 - self.component_ratio)
                             + self.component_ratio * component_band_data)
            imgdata[band] = (dims, img_band_data.astype("uint8"))
        if extent_mask is not None:
            imgdata = imgdata.where(extent_mask)
        imgdata = imgdata.where(hm_mask)
        imgdata = self.apply_masks(imgdata, pq_data)
        imgdata = imgdata.astype("uint8")
        return imgdata


class RgbaColorRampDef(StyleDefBase):
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

        self.color_ramp = style_cfg["color_ramp"]
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

        self.index_function = style_cfg.get("index_function", None)

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


#pylint: disable=invalid-name, inconsistent-return-statements
def StyleDef(product, cfg):
    if cfg.get("component_ratio", False):
        return HybridStyleDef(product, cfg)
    if cfg.get("heat_mapped", False):
        return HeatMappedStyleDef(product, cfg)
    elif cfg.get("components", False):
        return LinearStyleDef(product, cfg)
    elif cfg.get("value_map", False):
        return RGBMappedStyleDef(product, cfg)
    elif cfg.get("color_ramp", False):
        return RgbaColorRampDef(product, cfg)
