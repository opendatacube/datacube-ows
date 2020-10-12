import pytest
from unittest.mock import patch, MagicMock

from datacube_ows.config_utils import OWSConfigNotReady
from datacube_ows.ogc_utils import ConfigException
from datacube_ows.ows_configuration import BandIndex


@pytest.fixture
def minimal_prod():
    product = MagicMock()
    product.name = "foo"
    return product


def test_bidx_p_minimal(minimal_prod):
    bidx = BandIndex(minimal_prod, None)
    assert bidx.product_name == "foo"
    assert bidx.band_cfg == {}
    assert bidx._idx == {}
    assert not bidx.ready


def test_bidx_p_unready(minimal_prod):
    bidx = BandIndex(minimal_prod, {
        "foo": ["foo"]
    })
    with pytest.raises(OWSConfigNotReady) as excinfo:
        x = bidx.native_bands
    assert "native_bands" in str(excinfo.value)
    with pytest.raises(OWSConfigNotReady) as excinfo:
        x = bidx.nodata_val("foo")
    assert "_nodata_vals" in str(excinfo.value)

def test_bidx_p_duplicates(minimal_prod):
    with pytest.raises(ConfigException) as excinfo:
        bidx = BandIndex(minimal_prod, {
            "foo": ["bar"],
            "bar": ["baz"]
        })
    assert "Duplicate band name/alias" in str(excinfo.value)
    assert "bar" in str(excinfo.value)
    with pytest.raises(ConfigException) as excinfo:
        bidx = BandIndex(minimal_prod, {
            "foo": ["bar"],
            "boo": ["bar"]
        })
    assert "Duplicate band name/alias" in str(excinfo.value)
    assert "bar" in str(excinfo.value)

def test_bidx_p_band(minimal_prod):
    bidx = BandIndex(minimal_prod, {
        "foo": ["bar", "baz"],
    })
    assert bidx.band("foo") == "foo"
    assert bidx.band("bar") == "foo"
    assert bidx.band("baz") == "foo"
    with pytest.raises(ConfigException) as excinfo:
        bidx.band_label("splat")
    assert "Unknown band name/alias" in str(excinfo.value)
    assert "splat" in str(excinfo.value)

def test_bidx_p_band_labels(minimal_prod):
    bidx = BandIndex(minimal_prod, {
        "foo": ["bar", "foo", "baz"],
        "zing": ["pow", "splat"],
        "oof": [],
    })
    bls = bidx.band_labels()
    assert "bar" in bls
    assert "pow" in bls
    assert "oof" in bls
    assert len(bls) == 3

def test_bidx_p_label(minimal_prod):
    bidx = BandIndex(minimal_prod, {
        "foo": ["bar", "baz"],
    })
    assert bidx.band_label("foo") == "bar"
    assert bidx.band_label("bar") == "bar"
    assert bidx.band_label("baz") == "bar"
    with pytest.raises(ConfigException) as excinfo:
        bidx.band_label("splat")
    assert "Unknown band name/alias" in str(excinfo.value)
    assert "splat" in str(excinfo.value)


@pytest.fixture
def minimal_dc():
    dc = MagicMock()
    nb = MagicMock()
    nb.index = ['band1', 'band2', 'band3', 'band4']
    nb.__getitem__.return_value = {
        "band1": -999,
        "band2": -999,
        "band3": -999,
        "band4": -999,
    }
    dc.list_measurements().loc = {
        "foo": nb
    }
    return dc


def test_bidx_makeready(minimal_prod, minimal_dc):
    bidx = BandIndex(minimal_prod, None)
    bidx.make_ready(minimal_dc)
    assert bidx.band("band1") == "band1"
    assert bidx.nodata_val("band1") == -999

