from unittest.mock import MagicMock

import pytest

from datacube_ows.ogc_exceptions import WCS2Exception
from datacube_ows.wcs2_utils import uniform_crs


@pytest.fixture
def minimal_cfg():
    cfg = MagicMock()
    cfg.published_CRSs = {
        "dummy": {},
    }
    return cfg

def test_uniform_crs_url(minimal_cfg):
    crs = uniform_crs(minimal_cfg, "http://www.opengis.net/def/crs/EPSG/666")
    assert crs == "EPSG:666"

def test_uniform_crs_urn(minimal_cfg):
    crs = uniform_crs(minimal_cfg, "urn:ogc:def:crs:EPSG:666")
    assert crs == "EPSG:666"

def test_uniform_crs_epsg(minimal_cfg):
    crs = uniform_crs(minimal_cfg, "EPSG:666")
    assert crs == "EPSG:666"

def test_uniform_crs_published(minimal_cfg):
    crs = uniform_crs(minimal_cfg, "dummy")
    assert crs == "dummy"

def test_uniform_crs_published(minimal_cfg):
    with pytest.raises(WCS2Exception) as e:
        crs = uniform_crs(minimal_cfg, "spam")
    assert "spam" in str(e.value)
    assert "Not a CRS" in str(e.value)

