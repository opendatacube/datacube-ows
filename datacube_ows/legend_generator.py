from __future__ import absolute_import

import logging
from collections import defaultdict
from math import isclose

from datacube_ows.ogc_exceptions import WMSException
from datacube_ows.wms_utils import GetLegendGraphicParameters
import io
from PIL import Image
import numpy as np
from flask import make_response
import requests

import matplotlib
# Do not use X Server backend

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap


_LOG = logging.getLogger(__name__)


def legend_graphic(args):
    params = GetLegendGraphicParameters(args)
    img = create_legends_from_styles(params.styles,
                        ndates=len(params.times))
    if img is None:
        raise WMSException("No legend is available for this request")
    return img


def create_legend_for_style(product, style_name, ndates=0):
    if style_name not in product.style_index:
        return None
    style = product.style_index[style_name]
    return create_legends_from_styles([style], ndates)


def create_legends_from_styles(styles, ndates=0):
    # Run through all values in style cfg and generate
    imgs = []
    for s in styles:
        url = s.legend_override_with_url()
        if url:
            img = get_image_from_url(url)
            if img:
                imgs.append(img)
        elif not s.auto_legend:
            raise WMSException(f"Style {s.name} does not have a legend.")
        else:
            if ndates in [0,1]:
                bytesio = io.BytesIO()
                s.single_date_legend(bytesio)
                bytesio.seek(0)
                imgs.append(Image.open(bytesio))
            for mdh in s.multi_date_handlers:
                if ndates == 0 or mdh.applies_to(ndates):
                    bytesio = io.BytesIO()
                    if mdh.legend(bytesio):
                        bytesio.seek(0)
                        imgs.append(Image.open(bytesio))

    if not imgs:
        return None
    min_shape = sorted([(np.sum(i.size), i.size) for i in imgs])[0][1]
    imgs_comb = np.vstack([np.asarray(i.resize(min_shape)) for i in imgs])
    imgs_comb = Image.fromarray(imgs_comb)
    b = io.BytesIO()
    imgs_comb.save(b, 'png')
    legend = make_response(b.getvalue())
    legend.mimetype = 'image/png'
    b.close()
    return legend


def get_image_from_url(url):
    foo = requests.get
    r = requests.get(url, timeout=1)
    if r.status_code == 200 and r.headers['content-type'] == 'image/png':
        bytesio = io.BytesIO()
        bytesio.write(r.content)
        bytesio.seek(0)
        return Image.open(bytesio)
    return None


