from datetime import datetime
from textwrap import fill
import logging

import numpy
from colour import Color
from datacube.utils.masking import make_mask
from matplotlib import patches as mpatches, pyplot as plt
from xarray import Dataset, DataArray, merge

from datacube_ows.styles.base import StyleDefBase

_LOG = logging.getLogger(__name__)


class ColorMapStyleDef(StyleDefBase):
    auto_legend = True

    def __init__(self, product, style_cfg):
        super(ColorMapStyleDef, self).__init__(product, style_cfg)
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


    def transform_single_date_data(self, data):
        # pylint: disable=too-many-locals, too-many-branches
        # extent mask data per band to preseve nodata
        _LOG.debug("transform begin %s", datetime.now())
        #if extent_mask is not None:
        #    for band in data.data_vars:
        ##        try:
        #            data[band] = data[band].where(extent_mask, other=data[band].attrs['nodata'])
        #        except AttributeError:
        #            data[band] = data[band].where(extent_mask)

        imgdata = Dataset()
        for cfg_band, values in self.value_map.items():
            # Run through each item
            band = self.product.band_idx.band(cfg_band)
            band_data = Dataset()
            bdata = data[band]
            if bdata.dtype.kind == 'f':
                # Convert back to int for bitmasking
                bdata = ColorMapStyleDef.reint(bdata)
            for value in values:
                flags = value["flags"]
                rgb = Color(value["color"])
                alpha = value.get("alpha", 1.0)
                mask_source_band = value.get("mask", False)

                mask = ColorMapStyleDef.create_mask(bdata, flags)

                if mask_source_band:
                    # disable checking on the use of ~mask
                    # pylint: disable=invalid-unary-operand-type
                    bdata = bdata.where(~mask)
                    bdata = ColorMapStyleDef.reint(bdata)
                else:
                    masked = ColorMapStyleDef.create_colordata(bdata, rgb, alpha, mask)
                    band_data = masked if len(band_data.data_vars) == 0 else band_data.combine_first(masked)

            imgdata = band_data if len(imgdata.data_vars) == 0 else merge([imgdata, band_data])

        imgdata *= 255
        return imgdata.astype('uint8')

    def single_date_legend(self, bytesio):
        patches = []
        for band in self.value_map.keys():
            for value in self.value_map[band]:
                # only include values that have a title set
                if "title" in value and "abstract" in value and "color" in value and value["title"]:
                    rgb = Color(value["color"])
                    label = fill(value["title"] + " - " + value["abstract"], 30)
                    try:
                        patch = mpatches.Patch(color=rgb.hex_l, label=label)
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


StyleDefBase.register_subclass(ColorMapStyleDef, "value_map")
