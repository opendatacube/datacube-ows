"""Test band math utilities
"""
import numpy as np
import xarray as xr

from datacube_ows.band_utils import (
    scale_data, sum_bands, norm_diff,
    constant, single_band, band_quotient,
    band_quotient_sum, single_band_log,
    sentinel2_ndci, multi_date_delta
)

TEST_ARR_1 = np.ones((100,100))
TEST_ARR_2 = np.ones((100,100))
TEST_XARR = xr.Dataset(
    {
        'b1' : (['x','y'], TEST_ARR_1),
        'b2' : (['x','y'], TEST_ARR_2),
    }
)

TEST_XARR_T = xr.Dataset(
    {
        'b1' : (['x','y','time'], np.ones((100,100,2)))
    }
)

def test_scale_data():
    assert not scale_data(TEST_ARR_1, [0.0, 1.0] , [0.0, 1.0]) is None

def test_sum_bands():
    assert not sum_bands(TEST_XARR, 'b1', 'b2') is None

def test_norm_diff():
    assert not norm_diff(TEST_XARR, 'b1', 'b2') is None

def test_constant():
    assert not constant(TEST_XARR, 'b1', 10) is None

def test_band_quotient():
    assert not band_quotient(TEST_XARR, 'b1', 'b2') is None

def test_band_quotient_sum():
    assert not band_quotient_sum(TEST_XARR, 'b1', 'b2', 'b1', 'b2') is None

def test_single_band_log():
    assert not single_band_log(TEST_XARR, 'b1', 1.0, 1.0) is None

def test_multidate():
    assert not multi_date_delta(TEST_XARR_T) is None

def test_ndci():
    assert not sentinel2_ndci(TEST_XARR, 'b1', 'b2', 'b1', 'b2') is None