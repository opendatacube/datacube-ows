# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import datetime
from unittest.mock import MagicMock

import pytest
import xarray
from datacube.utils import geometry
from pytz import utc

import datacube_ows.ogc_utils
import datacube_ows.utils


class DSCT:
    def __init__(self, meta):
        self.center_time = datetime.datetime(1970, 1, 1, 0, 0, 0)
        self.metadata_doc = meta


def test_dataset_center_time():
    dct = datacube_ows.ogc_utils.dataset_center_time
    ds = DSCT({})
    assert dct(ds).year == 1970
    ds = DSCT({
        "properties": {
            "dtr:start_datetime": "1980-01-01T00:00:00"
        },
    })
    assert dct(ds).year == 1980
    ds = DSCT({
        "extent": {
            "center_dt": "1990-01-01T00:00:00"
        },
        "properties": {
            "dtr:start_datetime": "1980-01-01T00:00:00"
        },
    })
    assert dct(ds).year == 1990


@pytest.fixture
def dummy_ds():
    ds = MagicMock()
    ds.extent = geometry.polygon(
        [
            (149.0, -35.3),
            (149.1, -35.3),
            (149.1, -35.4),
            (149.0, -35.4),
            (149.0, -35.3),
        ],
        crs="EPSG:4326"
    )
    ds.center_time = datetime.datetime(2020, 12, 25, 15, 11, 11, tzinfo=utc)
    ds.metadata_doc = {}
    return ds

def test_tz_for_dataset(dummy_ds):
    ret = datacube_ows.ogc_utils.tz_for_dataset(dummy_ds)
    assert ret.zone == "Australia/Sydney"


def test_local_date(dummy_ds):
    ld = datacube_ows.ogc_utils.local_date(dummy_ds)
    assert ld.year == 2020
    assert ld.day == 26
    tz = datacube_ows.ogc_utils.tz_for_dataset(dummy_ds)
    ld = datacube_ows.ogc_utils.local_date(dummy_ds, tz)
    assert ld.year == 2020
    assert ld.day == 26


def test_month_date_range_wrap():
    d = datetime.date(2019, 12, 1)
    a, b = datacube_ows.ogc_utils.month_date_range(d)
    assert a == datetime.datetime(2019, 12, 1, 0, 0, 0, tzinfo=utc)
    assert b == datetime.datetime(2019, 12, 31, 0, 0, 0, tzinfo=utc)


def test_get_service_base_url():

    # not a list
    allowed_urls = "https://foo.hello.world"
    request_url = "https://foo.bar.baz"
    ret = datacube_ows.ogc_utils.get_service_base_url(allowed_urls, request_url)
    assert ret == "https://foo.hello.world"

    # Value not in list
    allowed_urls = ["https://foo.hello.world", "https://alice.bob.eve"]
    request_url = "https://foo.bar.baz"
    ret = datacube_ows.ogc_utils.get_service_base_url(allowed_urls, request_url)
    assert ret == "https://foo.hello.world"

    # Value in list
    allowed_urls = ["https://foo.hello.world", "https://foo.bar.baz", "https://alice.bob.eve"]
    request_url = "https://foo.bar.baz"
    ret = datacube_ows.ogc_utils.get_service_base_url(allowed_urls, request_url)
    assert ret == "https://foo.bar.baz"

    # Trailing /
    allowed_urls = ["https://foo.bar.baz", "https://alice.bob.eve"]
    request_url = "https://foo.bar.baz/"
    ret = datacube_ows.ogc_utils.get_service_base_url(allowed_urls, request_url)
    assert ret == "https://foo.bar.baz"

    # include path
    allowed_urls = ["https://foo.bar.baz", "https://foo.bar.baz/wms/"]
    request_url = "https://foo.bar.baz/wms/"
    ret = datacube_ows.ogc_utils.get_service_base_url(allowed_urls, request_url)
    assert ret == "https://foo.bar.baz/wms"

    # use value from list instead of request
    allowed_urls = ["https://foo.bar.baz", "https://foo.bar.baz/wms/"]
    request_url = "http://foo.bar.baz/wms/"
    ret = datacube_ows.ogc_utils.get_service_base_url(allowed_urls, request_url)
    assert ret == "https://foo.bar.baz/wms"


