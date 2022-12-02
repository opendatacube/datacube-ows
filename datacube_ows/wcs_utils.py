# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from datacube_ows.ogc_exceptions import WCS1Exception, WCS2Exception


def get_bands_from_styles(styles, layer, version=1):
    styles = styles.split(",")
    if len(styles) != 1:
        if version == 1:
            raise WCS1Exception("Multiple style parameters not supported")
        else:
            raise WCS2Exception("Multiple style parameters not supported")
    style = layer.style_index.get(styles[0])
    bands = set()
    if style:
        for b in style.needed_bands:
            if b not in style.flag_bands:
                bands.add(b)
    return bands
