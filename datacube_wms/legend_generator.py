import datacube_wms.band_mapper as mapper
import logging
from datacube_wms.wms_layers import get_service_cfg, get_layers
from datacube_wms.wms_utils import GetLegendGraphicParameters
import io
from PIL import Image
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
    # Run through all values in style cfg and generate
    imgs = [Image.open(io.BytesIO(s.legend())) for s in styles]

    min_shape = sorted([(np.sum(i.size), i.size ) for i in imgs])[0][1]
    imgs_comb = np.vstack((np.asarray( i.resize(min_shape)) for i in imgs ))
    imgs_comb = Image.fromarray(imgs_comb)
    b = io.BytesIO()
    imgs_comb.save(b, 'png')
    legend = make_response(b.getvalue())
    legend.mimetype = 'image/png'
    b.close()
    return legend