def test_parse_for_base_url():
    url = "https://hello.world.bar:8000/wms/?CheckSomething"
    ret = datacube_ows.ogc_utils.parse_for_base_url(url)
    assert ret == "hello.world.bar:8000/wms"


def test_create_geobox():
    geobox = datacube_ows.ogc_utils.create_geobox("EPSG:4326",
                                                  140.7184, 145.6924, -16.1144, -13.4938,
                                                  1182, 668)
    geobox_ho = datacube_ows.ogc_utils.create_geobox("EPSG:4326",
                                                  140.7184, 145.6924, -16.1144, -13.4938,
                                                  height=668)
    geobox_wo = datacube_ows.ogc_utils.create_geobox("EPSG:4326",
                              140.7184, 145.6924, -16.1144, -13.4938,
                              width=1182)
    for gb in (geobox, geobox_ho, geobox_wo):
        assert geobox.width == 1182
        assert geobox.height == 668
    with pytest.raises(Exception) as excinfo:
        geobox_no = datacube_ows.ogc_utils.create_geobox("EPSG:4326",
                                                         140.7184, 145.6924, -16.1144, -13.4938)
    assert "Must supply at least a width or height" in str(excinfo.value)


from tests.utils import dummy_da

coords = [
    ("x", [-1.0, -0.5, 0.0, 0.5, 1.0]),
]


def test_mask_by_val():
    data = {
        "match": dummy_da(-999, "match", coords, attrs={"nodata": -999}, dtype="int16"),
        "dont_match": dummy_da(679, "dont_match", coords, attrs={"nodata": -999}, dtype="int16"),
    }
    mask = datacube_ows.ogc_utils.mask_by_val(data, "match")
    assert not mask.values[0]
    mask = datacube_ows.ogc_utils.mask_by_val(data, "dont_match")
    assert mask.values[0]
    mask = datacube_ows.ogc_utils.mask_by_val(data, "match", val=679)
    assert mask.values[0]
    mask = datacube_ows.ogc_utils.mask_by_val(data, "dont_match", val=679)
    assert not mask.values[0]


def test_mask_by_val2():
    data = {
        "match": dummy_da(-999, "match", coords, attrs={"nodata": -999}, dtype="int16"),
        "dont_match": dummy_da(679, "dont_match", coords, attrs={"nodata": -999}, dtype="int16"),
    }
    mask = datacube_ows.ogc_utils.mask_by_val2(data, "match")
    assert not mask.values[0]
    mask = datacube_ows.ogc_utils.mask_by_val2(data, "dont_match")
    assert mask.values[0]


def test_mask_by_bitflag():
    data = {
        "match": dummy_da(128, "match", coords, attrs={"nodata": 128}, dtype="uint8"),
        "dont_match": dummy_da(63, "dont_match", coords, attrs={"nodata": 128}, dtype="uint8"),
    }
    mask = datacube_ows.ogc_utils.mask_by_bitflag(data, "match")
    assert not mask.values[0]
    mask = datacube_ows.ogc_utils.mask_by_bitflag(data, "dont_match")
    assert mask.values[0]


def test_mask_by_val_in_band():
    data = {
        "match": dummy_da(-999, "match", coords, attrs={"nodata": -999}, dtype="int16"),
        "dont_match": dummy_da(679, "dont_match", coords, attrs={"nodata": -999}, dtype="int16"),
        "dband": dummy_da(0.77, "dband", coords, dtype="float128"),
    }
    mask = datacube_ows.ogc_utils.mask_by_val_in_band(data, "dband", mask_band="match")
    assert not mask.values[0]
    mask = datacube_ows.ogc_utils.mask_by_val_in_band(data, "dband", mask_band="dont_match", val=679)
    assert not mask.values[0]


def test_mask_by_quality():
    data = {
        "quality": dummy_da(-999, "match", coords, attrs={"nodata": -999}, dtype="int16"),
        "dband": dummy_da(0.77, "dband", coords, dtype="float128"),
    }
    mask = datacube_ows.ogc_utils.mask_by_quality(data, "dband")
    assert not mask.values[0]


def test_mask_by_extent_flag():
    data = {
        "extent": dummy_da(1, "match", coords, dtype="uint8"),
        "dband": dummy_da(0.77, "dband", coords, dtype="float128"),
    }
    mask = datacube_ows.ogc_utils.mask_by_extent_flag(data, "dband")
    assert mask.values[0]
    data["extent"] = dummy_da(0, "match", coords, dtype="uint8")
    mask = datacube_ows.ogc_utils.mask_by_extent_flag(data, "dband")
    assert not mask.values[0]


