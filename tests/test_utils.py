# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import datetime
from unittest.mock import MagicMock

import pytest
import pytz


def mock_ds_for_sort(id_: str, st: datetime, ct: datetime, lon: float, prod_name):
    ds = MagicMock()
    ds.id = id_
    ds.time.begin = st
    ds.center_time = ct
    ds.metadata.lon.begin = lon - 5.0
    ds.metadata.lon.end = lon + 5.0
    ds.type.name = prod_name
    return ds


@pytest.fixture
def datasets_for_sorting():
    utc = datetime.timezone.utc
    DT = datetime.datetime
    return [
        mock_ds_for_sort("A", DT(2022, 7, 15, 0, 0, tzinfo=utc), DT(2022, 7, 15, 9, 45, tzinfo=utc), 148.0, "prod_a"),
        mock_ds_for_sort("B", DT(2022, 7, 15, 0, 0, tzinfo=utc), DT(2022, 7, 15, 10, 45, tzinfo=utc), 148.0, "prod_a"),
        mock_ds_for_sort("C", DT(2022, 7, 15, 5, 0, tzinfo=utc), DT(2022, 7, 15, 0, 5, tzinfo=utc), 128.0, "prod_a"),
        mock_ds_for_sort("D", DT(2022, 7, 15, 5, 0, tzinfo=utc), DT(2022, 7, 15, 14, 45, tzinfo=utc), 128.0, "prod_a"),

        mock_ds_for_sort("E", DT(2022, 7, 15, 0, 0, tzinfo=utc), DT(2022, 7, 15, 9, 45, tzinfo=utc), 128.0, "prod_b"),
        mock_ds_for_sort("F", DT(2022, 7, 15, 0, 0, tzinfo=utc), DT(2022, 7, 15, 10, 45, tzinfo=utc), 128.0, "prod_b"),
        mock_ds_for_sort("G", DT(2022, 7, 15, 5, 0, tzinfo=utc), DT(2022, 7, 15, 0, 5, tzinfo=utc), 148.0, "prod_b"),
        mock_ds_for_sort("H", DT(2022, 7, 15, 5, 0, tzinfo=utc), DT(2022, 7, 15, 14, 45, tzinfo=utc), 148.0, "prod_b"),

        mock_ds_for_sort("I", DT(2022, 7, 15, 0, 0, tzinfo=utc), DT(2022, 7, 15, 9, 45, tzinfo=utc), 128.0, "prod_c"),
        mock_ds_for_sort("J", DT(2022, 7, 15, 0, 0, tzinfo=utc), DT(2022, 7, 15, 10, 45, tzinfo=utc), 128.0, "prod_c"),
        mock_ds_for_sort("K", DT(2022, 7, 15, 5, 0, tzinfo=utc), DT(2022, 7, 15, 0, 45, tzinfo=utc), 148.0, "prod_c"),
        mock_ds_for_sort("L", DT(2022, 7, 15, 5, 0, tzinfo=utc), DT(2022, 7, 15, 14, 45, tzinfo=utc), 148.0, "prod_c"),
    ]


def test_group_by_stat(datasets_for_sorting):
    from datacube import Datacube

    from datacube_ows.utils import group_by_begin_datetime

    gby = group_by_begin_datetime()
    date_only = Datacube.group_datasets(datasets_for_sorting, gby)
    assert len(date_only) == 1
    arrays = date_only.values
    assert [ds.id for ds in arrays[0]] == ['A', 'B', 'E', 'F', 'I', 'J', 'C', 'D', 'G', 'H', 'K', 'L']


    gby = group_by_begin_datetime(["prod_c", "prod_b", "prod_a"], truncate_dates=False)
    date_only = Datacube.group_datasets(datasets_for_sorting, gby)
    assert len(date_only) == 2
    arrays = date_only.values
    assert [ds.id for ds in arrays[0]] == ['I', 'J', 'E', 'F', 'A', 'B']
    assert [ds.id for ds in arrays[1]] == ['K', 'L', 'G', 'H', 'C', 'D']


