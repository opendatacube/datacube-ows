# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

from datetime import UTC, datetime
from unittest.mock import MagicMock

import pytest
from numpy import datetime64 as npdt64
from odc.geo.geobox import GeoBox

from datacube_ows.ows_configuration import TimeRes


@pytest.fixture
def simple_geobox() -> GeoBox:
    from affine import Affine

    aff = Affine.translation(145.0, -35.0) * Affine.scale(1.0 / 256, 2.0 / 256)
    return GeoBox((256, 256), aff, "EPSG:4326")


def test_timeres_enum(simple_geobox) -> None:
    # Make sure no values trigger exceptions.
    for res in TimeRes:
        res.is_subday()
        res.is_solar()
        res.is_summary()
        res.is_utc()
        res.is_grouped_day()
        res.search_times(datetime(2010, 1, 15, 13, 23, 55), geobox=simple_geobox)
        res.dataset_groupby()


def test_subday() -> None:
    res = TimeRes.SUBDAY
    assert res.is_subday()
    assert not res.is_solar()
    assert not res.is_summary()
    assert not res.is_utc()
    assert not res.is_grouped_day()


def test_solar(simple_geobox) -> None:
    res = TimeRes.SOLAR
    assert not res.is_subday()
    assert res.is_solar()
    assert not res.is_summary()
    assert not res.is_utc()
    assert res.is_grouped_day()

    with pytest.raises(ValueError) as e:
        res.search_times(datetime(2020, 6, 7, 20, 20, 0, tzinfo=UTC))
    assert "Solar time resolution search_times requires a geobox" in str(e.value)

    assert res.search_times(
        datetime(2020, 6, 7, 20, 20, 0, tzinfo=UTC), simple_geobox
    ) == (
        datetime(2020, 6, 6, 14, 0, tzinfo=UTC),
        datetime(2020, 6, 7, 13, 59, 59, tzinfo=UTC),
    )


def test_utc() -> None:
    res = TimeRes.UTC
    assert not res.is_subday()
    assert not res.is_solar()
    assert not res.is_summary()
    assert res.is_utc()
    assert res.is_grouped_day()

    assert res.search_times(
        datetime(2020, 6, 7, 20, 20, 0, tzinfo=UTC), simple_geobox
    ) == (
        datetime(2020, 6, 7, 0, 0, tzinfo=UTC),
        datetime(2020, 6, 7, 23, 59, 59, tzinfo=UTC),
    )

    gby = res.dataset_groupby(["z", "a"])
    assert gby.dimension == "time"
    gby_fn = gby.group_by_func

    ds_test = MagicMock()
    for test_in, expected_out in [
        (
            datetime(2020, 6, 7, 0, 0, 0, tzinfo=UTC),
            datetime(2020, 6, 7, 0, 0, 0, tzinfo=UTC),
        ),
        (
            datetime(2020, 7, 7, 6, 30, 22, tzinfo=UTC),
            datetime(2020, 7, 7, 0, 0, 0, tzinfo=UTC),
        ),
    ]:
        ds_test.time.begin = test_in
        assert gby_fn(ds_test) == npdt64(expected_out, "ns")
    gby_sortkey = gby.sort_key
    ds_test.product.name = "z"
    assert gby_sortkey(ds_test) == (0, ds_test.time.begin)
    ds_test.product.name = "a"
    assert gby_sortkey(ds_test) == (1, ds_test.time.begin)


def test_summary() -> None:
    res = TimeRes.SUMMARY
    assert not res.is_subday()
    assert not res.is_solar()
    assert res.is_summary()
    assert not res.is_utc()
    assert not res.is_grouped_day()
    assert res.search_times(datetime(2020, 6, 7, 0, 0, 0, tzinfo=UTC)) == datetime(
        2020, 6, 7, 0, 0, 0, tzinfo=UTC
    )


def test_legacy_aliases() -> None:
    assert TimeRes.parse("raw") == TimeRes.SOLAR
    assert TimeRes.parse("day") == TimeRes.SUMMARY
    assert TimeRes.parse("month") == TimeRes.SUMMARY
    assert TimeRes.parse("year") == TimeRes.SUMMARY
