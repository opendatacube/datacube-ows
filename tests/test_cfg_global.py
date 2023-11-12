# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import pytest

from datacube_ows.ogc_utils import ConfigException
from datacube_ows.ows_configuration import ContactInfo, OWSConfig


def test_minimal_global(minimal_global_raw_cfg, minimal_dc):
    OWSConfig._instance = None
    cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    cfg.make_ready(minimal_dc)
    assert cfg.ready
    assert cfg.initialised
    assert not cfg.wcs_tiff_statistics
    assert cfg.default_geographic_CRS == "" # No WCS


def test_global_no_title(minimal_global_raw_cfg):
    OWSConfig._instance = None
    del minimal_global_raw_cfg["global"]["title"]
    with pytest.raises(ConfigException) as excinfo:
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "Entity global has no title" in str(excinfo.value)


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
    assert cfg.wcs_tiff_statistics
    assert cfg.default_geographic_CRS == "urn:ogc:def:crs:OGC:1.3:CRS84"

def test_geog_crs(minimal_global_raw_cfg, wcs_global_cfg, minimal_dc):
    OWSConfig._instance = None
    minimal_global_raw_cfg["global"]["services"] = {
        "wcs": True,
        "wms": False,
        "wmts": False,
    }
    minimal_global_raw_cfg["wcs"] = wcs_global_cfg
    minimal_global_raw_cfg["global"]["published_CRSs"] = {
        "EPSG:3857": {  # Web Mercator
            "geographic": False,
            "horizontal_coord": "x",
            "vertical_coord": "y",
        },
    }
    with pytest.raises(ConfigException) as e:
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "At least one geographic CRS must be supplied" in str(e.value)
    OWSConfig._instance = None
    minimal_global_raw_cfg["global"]["published_CRSs"] = {
        "EPSG:3857": {  # Web Mercator
            "geographic": False,
            "horizontal_coord": "x",
            "vertical_coord": "y",
        },
        "EPSG:99899": {  # Made up
            "geographic": True,
            "horizontal_coord": "longitude",
            "vertical_coord": "latitude",
        },
    }
    cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    cfg.make_ready(minimal_dc)
    assert cfg.default_geographic_CRS == "EPSG:99899"


def test_contact_details_parse(minimal_global_cfg):
    addr1 = ContactInfo.parse({}, minimal_global_cfg)
    assert addr1 is None
    addr2 = ContactInfo.parse({"address": {}}, minimal_global_cfg)
    assert addr2.address is None
    addr3 = ContactInfo.parse({"address": {"address": "foo"}}, minimal_global_cfg)
    assert addr3.address.address == "foo"


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
    OWSConfig._instance = None
    minimal_global_raw_cfg["global"]["services"] = {
        "wms": False,
        "wmts": False,
    }
    with pytest.raises(ConfigException) as excinfo:
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "At least one service must be active" in str(excinfo.value)


def test_no_published_crss(minimal_global_raw_cfg):
    del minimal_global_raw_cfg["global"]["published_CRSs"]
    with pytest.raises(ConfigException) as e:
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "Missing required config entry in 'global' section:" in str(e.value)
    assert "published_CRSs" in str(e.value)


def test_bad_geographic_crs(minimal_global_raw_cfg):
    OWSConfig._instance = None
    minimal_global_raw_cfg["global"]["published_CRSs"]["EPSG:7777"] = {
        "geographic": True,
        "horizontal_coord": "x"
    }
    with pytest.raises(ConfigException) as excinfo:
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "is geographic" in str(excinfo.value)
    assert "EPSG:7777" in str(excinfo.value)
    assert "horizontal" in str(excinfo.value)
    assert "longitude" in str(excinfo.value)
    OWSConfig._instance = None
    minimal_global_raw_cfg["global"]["published_CRSs"]["EPSG:7777"] = {
        "geographic": True,
        "vertical_coord": "y"
    }
    with pytest.raises(ConfigException) as excinfo:
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "is geographic" in str(excinfo.value)
    assert "EPSG:7777" in str(excinfo.value)
    assert "latitude" in str(excinfo.value)
    assert "vertical" in str(excinfo.value)


def test_bad_crs_alias(minimal_global_raw_cfg):
    OWSConfig._instance = None
    minimal_global_raw_cfg["global"]["published_CRSs"]["EPSG:7777"] = {
        "alias": "EPSG:6666",
    }
    cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "EPSG:7777" not in cfg.published_CRSs


