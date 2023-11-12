# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from unittest.mock import patch

import pytest

from datacube_ows.ogc_utils import ConfigException
from datacube_ows.ows_configuration import WCSFormat, parse_ows_layer


def test_zero_grid(minimal_global_cfg, minimal_layer_cfg, minimal_dc, mock_range):
    minimal_global_cfg.wcs = True
    minimal_layer_cfg["native_crs"] = "EPSG:4326"
    minimal_layer_cfg["product_name"] = "foo_nativeres"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    mock_range["bboxes"]["EPSG:4326"] = {
        "top": 0.1, "bottom": 0.1,
        "left": -0.1, "right": 0.1,
    }
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        with pytest.raises(ConfigException) as excinfo:
            lyr.make_ready(minimal_dc)
    assert not lyr.ready
    assert "Grid High y is non-positive" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)
    assert "EPSG:4326" in str(excinfo.value)
    minimal_global_cfg.product_index = {}
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    mock_range["bboxes"]["EPSG:4326"] = {
        "top": 0.1, "bottom": -0.1,
        "left": -0.1, "right": -0.1,
    }
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        with pytest.raises(ConfigException) as excinfo:
            lyr.make_ready(minimal_dc)
    assert "Grid High x is non-positive" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)
    assert "EPSG:4326" in str(excinfo.value)


def test_wcs_renderer_detection():
    fmt = WCSFormat(
        "GeoTIFF",
        "image/geotiff",
        "tif",
        {
            "1": "datacube_ows.wcs1_utils.get_tiff",
            "2": "datacube_ows.wcs2_utils.get_tiff",
        },
        False
    )
    r = fmt.renderer("2.1.0")
    assert r == fmt.renderers[2]
