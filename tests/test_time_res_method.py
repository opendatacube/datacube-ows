import pytest
from datetime import datetime
import pytz

from datacube_ows.ows_configuration import OWSProductLayer, TIMERES_RAW, TIMERES_MON, TIMERES_YR


def dummy_timeres_layer(time_res):
    prod = product_layer = OWSProductLayer.__new__(OWSProductLayer)
    prod.time_resolution = time_res
    return prod

class Thing:
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

@pytest.fixture
def dummy_raw_layer():
    return dummy_timeres_layer(TIMERES_RAW)

@pytest.fixture
def dummy_monthly_layer():
    return dummy_timeres_layer(TIMERES_MON)

@pytest.fixture
def dummy_yearly_layer():
    return dummy_timeres_layer(TIMERES_YR)

@pytest.fixture
def simple_geobox():
    from affine import Affine
    from datacube.utils import geometry

    aff = Affine.translation(145.0, -35.0) * Affine.scale(
        1.0/256, 2.0/256
    )
    return geometry.GeoBox(256, 256, aff, 'EPSG:4326')

def test_raw_timeres(dummy_raw_layer, simple_geobox):
    assert dummy_raw_layer.is_raw_time_res
    assert not dummy_raw_layer.is_month_time_res
    assert not dummy_raw_layer.is_year_time_res
    assert dummy_raw_layer.dataset_groupby() == "solar_day"

    assert dummy_raw_layer.search_times(
        datetime(2020, 6, 7, 20, 20, 0, tzinfo=pytz.utc),
        simple_geobox,
    ) == (
        datetime(2020, 6, 6, 13, 55, tzinfo=pytz.utc),
        datetime(2020, 6, 7, 13, 54, 59, tzinfo=pytz.utc),
    )

def test_mon_timeres(dummy_monthly_layer, simple_geobox):
    assert not dummy_monthly_layer.is_raw_time_res
    assert dummy_monthly_layer.is_month_time_res
    assert not dummy_monthly_layer.is_year_time_res
    gby = dummy_monthly_layer.dataset_groupby()
    assert gby.dimension == 'time'

    t = Thing(begin="ABC")
    ds = Thing(time=t)
    assert gby.group_by_func(ds) == "ABC"
    assert gby.units == 'seconds since 1970-01-01 00:00:00'
    assert gby.sort_key(ds) == "ABC"

    assert dummy_monthly_layer.search_times(
        datetime(2020, 6, 1, tzinfo=pytz.utc),
        simple_geobox,
    ) == (
               datetime(2020, 6, 1),
               datetime(2020, 6, 30),
           )

def test_year_timeres(dummy_yearly_layer):
    assert not dummy_yearly_layer.is_raw_time_res
    assert not dummy_yearly_layer.is_month_time_res
    assert dummy_yearly_layer.is_year_time_res
    gby = dummy_yearly_layer.dataset_groupby()
    assert gby.dimension == 'time'

    t = Thing(begin="ABC")
    ds = Thing(time=t)
    assert gby.group_by_func(ds) == "ABC"
    assert gby.units == 'seconds since 1970-01-01 00:00:00'
    assert gby.sort_key(ds) == "ABC"

    assert dummy_yearly_layer.search_times(
        datetime(2020, 6, 1, tzinfo=pytz.utc),
        simple_geobox,
    ) == (
               datetime(2020, 1, 1),
               datetime(2020, 12, 31, 23, 59, 59),
           )
