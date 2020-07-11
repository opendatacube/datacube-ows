"""Test band math utilities
"""
import numpy as np
import xarray as xr

from datacube_ows.band_utils import (
    scale_data, sum_bands, norm_diff,
    constant, single_band, band_quotient
)

TEST_ARR_1 = np.ones((100,100))
TEST_ARR_2 = np.ones((100,100))
TEST_XARR = xr.Dataset(
    {
        'b1' : (['x','y'], TEST_ARR_1),
        'b2' : (['x','y'], TEST_ARR_2),
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