# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from unittest.mock import MagicMock

import pytest

from datacube_ows.ogc_utils import ConfigException
from datacube_ows.ows_configuration import AttributionCfg, SuppURL


def test_cfg_attrib_empty(minimal_owner):
    attrib = AttributionCfg.parse({}, minimal_owner)
    assert attrib is None

@pytest.fixture
def minimal_owner():
    owner = MagicMock()
    owner.attribution_title = None
    return owner

@pytest.fixture
def owner_w_attrib_title():
    owner = MagicMock()
    owner.attribution_title = "Sir"
    return owner

def test_cfg_attrib_emptyfail(minimal_owner):
    with pytest.raises(ConfigException) as excinfo:
        attrib = AttributionCfg.parse({"foo": "bar"}, minimal_owner)
    assert "At least one" in str(excinfo.value)


def test_cfg_attrib_title_only(owner_w_attrib_title):
    attrib = AttributionCfg.parse({
        "title": "Sir"
    }, owner_w_attrib_title)
    assert attrib.title == "Sir"
    assert attrib.get("title") == "Sir"
    assert attrib.logo_width is None
    assert attrib.url is None


def test_cfg_attrib_url_only(minimal_owner):
    attrib = AttributionCfg.parse({
        "url": "http://test.url/path/name",
    }, minimal_owner)
    assert attrib.title is None
    assert attrib.logo_width is None
    assert attrib.url == "http://test.url/path/name"


def test_cfg_attrib_minimal_logo_only(minimal_owner):
    attrib = AttributionCfg.parse({
        "logo": {
            "url": "http://test.url/path/img.png",
            "format": "image/png"
        }
    }, minimal_owner)
    assert attrib.title is None
    assert attrib.url is None
    assert attrib.logo_url == "http://test.url/path/img.png"
    assert attrib.logo_fmt == "image/png"
    assert attrib.logo_width is None


def test_cfg_attrib_logo_requirements(minimal_owner):
    with pytest.raises(ConfigException) as excinfo:
        attrib = AttributionCfg.parse({
            "logo": {
                "url": "http://test.url/path/img.png",
            }
        }, minimal_owner)
    assert "url and format" in str(excinfo.value)
    with pytest.raises(ConfigException) as excinfo:
        attrib = AttributionCfg.parse({
            "logo": {
                "format": "image/png"
            }
        }, minimal_owner)
    assert "url and format" in str(excinfo.value)


def test_cfg_attrib_logo_options(minimal_owner):
    attrib = AttributionCfg.parse({
        "logo": {
            "url": "http://test.url/path/img.png",
            "format": "image/png",
            "width": 200
        }
    }, minimal_owner)
    assert attrib.logo_url == "http://test.url/path/img.png"
    assert attrib.logo_fmt == "image/png"
    assert attrib.logo_width == 200
    assert attrib.logo_height is None
    attrib = AttributionCfg.parse({
        "logo": {
            "url": "http://test.url/path/img.png",
            "format": "image/png",
            "width": 200,
            "height": 300
        }
    }, minimal_owner)
    assert attrib.logo_height == 300


def test_cfg_attrib_all_flds(minimal_dc, owner_w_attrib_title):
    attrib = AttributionCfg.parse({
        "title": "Sir",
        "url": "http://test.url/path",
        "logo": {
            "url": "http://test.url/path/img.png",
            "format": "image/png",
            "width": 200,
            "height": 150,
        }
    }, owner_w_attrib_title)
    assert attrib.title == "Sir"
    assert attrib.url == "http://test.url/path"
    assert attrib.logo_url == "http://test.url/path/img.png"
    assert attrib.logo_fmt == "image/png"
    assert attrib.logo_width == 200
    assert attrib.logo_height == 150
    attrib.make_ready(minimal_dc)
    assert attrib.ready


def test_surl_empty():
    supps = SuppURL.parse_list(None)
    assert supps == []
    supps = SuppURL.parse_list([])
    assert supps == []


def test_surl_no_url():
    with pytest.raises(KeyError):
        supps = SuppURL.parse_list([
            {
                "format": "text/html"
            }
        ])


def test_surl_no_format():
    with pytest.raises(KeyError):
        supps = SuppURL.parse_list([
            {
                "url": "http://test.url/path"
            }
        ])


def test_surl_full(minimal_dc):
    supps = SuppURL.parse_list([
        {
            "url": "http://test.url/path",
            "format": "text/html"
        },
        {
            "url": "http://test.url/another_path",
            "format": "text/plain"
        },
    ])
    assert len(supps) == 2
    assert supps[0].url == "http://test.url/path"
    assert supps[1].url == "http://test.url/another_path"
    assert supps[0].format == "text/html"
    assert supps[1].format == "text/plain"
    supps[0].make_ready(minimal_dc)
    assert supps[0].ready
    assert not supps[1].ready
