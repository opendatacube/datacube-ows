# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

"""Test band math utilities
"""
from collections.abc import Sequence

import numpy as np
import pytest
import xarray as xr
from datacube_ows.band_utils import (
    band_quotient,
    band_quotient_sum,
    constant,
    delta_bands,
    multi_date_delta,
    norm_diff,
    pre_scaled_delta_bands,
    pre_scaled_norm_diff,
    pre_scaled_sum_bands,
    radar_vegetation_index,
    scale_data,
    sentinel2_ndci,
    single_band,
    single_band_arcsec,
    single_band_log,
    single_band_offset_log,
    sum_bands,
)
from datacube_ows.ows_configuration import BandIndex, OWSProductLayer


class MockArray(xr.DataArray):
    __slots__ = ("nodata",)

    def __init__(
        self,
        data,
        coords=None,
        dims: Sequence[int] | None = None,
        name: str | None = None,
        attrs=None,
        indexes=None,
        fastpath=None,
    ) -> None:
        super().__init__(data, coords, dims, name, attrs, indexes, fastpath)
        self.nodata = 0


TEST_ARR_1 = MockArray(np.ones((100, 100), dtype=np.uint32), attrs={"nodata": 0})
TEST_ARR_2 = MockArray(np.ones((100, 100), dtype=np.uint32), attrs={"nodata": 0})
TEST_ARR_3 = MockArray(np.full((100, 100), 3, dtype=np.uint32), attrs={"nodata": 0})
TEST_XARR = {"b1": TEST_ARR_1, "b2": TEST_ARR_2}
TEST_XARR2 = {"b3": TEST_ARR_3, "b2": TEST_ARR_2}

TEST_XARR_T = xr.Dataset({"b1": (["x", "y", "time"], np.ones((100, 100, 2)))})


@pytest.fixture
def dummy_layer():
    product_layer = OWSProductLayer.__new__(OWSProductLayer)
    product_layer.name = "test_product"
    product_layer.band_idx = BandIndex.__new__(BandIndex)
    product_layer.band_idx._idx = {"b1": "b1", "b2": "b2"}
    product_layer.style_index = {}
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


def test_scale_data() -> None:
    assert scale_data(TEST_ARR_1, [0.0, 1.0], [0.0, 1.0]) is not None


def test_sum_bands() -> None:
    assert sum_bands(TEST_XARR, "b1", "b2") is not None


def test_pre_scaled_sum_bands() -> None:
    assert pre_scaled_sum_bands(TEST_XARR, "b1", "b2", 1.0, 0.0, 1.0, 0.0) is not None
    unscaled = sum_bands(TEST_XARR, "b1", "b2")
    assert pre_scaled_sum_bands(TEST_XARR, "b1", "b2").equals(unscaled)
    assert pre_scaled_sum_bands(TEST_XARR, "b1", "b2", 1.0, 0.0, 1.0, 0.0).equals(
        unscaled
    )
    assert pre_scaled_sum_bands(TEST_XARR, "b1", "b2", 2.0, 10.0, 2.0, 10.0).equals(
        2.0 * unscaled + 2 * 10.0
    )


def test_pre_scaled_delta_bands() -> None:
    assert (
        pre_scaled_delta_bands(TEST_XARR2, "b3", "b2", 1.0, 0.0, 1.0, 0.0) is not None
    )
    unscaled = delta_bands(TEST_XARR2, "b3", "b2")
    assert pre_scaled_delta_bands(TEST_XARR2, "b3", "b2").equals(unscaled)
    assert pre_scaled_delta_bands(TEST_XARR2, "b3", "b2", 1.0, 0.0, 1.0, 0.0).equals(
        unscaled
    )
    assert pre_scaled_delta_bands(TEST_XARR2, "b3", "b2", 2.0, 10.0, 2.0, 10.0).equals(
        2.0 * unscaled + 0.0
    )


def test_norm_diff(band_mapper) -> None:
    assert norm_diff(TEST_XARR, "b1", "b2") is not None
    assert norm_diff(TEST_XARR, "b1a", "b2", band_mapper, scale_from=[0, 1]) is not None


def test_pre_scaled_norm_diff(band_mapper) -> None:
    assert pre_scaled_norm_diff(TEST_XARR, "b1", "b2") is not None
    assert (
        pre_scaled_norm_diff(
            TEST_XARR, "b1a", "b2", band_mapper=band_mapper, scale_from=[0, 1]
        ) is not None
    )
    assert np.array_equal(
        pre_scaled_norm_diff(TEST_XARR2, "b3", "b2", 2.0, 0.0, 6.0, 0.0).values,
        np.zeros_like(TEST_ARR_1),
    )
    assert np.array_equal(
        pre_scaled_norm_diff(TEST_XARR2, "b3", "b2", 2.0, 10.0, 6.0, 10.0).values,
        np.zeros_like(TEST_ARR_1),
    )


def test_constant(band_mapper) -> None:
    assert constant(TEST_XARR, "b1", 10) is not None
    assert constant(TEST_XARR, "b1a", 10, band_mapper) is not None


def test_band_quotient(band_mapper) -> None:
    assert band_quotient(TEST_XARR, "b1", "b2") is not None
    assert band_quotient(TEST_XARR, "b1", "b2", band_mapper) is not None


def test_band_quotient_sum() -> None:
    assert band_quotient_sum(TEST_XARR, "b1", "b2", "b1", "b2") is not None


def test_single_band_log(band_mapper) -> None:
    assert single_band_log(TEST_XARR, "b1", 1.0, 1.0) is not None
    assert single_band_log(TEST_XARR, "b1", 1.0, 1.0, band_mapper) is not None


def test_single_band(band_mapper) -> None:
    assert single_band(TEST_XARR, "b1") is not None
    assert single_band(TEST_XARR, "b1", band_mapper) is not None


def test_multidate() -> None:
    assert multi_date_delta(TEST_XARR_T) is not None
    assert multi_date_delta(TEST_XARR_T, time_direction=1) is not None


def test_ndci() -> None:
    assert sentinel2_ndci(TEST_XARR, "b1", "b2", "b1", "b2") is not None


def test_single_band_offset_log(band_mapper) -> None:
    assert single_band_offset_log(TEST_XARR, "b1") is not None
    assert single_band_offset_log(TEST_XARR, "b1", offset=0.5) is not None
    assert single_band_offset_log(TEST_XARR, "b1", scale=100) is not None
    assert single_band_offset_log(TEST_XARR, "b1", scale_from=[0.0, 4.0]) is not None
    assert single_band_offset_log(TEST_XARR, "b1", scale_from=[0.0, 4.0], scale_to=[0, 1024]) is not None
    assert single_band_offset_log(TEST_XARR, "b1", band_mapper=band_mapper) is not None
    assert single_band_offset_log(TEST_XARR, "b1", mult_band="b2", band_mapper=band_mapper) is not None


def test_single_band_arcsec(band_mapper) -> None:
    assert single_band_arcsec(TEST_XARR, "b1") is not None
    assert single_band_arcsec(TEST_XARR, "b1", scale_from=[0.0, 0.8]) is not None
    assert single_band_arcsec(TEST_XARR, "b1", scale_from=[0.0, 0.8], scale_to=[0, 1024]) is not None
    assert single_band_arcsec(TEST_XARR, "b1", band_mapper=band_mapper) is not None


def test_rvi(band_mapper) -> None:
    assert radar_vegetation_index(TEST_XARR, "b1", "b2") is not None
    assert radar_vegetation_index(TEST_XARR, "b1", "b2", band_mapper=band_mapper) is not None
