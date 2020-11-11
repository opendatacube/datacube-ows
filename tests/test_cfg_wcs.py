import pytest
from unittest.mock import MagicMock, patch

from datacube_ows.ogc_utils import ConfigException
from datacube_ows.ows_configuration import OWSLayer, OWSFolder, parse_ows_layer


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

