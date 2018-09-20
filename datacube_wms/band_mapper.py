from __future__ import absolute_import, division, print_function
from xarray import Dataset, DataArray, merge
import numpy
from colour import Color

from datacube.storage.masking import make_mask

import logging
from datetime import datetime

_LOG = logging.getLogger(__name__)

class StyleMask():
    def __init__(self, flags, invert=False):
        self.flags = flags
        self.invert = invert

class StyleDefBase():
    def __init__(self, product, style_cfg):
        self.product = product
        self.name = style_cfg["name"]
        self.title = style_cfg["title"]
        self.abstract = style_cfg["abstract"]
        self.masks = [StyleMask(**mask_cfg) for mask_cfg in style_cfg.get("pq_masks", [])]
        self.needed_bands = set()
        for band in self.product.always_fetch_bands:
            self.needed_bands.add(band)

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

class DynamicRangeCompression(StyleDefBase):
    def __init__(self, product, style_cfg):
        super(DynamicRangeCompression, self).__init__(product, style_cfg)
        self.scale_factor = style_cfg.get("scale_factor")
        if "scale_range" in style_cfg:
            self.scale_min, self.scale_max = style_cfg["scale_range"]
            self.gain = 255.0/(self.scale_max - self.scale_min)
            self.offset = self.gain * self.scale_min
        else:
            self.scale_min = 0.0
            self.scale_max = 255.0 * style_cfg["scale_factor"]
            self.gain = 1.0 / style_cfg["scale_factor"]
            self.offset = 0.0
    def compress_band(self, imgband_data):
        unclipped = imgband_data * self.gain - self.offset
        return numpy.clip(unclipped.values, 1, 255)

class RGBMappedStyleDef(StyleDefBase):
    def __init__(self, product, style_cfg):
        super(RGBMappedStyleDef, self).__init__(product, style_cfg)
        self.value_map = style_cfg["value_map"]
        for band in self.value_map.keys():
            self.needed_bands.add(band)


    def transform_data(self, data, pq_data, extent_mask, *masks):
        # pylint: disable=too-many-locals
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
        for band in self.value_map.keys():
            band_data = Dataset()
            for value in self.value_map[band]:
                target = Dataset()
                flags = value["flags"]
                rgb = value["values"]
                dims = data[band].dims
                coords = data[band].coords
                bdata = data[band]
                for color, intensity in rgb.items():
                    c = numpy.full(data[band].shape, intensity)
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

        return imgdata.astype('uint8')


class LinearStyleDef(DynamicRangeCompression):
    def __init__(self, product, style_cfg):
        super(LinearStyleDef, self).__init__(product, style_cfg)
        self.red_components = style_cfg["components"]["red"]
        self.green_components = style_cfg["components"]["green"]
        self.blue_components = style_cfg["components"]["blue"]
        self.alpha_components = style_cfg["components"].get("alpha", None);
        for band in self.red_components.keys():
            self.needed_bands.add(band)
        for band in self.green_components.keys():
            self.needed_bands.add(band)
        for band in self.blue_components.keys():
            self.needed_bands.add(band)

        if self.alpha_components is not None:
            for band in self.alpha_components.keys():
                self.needed_bands.add(band)

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


class HeatMappedStyleDef(StyleDefBase):
    def __init__(self, product, style_cfg):
        super(HeatMappedStyleDef, self).__init__(product, style_cfg)
        for b in style_cfg["needed_bands"]:
            self.needed_bands.add(b)
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

        values, r, g, b, a = crack_ramp(style_cfg["color_ramp"])
        self.values = values
        self.components = {
            "red": r,
            "green": g,
            "blue": b,
            "alpha": a
        }
        for band in style_cfg["needed_bands"]:
            self.needed_bands.add(band)

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
                imgdata[band] *= 255
        imgdata = imgdata.astype("uint8")
        return imgdata


    def legend(self):
        # Use extents of ramp and transform_data based on that
        # take 100 steps between
        steps = numpy.linspace(self.values[0], self.values[-1], num=100)
        # pass all steps through transform data
        imgdata = Dataset()
        for band, intensity in self.components.items():
            imgdata[band] = (steps.dims, get_value(steps, self.values, intensity))


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