def test_no_wcs(minimal_global_raw_cfg):
    OWSConfig._instance = None
    minimal_global_raw_cfg["global"]["services"] = {"wcs": True}
    with pytest.raises(ConfigException) as excinfo:
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "WCS section missing" in str(excinfo.value)
    assert "WCS is enabled" in str(excinfo.value)


def test_no_wcs_formats(minimal_global_raw_cfg):
    OWSConfig._instance = None
    minimal_global_raw_cfg["global"]["services"] = {"wcs": True}
    minimal_global_raw_cfg["wcs"] = {
        "formats": {}
    }
    with pytest.raises(ConfigException) as excinfo:
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "Must configure at least one wcs format" in str(excinfo.value)


def test_bad_wcs_format(minimal_global_raw_cfg, wcs_global_cfg):
    OWSConfig._instance = None
    minimal_global_raw_cfg["global"]["services"] = {"wcs": True}
    minimal_global_raw_cfg["wcs"] = wcs_global_cfg
    minimal_global_raw_cfg["wcs"]["native_format"] = "jpeg2000"
    with pytest.raises(ConfigException) as excinfo:
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "Configured native WCS format" in str(excinfo.value)
    assert "jpeg2000" in str(excinfo.value)
    assert "not a supported format" in str(excinfo.value)


def test_tiff_stats(minimal_global_raw_cfg, wcs_global_cfg):
    OWSConfig._instance = None
    minimal_global_raw_cfg["global"]["services"] = {"wcs": True}
    minimal_global_raw_cfg["wcs"] = wcs_global_cfg
    minimal_global_raw_cfg["wcs"]["calculate_tiff_statistics"] = False
    cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert not cfg.wcs_tiff_statistics

def test_crs_lookup_fail(minimal_global_raw_cfg, minimal_dc):
    OWSConfig._instance = None
    cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    with pytest.raises(ConfigException) as excinfo:
        crs = cfg.crs("EPSG:111")
    assert "EPSG:111" in str(excinfo.value)
    assert "is not published" in str(excinfo.value)


def test_no_langs(minimal_global_raw_cfg, minimal_dc):
    OWSConfig._instance = None
    minimal_global_raw_cfg["global"]["supported_languages"] = []
    with pytest.raises(ConfigException) as excinfo:
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "at least one language" in str(excinfo.value)


def test_two_langs(minimal_global_raw_cfg, minimal_dc):
    OWSConfig._instance = None
    minimal_global_raw_cfg["global"]["supported_languages"] = ["fr", "en"]
    cfg = OWSConfig(cfg=minimal_global_raw_cfg)

    assert cfg.global_config().default_locale == 'fr'
    assert len(cfg.global_config().locales) == 2
    assert not cfg.global_config().internationalised


def test_internationalised(minimal_global_raw_cfg, minimal_dc):
    OWSConfig._instance = None

    minimal_global_raw_cfg["global"]["supported_languages"] = ["fr", "en"]
    minimal_global_raw_cfg["global"]["translations_directory"] = "/integration_tests/cfg/translations" # no need to be valid
    cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert cfg.global_config().internationalised


def test_bad_integers_in_wms_section(minimal_global_raw_cfg, minimal_dc):
    minimal_global_raw_cfg["wms"] = {}
    minimal_global_raw_cfg["wms"]["max_width"] = "very big"
    with pytest.raises(ConfigException) as e:
        OWSConfig._instance = None
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "max_width and max_height in wms section must be integers" in str(e.value)
    assert "very big" in str(e.value)
    minimal_global_raw_cfg["wms"]["max_width"] = 0
    with pytest.raises(ConfigException) as e:
        OWSConfig._instance = None
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "max_width and max_height in wms section must be positive integers" in str(e.value)
    assert "0" in str(e.value)
    minimal_global_raw_cfg["wms"]["max_width"] = 256
    minimal_global_raw_cfg["wms"]["caps_cache_maxage"] = "forever"
    with pytest.raises(ConfigException) as e:
        OWSConfig._instance = None
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "caps_cache_maxage in wms section must be an integer" in str(e.value)
    assert "forever" in str(e.value)
    minimal_global_raw_cfg["wms"]["caps_cache_maxage"] = -100
    with pytest.raises(ConfigException) as e:
        OWSConfig._instance = None
        cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    assert "caps_cache_maxage in wms section cannot be negative" in str(e.value)
    assert "-100" in str(e.value)
