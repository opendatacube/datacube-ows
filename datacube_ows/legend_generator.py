from __future__ import absolute_import

import logging
from datacube_ows.wms_utils import GetLegendGraphicParameters
import io
from PIL import Image
import numpy as np
from flask import make_response
import requests

_LOG = logging.getLogger(__name__)


def legend_graphic(args):
    params = GetLegendGraphicParameters(args)
    img = None
    product = params.product
    style = params.style_name
    legend_config = getattr(product, 'legend', None)
    if legend_config is not None:
        if legend_config.get('url', None):
            img_url = legend_config.get('url')
            r = requests.get(img_url, timeout=1)
            if r.status_code == 200 and r.headers['content-type'] == 'image/png':
                img = make_response(r.content)
                img.mimetype = 'image/png'
        elif legend_config.get('styles', []):
            if style in legend_config.get('styles', []):
                img = create_legends_from_styles([style])
            elif set(legend_config.get('styles', [])) == set(product.style_index.keys()):
                # We want all the styles, and all the styles have legends
                styles = [product.style_index[s] for s in legend_config.get('styles', [])]
                img = create_legends_from_styles(styles)
    return img


def create_legend_for_style(product, style_name):
    if style_name not in product.style_index:
        return None
    style = product.style_index[style_name]
    return create_legends_from_styles([style])


def create_legends_from_styles(styles):
    # Run through all values in style cfg and generate
    imgs = []
    for s in styles:
        url = s.legend_override_with_url()
        if url:
            img = get_image_from_url(url)
            if img:
                imgs.append(img)
        else:
            bytesio = io.BytesIO()
            s.legend(bytesio)
            bytesio.seek(0)
            imgs.append(Image.open(bytesio))

    min_shape = sorted([(np.sum(i.size), i.size) for i in imgs])[0][1]
    imgs_comb = np.vstack((np.asarray(i.resize(min_shape)) for i in imgs))
    imgs_comb = Image.fromarray(imgs_comb)
    b = io.BytesIO()
    imgs_comb.save(b, 'png')
    legend = make_response(b.getvalue())
    legend.mimetype = 'image/png'
    b.close()
    return legend


def get_image_from_url(url):
    r = requests.get(url, timeout=1)
    if r.status_code == 200 and r.headers['content-type'] == 'image/png':
        bytesio = io.BytesIO()
        bytesio.write(r.content)
        bytesio.seek(0)
        return Image.open(bytesio)
    return None
