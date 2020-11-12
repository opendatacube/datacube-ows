import pytest
from unittest.mock import MagicMock, patch
from datacube_ows.ogc_utils import ConfigException
from datacube_ows.ows_configuration import OWSConfig


def test_minimal_global(minimal_global_raw_cfg, minimal_dc):
    OWSConfig._instance = None
    cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    cfg.make_ready(minimal_dc)
    assert cfg.ready


def test_global_no_title(minimal_global_raw_cfg):
    OWSConfig._instance = None
    del minimal_global_raw_cfg["global"]["title"]
    with pytest.raises(ConfigException) as excinfo:
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "title" in str(excinfo.value)
    assert "Missing required config entry" in str(excinfo.value)
    assert "global" in str(excinfo.value)

def test_wcs_only(minimal_global_raw_cfg, wcs_global_cfg, minimal_dc):
    OWSConfig._instance = None
    minimal_global_raw_cfg["global"]["services"] = {
        "wcs": True,
        "wms": False,
        "wmts": False,
    }
    minimal_global_raw_cfg["wcs"] = wcs_global_cfg
    cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    cfg.make_ready(minimal_dc)
    assert cfg.ready
    assert cfg.wcs
    assert not cfg.wms
    assert not cfg.wmts

def test_wcs_no_native_format(minimal_global_raw_cfg, wcs_global_cfg):
    OWSConfig._instance = None
    minimal_global_raw_cfg["global"]["services"] = {
        "wcs": True,
        "wms": False,
        "wmts": False,
    }
    del wcs_global_cfg["native_format"]
    minimal_global_raw_cfg["wcs"] = wcs_global_cfg
    with pytest.raises(ConfigException) as excinfo:
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "native_format" in str(excinfo.value)
    assert "Missing required config entry" in str(excinfo.value)
    assert "wcs" in str(excinfo.value)

def test_no_services(minimal_global_raw_cfg):
    minimal_global_raw_cfg["global"]["services"] = {
        "wms": False,
        "wmts": False,
    }
    with pytest.raises(ConfigException) as excinfo:
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "At least one service must be active" in str(excinfo.value)