# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import absolute_import

import io
import logging

import matplotlib
import numpy as np
# from flask import make_response
from PIL import Image

from datacube_ows.ogc_exceptions import WMSException
from datacube_ows.ogc_utils import resp_headers
from datacube_ows.wms_utils import GetLegendGraphicParameters

# Do not use X Server backend

matplotlib.use('Agg')

_LOG = logging.getLogger(__name__)


def legend_graphic(args):
    params = GetLegendGraphicParameters(args)
    img = create_legends_from_styles(params.styles,
                        ndates=len(params.times))
    if img is None:
        raise WMSException("No legend is available for this request", http_response=404)
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
        img = s.render_legend(ndates)
        if img is not None:
            imgs.append(img)

    if not imgs:
        return None
    min_shape = sorted([(np.sum(i.size), i.size) for i in imgs])[0][1]
    imgs_comb = np.vstack([np.asarray(i.resize(min_shape)) for i in imgs])
    imgs_comb = Image.fromarray(imgs_comb)
    b = io.BytesIO()
    imgs_comb.save(b, 'png')
    # legend = make_response(b.getvalue())
    # legend.mimetype = 'image/png'
    # b.close()
    return (b.getvalue(), 200, resp_headers({"Content-Type": "image/png"}))
