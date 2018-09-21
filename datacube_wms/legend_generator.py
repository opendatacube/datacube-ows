import datacube_wms.band_mapper as mapper
import logging
from datacube_wms.wms_layers import get_service_cfg, get_layers
from datacube_wms.wms_utils import GetLegendGraphicParameters
import matplotlib.pyplot as plt
import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap
import io
import numpy as np
from flask import make_response

_LOG = logging.getLogger(__name__)


def legend_graphic(args):
    params = GetLegendGraphicParameters(args)
    svc_cfg = get_service_cfg()
    if not params.style_name:
        product = params.product
        legend_config = product.legend
        if legend_config is not None:
            if legend_config.get('url', None):
                pass
            else:
                styles = [product.style_index[s] for s in legend_config.get('styles', [])]
                img = create_legends_from_styles(product, styles)
    return img


def create_legends_from_styles(product, styles):
    fig = plt.figure(figsize=(5,4))
    num_styles = len(styles)
    bdict = dict()
    # Run through all values in style cfg and generate
    for index, style in enumerate(styles):
        start, stop, cdict = style.legend()
        bar = dict()
        bar['ax'] = fig.add_axes([0.05, index * (1.0 / num_styles) + 0.3, 0.9, 0.15])

        bar['custom_map'] = LinearSegmentedColormap(product.name, cdict)

        bar['color_bar'] = mpl.colorbar.ColorbarBase(
            bar['ax'],
            cmap=bar['custom_map'],
            orientation="horizontal")
        bar['color_bar'].set_label(style.name)
        bdict[style.name] = bar

    b = io.BytesIO()
    plt.savefig(b, format='png')
    legend = make_response(b.getvalue())
    b.close()
    legend.mimetype = 'image/png'
    return legend
