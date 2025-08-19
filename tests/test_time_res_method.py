# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

from datetime import datetime, timezone

import pytest
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
        res.search_times(datetime(2010, 1, 15, 13, 23, 55), geobox=simple_geobox)
        res.dataset_groupby()


def test_subday() -> None:
    res = TimeRes.SUBDAY
    assert res.is_subday()
    assert not res.is_solar()
    assert not res.is_summary()


def test_solar(simple_geobox) -> None:
    res = TimeRes.SOLAR
    assert not res.is_subday()
    assert res.is_solar()
    assert not res.is_summary()

    with pytest.raises(ValueError) as e:
        res.search_times(datetime(2020, 6, 7, 20, 20, 0, tzinfo=timezone.utc))
    assert "Solar time resolution search_times requires a geobox" in str(e.value)

    assert res.search_times(
        datetime(2020, 6, 7, 20, 20, 0, tzinfo=timezone.utc), simple_geobox
    ) == (
        datetime(2020, 6, 6, 14, 0, tzinfo=timezone.utc),
        datetime(2020, 6, 7, 13, 59, 59, tzinfo=timezone.utc),
    )


def test_summary() -> None:
    res = TimeRes.SUMMARY
    assert not res.is_subday()
    assert not res.is_solar()
    assert res.is_summary()
    assert res.search_times(
        datetime(2020, 6, 7, 0, 0, 0, tzinfo=timezone.utc)
    ) == datetime(2020, 6, 7, 0, 0, 0, tzinfo=timezone.utc)


def test_legacy_aliases() -> None:
    assert TimeRes.parse("raw") == TimeRes.SOLAR
    assert TimeRes.parse("day") == TimeRes.SUMMARY
    assert TimeRes.parse("month") == TimeRes.SUMMARY
    assert TimeRes.parse("year") == TimeRes.SUMMARY
