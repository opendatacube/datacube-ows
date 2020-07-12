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
)


class MockArray(xr.DataArray):
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


def test_scale_data():
    assert not scale_data(TEST_ARR_1, [0.0, 1.0], [0.0, 1.0]) is None


def test_sum_bands():
    assert not sum_bands(TEST_XARR, "b1", "b2") is None


def test_norm_diff():
    assert not norm_diff(TEST_XARR, "b1", "b2") is None


def test_constant():
    assert not constant(TEST_XARR, "b1", 10) is None


def test_band_quotient():
    assert not band_quotient(TEST_XARR, "b1", "b2") is None


def test_band_quotient_sum():
    assert not band_quotient_sum(TEST_XARR, "b1", "b2", "b1", "b2") is None


def test_single_band_log():
    assert not single_band_log(TEST_XARR, "b1", 1.0, 1.0) is None


def test_single_band():
    assert not single_band(TEST_XARR, "b1") is None


def test_multidate():
    assert not multi_date_delta(TEST_XARR_T) is None


def test_ndci():
    assert not sentinel2_ndci(TEST_XARR, "b1", "b2", "b1", "b2") is None