def test_group_by_solar(datasets_for_sorting):
    from datacube import Datacube

    from datacube_ows.utils import group_by_solar

    gby = group_by_solar()
    date_only = Datacube.group_datasets(datasets_for_sorting, gby)
    assert len(date_only) == 2
    arrays = date_only.values
    assert [ds.id for ds in arrays[0]] == ['A', 'B', 'E', 'F', 'I', 'J', 'C', 'D', 'G', 'K']
    assert [ds.id for ds in arrays[1]] == ['H', 'L']


    gby = group_by_solar(["prod_c", "prod_b", "prod_a"])
    date_only = Datacube.group_datasets(datasets_for_sorting, gby)
    assert len(date_only) == 2
    arrays = date_only.values
    assert [ds.id for ds in arrays[0]] == ['I', 'J', 'K', 'E', 'F', 'G', 'A', 'B', 'C', 'D']
    assert [ds.id for ds in arrays[1]] == ['L', 'H']


def test_group_by_mosaic(datasets_for_sorting):
    from datacube import Datacube

    from datacube_ows.utils import group_by_mosaic

    gby = group_by_mosaic()
    date_only = Datacube.group_datasets(datasets_for_sorting, gby)
    assert len(date_only) == 1
    arrays = date_only.values
    assert [ds.id for ds in arrays[0]] == ['A', 'B', 'E', 'F', 'I', 'J', 'C', 'D', 'G', 'K', 'H', 'L']


    gby = group_by_mosaic(["prod_c", "prod_b", "prod_a"])
    date_only = Datacube.group_datasets(datasets_for_sorting, gby)
    assert len(date_only) == 1
    arrays = date_only.values
    assert [ds.id for ds in arrays[0]] == ['I', 'J', 'K', 'E', 'F', 'G', 'A', 'B', 'C', 'D', 'L', 'H']


def test_find_in_dates():
    from datacube_ows.utils import find_matching_date
    dates = [
        datetime.datetime(1991, 8, 3, 22, 15, 24, 122234, tzinfo=pytz.utc),
        datetime.datetime(1991, 8, 5, 14, 6, 12, 156238, tzinfo=pytz.utc),
        datetime.datetime(1992, 2, 5, 15, 45, 11, 832438, tzinfo=pytz.utc),
        datetime.datetime(1995, 2, 13, 21, 9, 55, 722242, tzinfo=pytz.utc),
        datetime.datetime(1996, 1, 23, 12, 15, 25, 723411, tzinfo=pytz.utc),
        datetime.datetime(1996, 1, 23, 12, 15, 27, 523410, tzinfo=pytz.utc),
        datetime.datetime(1996, 1, 23, 12, 15, 28, 0, tzinfo=pytz.utc),
        datetime.datetime(1999, 12, 31, 22, 22, 22, 222222, tzinfo=pytz.utc),
        datetime.datetime(2011, 7, 23, 12, 4, 12, 723494, tzinfo=pytz.utc),
    ]
    assert find_matching_date(datetime.datetime(1991, 8, 3, 22, 15, 24, 122234, tzinfo=pytz.utc), dates)
    assert find_matching_date(datetime.datetime(2011, 7, 23, 12, 4, 12, 723494, tzinfo=pytz.utc), dates)
    assert find_matching_date(datetime.datetime(1992, 2, 5, 15, 45, 11, 234110, tzinfo=pytz.utc), dates)
    assert find_matching_date(datetime.datetime(1996, 1, 23, 12, 15, 25, 723411, tzinfo=pytz.utc), dates)
    assert not find_matching_date(datetime.datetime(1996, 1, 23, 12, 15, 26, 723411, tzinfo=pytz.utc), dates)
    assert find_matching_date(datetime.datetime(1996, 1, 23, 12, 15, 27, 723411, tzinfo=pytz.utc), dates)
    assert not find_matching_date(datetime.datetime(1896, 1, 23, 12, 15, 26, 723411, tzinfo=pytz.utc), dates)
    assert not find_matching_date(datetime.datetime(2016, 1, 23, 12, 15, 26, 723411, tzinfo=pytz.utc), dates)
    assert not find_matching_date(datetime.datetime(2011, 7, 23, 12, 4, 12, 723494, tzinfo=pytz.utc), [])