def test_mask_by_extent_val():
    data = {
        "extent": dummy_da(-999, "match", coords, attrs={"nodata": -999}, dtype="int16"),
        "dband": dummy_da(0.77, "dband", coords, dtype="float128"),
    }
    mask = datacube_ows.ogc_utils.mask_by_extent_val(data, "dband")
    assert not mask.values[0]


def test_mask_by_nan():
    data = {
        "match": dummy_da(float("nan"), "match", coords, dtype="float128"),
        "dont_match": dummy_da(67.9, "dont_match", coords, dtype="float128"),
    }
    mask = datacube_ows.ogc_utils.mask_by_nan(data, "match")
    assert not mask.values[0]
    mask = datacube_ows.ogc_utils.mask_by_nan(data, "dont_match")
    assert mask.values[0]

def test_day_summary_date_range():
    start, end = datacube_ows.ogc_utils.day_summary_date_range(datetime.date(2015, 5, 12))
    assert start == datetime.datetime(2015, 5, 12, 0, 0, 0, tzinfo=utc)
    assert end == datetime.datetime(2015, 5, 12, 23, 59, 59, tzinfo=utc)

xyt_coords = [
    ("x", [-1.0, -0.5, 0.0, 0.5, 1.0]),
    ("y", [-1.0, -0.5, 0.0, 0.5, 1.0]),
    ("time", [
                datetime.datetime(2021, 1, 1, 22, 44, 5),
                datetime.datetime.now()
              ])
]

def test_png_loop_over():
    data = xarray.Dataset({
            "red": dummy_da(100, "red", xyt_coords, dtype="uint8"),
            "green": dummy_da(70, "green", xyt_coords, dtype="uint8"),
            "blue": dummy_da(150, "blue", xyt_coords, dtype="uint8"),
            "alpha": dummy_da(200, "alpha", xyt_coords, dtype="uint8"),
        })
    imgs = datacube_ows.ogc_utils.xarray_image_as_png(data, None, loop_over="time")
    assert len(imgs) == 2

def test_png_loop_over_anim():
    data = xarray.Dataset({
        "red": dummy_da(100, "red", xyt_coords, dtype="uint8"),
        "green": dummy_da(70, "green", xyt_coords, dtype="uint8"),
        "blue": dummy_da(150, "blue", xyt_coords, dtype="uint8"),
        "alpha": dummy_da(200, "alpha", xyt_coords, dtype="uint8"),
    })
    imgs = datacube_ows.ogc_utils.xarray_image_as_png(data, None, loop_over="time", animate=True)
    assert len(imgs) == 223
    assert imgs.find(b"\x89PNG") == 0

def test_time_call(monkeypatch):
    class FakeLogger:
        _instance = None
        slot = None

        def __new__(cls, *args, **kwargs):
            if not cls._instance:
                cls._instance = super().__new__(cls)
            return cls._instance

        def debug(self, template, *args):
            self.slot = template % args

        def addHandler(self, handler):
            pass

        def removeHandler(self, handler):
            pass

    monkeypatch.setattr("logging.getLogger", FakeLogger)

    @datacube_ows.utils.time_call
    def timed_func(x):
        return x + 1

    assert timed_func(7) == 8
    assert "timed_func" in FakeLogger._instance.slot
    assert "took" in FakeLogger._instance.slot
    assert "ms" in FakeLogger._instance.slot


def test_log_call(monkeypatch):
    class FakeLogger:
        _instance = None
        slot = None

        def __new__(cls, *args, **kwargs):
            if not cls._instance:
                cls._instance = super().__new__(cls)
            return cls._instance

        def debug(self, template, *args):
            self.slot = template % args

        def addHandler(self, handler):
            pass

        def removeHandler(self, handler):
            pass

    monkeypatch.setattr("logging.getLogger", FakeLogger)

    @datacube_ows.utils.log_call
    def timed_func(x):
        return x + 1

    assert timed_func(7) == 8
    assert "timed_func" in FakeLogger._instance.slot
    assert "args" in FakeLogger._instance.slot
    assert "7" in FakeLogger._instance.slot

