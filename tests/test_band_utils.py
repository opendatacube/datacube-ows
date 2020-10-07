"""Test band math utilities
"""
import pytest
import numpy as np
import xarray as xr

from datacube_ows.band_utils import (
    scale_data,
    sum_bands,
    norm_diff,
    constant,
    single_band,
    band_quotient,
    band_quotient_sum,
    single_band_log,
    sentinel2_ndci,
    multi_date_delta,
    single_band_offset_log,
    single_band_arcsec,
)
from datacube_ows.ows_configuration import BandIndex, OWSProductLayer


class MockArray(xr.DataArray):
    __slots__ = ("nodata",)

    def __init__(
        self,
        data,
        coords=None,
        dims=None,
        name=None,
        attrs=None,
        indexes=None,
        fastpath=None,
    ):
        super().__init__(data, coords, dims, name, attrs, indexes, fastpath)
        self.nodata = 0


TEST_ARR_1 = MockArray(np.ones((100, 100), dtype=np.uint32), attrs={"nodata": 0})
TEST_ARR_2 = MockArray(np.ones((100, 100), dtype=np.uint32), attrs={"nodata": 0})
TEST_XARR = {"b1": TEST_ARR_1, "b2": TEST_ARR_2}

TEST_XARR_T = xr.Dataset({"b1": (["x", "y", "time"], np.ones((100, 100, 2)))})


@pytest.fixture
def dummy_layer():
    product_layer = OWSProductLayer.__new__(OWSProductLayer)
    product_layer.name = "test_product"
    product_layer.band_idx = BandIndex.__new__(BandIndex)
    product_layer.band_idx._idx = {"b1": "b1", "b2": "b2"}
    return product_layer

@pytest.fixture
def band_mapper():
    idx = {
        "b1": "b1",
        "b2": "b2",
        "b1a": "b1",
        "b2a": "b2",
    }
    return lambda b: idx[b]


def test_scale_data():
    assert not scale_data(TEST_ARR_1, [0.0, 1.0], [0.0, 1.0]) is None


def test_sum_bands():
    assert not sum_bands(TEST_XARR, "b1", "b2") is None


def test_norm_diff(band_mapper):
    assert not norm_diff(TEST_XARR, "b1", "b2") is None
    assert not norm_diff(TEST_XARR, "b1a", "b2", band_mapper, scale_from=[0, 1]) is None


def test_constant(band_mapper):
    assert not constant(TEST_XARR, "b1", 10) is None
    assert not constant(TEST_XARR, "b1a", 10, band_mapper) is None


def test_band_quotient(band_mapper):
    assert not band_quotient(TEST_XARR, "b1", "b2") is None
    assert not band_quotient(TEST_XARR, "b1", "b2", band_mapper) is None


def test_band_quotient_sum():
    assert not band_quotient_sum(TEST_XARR, "b1", "b2", "b1", "b2") is None


def test_single_band_log(band_mapper):
    assert not single_band_log(TEST_XARR, "b1", 1.0, 1.0) is None
    assert not single_band_log(TEST_XARR, "b1", 1.0, 1.0, band_mapper) is None


def test_single_band(band_mapper):
    assert not single_band(TEST_XARR, "b1") is None
    assert not single_band(TEST_XARR, "b1", band_mapper) is None

def test_multidate():
    assert not multi_date_delta(TEST_XARR_T) is None


def test_ndci():
    assert not sentinel2_ndci(TEST_XARR, "b1", "b2", "b1", "b2") is None


def test_single_band_offset_log(band_mapper):
    assert not single_band_offset_log(TEST_XARR, "b1") is None
    assert not single_band_offset_log(TEST_XARR, "b1", offset=0.5) is None
    assert not single_band_offset_log(TEST_XARR, "b1", scale=100) is None
    assert not single_band_offset_log(TEST_XARR, "b1", scale_from=[0.0, 4.0]) is None
    assert not single_band_offset_log(TEST_XARR, "b1", scale_from=[0.0, 4.0], scale_to=[0, 1024]) is None
    assert not single_band_offset_log(TEST_XARR, "b1", band_mapper=band_mapper) is None


def test_single_band_arcsec(band_mapper):
    assert not single_band_arcsec(TEST_XARR, "b1") is None
    assert not single_band_arcsec(TEST_XARR, "b1", scale_from=[0.0, 0.8]) is None
    assert not single_band_arcsec(TEST_XARR, "b1", scale_from=[0.0, 0.8], scale_to=[0, 1024]) is None
    assert not single_band_arcsec(TEST_XARR, "b1", band_mapper=band_mapper) is None
