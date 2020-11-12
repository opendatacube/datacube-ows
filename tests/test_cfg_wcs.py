import math
import pytest
from unittest.mock import MagicMock, patch

from datacube_ows.ogc_utils import ConfigException
from datacube_ows.ows_configuration import parse_ows_layer, WCSFormat


def test_native_crs_mismatch(minimal_global_cfg, minimal_layer_cfg, minimal_dc):
    minimal_global_cfg.wcs = True
    minimal_layer_cfg["wcs"] = {
        "native_crs": "EPSG:1234",
        "default_bands": ["band1", "band2", "band3"],
    }
    minimal_layer_cfg["product_name"] = "foo_nativecrs"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    lyr.extract_bboxes = MagicMock()
    lyr.extract_bboxes.return_value = {
        "EPSG": {
            "top": 1,
            "bottom": -1,
            "left": -1,
            "right": 1,
        }
    }
    lyr.make_ready(minimal_dc)
    assert lyr.native_CRS == "EPSG:4326"


def test_native_crs_none(minimal_global_cfg, minimal_layer_cfg, minimal_dc, mock_range):
    minimal_global_cfg.wcs = True
    minimal_layer_cfg["wcs"] = {
        "default_bands": ["band1", "band2"]
    }
    minimal_layer_cfg["product_name"] = "foo_nonativecrs"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        with pytest.raises(ConfigException) as excinfo:
            lyr.make_ready(minimal_dc)
    assert "a_layer" in str(excinfo.value)
    assert "No native CRS" in str(excinfo.value)


def test_native_crs_unpublished(minimal_global_cfg, minimal_layer_cfg, minimal_dc):
    minimal_global_cfg.wcs = True
    minimal_layer_cfg["wcs"] = {
        "default_bands": ["band1", "band2", "band3"],
    }
    minimal_layer_cfg["product_name"] = "foo_badnativecrs"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    lyr.extract_bboxes = MagicMock()
    lyr.extract_bboxes.return_value = {
        "EPSG": {
            "top": 1,
            "bottom": -1,
            "left": -1,
            "right": 1,
        }
    }
    with pytest.raises(ConfigException) as excinfo:
        lyr.make_ready(minimal_dc)
    assert "EPSG:9999" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)
    assert "not in published CRSs" in str(excinfo.value)


def test_no_native_resolution(minimal_global_cfg, minimal_layer_cfg, minimal_dc, mock_range):
    minimal_global_cfg.wcs = True
    minimal_layer_cfg["wcs"] = {
        "native_crs": "EPSG:4326",
        "default_bands": ["band1", "band2", "band3"],
    }
    minimal_layer_cfg["product_name"] = "foo_nonativeres"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        with pytest.raises(ConfigException) as excinfo:
            lyr.make_ready(minimal_dc)
    assert "a_layer" in str(excinfo.value)
    assert "No native resolution" in str(excinfo.value)


def test_no_native_resolution_noniter(minimal_global_cfg, minimal_layer_cfg, minimal_dc, mock_range):
    minimal_global_cfg.wcs = True
    minimal_layer_cfg["wcs"] = {
        "native_crs": "EPSG:4326",
        "default_bands": ["band1", "band2", "band3"],
        "native_resolution": 45,
    }
    minimal_layer_cfg["product_name"] = "foo_nonativeres"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        with pytest.raises(ConfigException) as excinfo:
            lyr.make_ready(minimal_dc)
    assert "a_layer" in str(excinfo.value)
    assert "Invalid native resolution" in str(excinfo.value)


def test_no_native_resolution_badlen(minimal_global_cfg, minimal_layer_cfg, minimal_dc, mock_range):
    minimal_global_cfg.wcs = True
    minimal_layer_cfg["wcs"] = {
        "native_crs": "EPSG:4326",
        "default_bands": ["band1", "band2", "band3"],
        "native_resolution": [33,45,2234],
    }
    minimal_layer_cfg["product_name"] = "foo_nonativeres"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        with pytest.raises(ConfigException) as excinfo:
            lyr.make_ready(minimal_dc)
    assert "a_layer" in str(excinfo.value)
    assert "Invalid native resolution" in str(excinfo.value)


def test_native_resolution_mismatch(minimal_global_cfg, minimal_layer_cfg, minimal_dc, mock_range):
    minimal_global_cfg.wcs = True
    minimal_layer_cfg["wcs"] = {
        "native_crs": "EPSG:4326",
        "default_bands": ["band1", "band2", "band3"],
        "native_resolution": [0.1, 0.1],
    }
    minimal_layer_cfg["product_name"] = "foo_nativeres"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        lyr.make_ready(minimal_dc)
    assert not lyr.hide
    assert lyr.ready
    assert math.isclose(lyr.resolution_x, 0.001, rel_tol=1e-8)
    assert math.isclose(lyr.resolution_y, 0.001, rel_tol=1e-8)


def test_zero_grid(minimal_global_cfg, minimal_layer_cfg, minimal_dc, mock_range):
    minimal_global_cfg.wcs = True
    minimal_layer_cfg["wcs"] = {
        "native_crs": "EPSG:4326",
        "default_bands": ["band1", "band2", "band3"],
    }
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
    assert "Grid High y is zero" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)
    assert "EPSG:4326" in str(excinfo.value)
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
    assert "Grid High x is zero" in str(excinfo.value)
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