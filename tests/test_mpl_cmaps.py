# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
"""
Test creation of colour maps from matplotlib
"""
from datacube_ows.ows_cfg_example import style_deform
from datacube_ows.styles.ramp import read_mpl_ramp


def test_get_mpl_cmap():
    matplotlib_ramp_name = style_deform['mpl_ramp']
    assert matplotlib_ramp_name
    ows_ramp_dict = read_mpl_ramp(matplotlib_ramp_name)
    assert len(ows_ramp_dict) == 11
    for cmap in ows_ramp_dict:
        assert "color" in cmap
        assert "value" in cmap
        assert cmap["color"].startswith("#")
        assert isinstance(cmap["value"], float)
