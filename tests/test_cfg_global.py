# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
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


def test_crs_lookup_fail(minimal_global_raw_cfg, minimal_dc):
    OWSConfig._instance = None
    cfg = OWSConfig(cfg=minimal_global_raw_cfg)
    with pytest.raises(ConfigException) as excinfo:
        crs = cfg.crs("EPSG:111")
    assert "EPSG:111" in str(excinfo.value)
    assert "is not published" in str(excinfo.value)
