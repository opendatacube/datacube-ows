# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import datetime
from unittest.mock import MagicMock

import pytest

import datacube_ows.wms_utils
from datacube_ows.ogc_exceptions import WMSException


def test_parse_time_delta():
    from dateutil.relativedelta import relativedelta

    tests = {
        relativedelta(hours=1): ['P0Y0M0DT1H0M0S', 'PT1H0M0S', 'PT1H', ],
        relativedelta(months=18): ['P1Y6M0DT0H0M0S', 'P1Y6M0D', 'P0Y18M0DT0H0M0S', 'P18M', ],
        relativedelta(minutes=90): ['PT1H30M', 'P0Y0M0DT1H30M0S', 'PT90M'],
    }
    for td, td_str_list in tests.items():
        for td_str in td_str_list:
            assert td == datacube_ows.wms_utils.parse_time_delta(td_str)


def test_parse_wms_time_strings():
    import datetime as dt
    tests = {
        '2018-01-10/2019-01-10': (dt.datetime(2018, 1, 10, 0, 0), dt.datetime(2019, 1, 10, 23, 23, 59, 999999)),
        '2000/P1Y': (dt.datetime(2000, 1, 1, 0, 0), dt.datetime(2000, 12, 31, 23, 59, 59, 999999)),
        '2018-01-10/P5D': (dt.datetime(2018, 1, 10, 0, 0), dt.datetime(2018, 1, 14, 23, 59, 59, 999999)),
        'P1M/2018-01-10': (dt.datetime(2017, 12, 10, 0, 0, 0, 1), dt.datetime(2018, 1, 10, 23, 23, 59, 999999)),
    }

    for value, result in tests.items():
        assert result == datacube_ows.wms_utils.parse_wms_time_strings(value.split('/'))


def test_parse_wms_time_strings_with_present():
    import datetime as dt
    start, end = datacube_ows.wms_utils.parse_wms_time_strings('2018-01-10/PRESENT'.split('/'))
    assert start == dt.datetime(2018, 1, 10, 0, 0)
    assert (dt.datetime.utcnow() - end).total_seconds() < 60


@pytest.fixture
def dummy_product():
    dummy = MagicMock()
    return dummy


def test_parse_userbandmath(dummy_product):
    style = datacube_ows.wms_utils.single_style_from_args(dummy_product,
                                                          {
                                                              "code": "2*(red-nir)/(red+nir)",
                                                              "colorscheme": "viridis",
                                                              "colorscalerange": "0,2"
                                                          })


def test_parse_userbandmath_nobands(dummy_product):
    with pytest.raises(WMSException) as e:
        style = datacube_ows.wms_utils.single_style_from_args(dummy_product,
                              {
                                  "code": "2+(4.0*72)",
                                  "colorscheme": "viridis",
                                  "colorscalerange": "0,2"
                              })
    assert "Code expression invalid" in str(e.value)
    assert "Expression references no bands" in str(e.value)


def test_parse_userbandmath_banned_op(dummy_product):
    with pytest.raises(WMSException) as e:
        style = datacube_ows.wms_utils.single_style_from_args(dummy_product,
                                  {
                                      "code": "red<green",
                                      "colorscheme": "viridis",
                                      "colorscalerange": "0,2"
                                  })
    assert "not supported" in str(e.value)
    assert "Code expression invalid" in str(e.value)

def test_parse_userbandmath_bad_code(dummy_product):
    with pytest.raises(WMSException) as e:
        style = datacube_ows.wms_utils.single_style_from_args(dummy_product,
                          {
                              "code": "2*(red@nir)/(red#nir)",
                              "colorscheme": "viridis",
                              "colorscalerange": "0,2"
                          })
    assert "Code expression invalid" in str(e.value)


def test_parse_userbandmath_bad_scheme(dummy_product):
    with pytest.raises(WMSException) as e:
        style = datacube_ows.wms_utils.single_style_from_args(dummy_product,
                                                              {
                                                                  "code": "2*(red-nir)/(red+nir)",
                                                                  "colorscheme": "i_am_not_a_matplotlib_scheme",
                                                                  "colorscalerange": "0,2"
                                                              })
    assert "Invalid Matplotlib ramp name:" in str(e.value)


def test_parse_no2_colorscalerange(dummy_product):
    with pytest.raises(WMSException) as e:
        style = datacube_ows.wms_utils.single_style_from_args(dummy_product,
                                                              {
                                                                  "code": "2*(red-nir)/(red+nir)",
                                                                  "colorscheme": "viridis",
                                                                  "colorscalerange": "0,2,4,6,8,9,15,52"
                                                              })
    assert "Colorscale range must be two numbers, sorted and separated by a comma." in str(e.value)
    with pytest.raises(WMSException) as e:
        style = datacube_ows.wms_utils.single_style_from_args(dummy_product,
                                                              {
                                                                  "code": "2*(red-nir)/(red+nir)",
                                                                  "colorscheme": "viridis",
                                                                  "colorscalerange": "2"
                                                              })
    assert "Colorscale range must be two numbers, sorted and separated by a comma." in str(e.value)


def test_parse_nonnumeric_colorscalerange(dummy_product):
    with pytest.raises(WMSException) as e:
        style = datacube_ows.wms_utils.single_style_from_args(dummy_product,
                                                              {
                                                                  "code": "2*(red-nir)/(red+nir)",
                                                                  "colorscheme": "viridis",
                                                                  "colorscalerange": "0,spam",
                                                              })
    assert "Colorscale range must be two numbers, sorted and separated by a comma." in str(e.value)
    with pytest.raises(WMSException) as e:
        style = datacube_ows.wms_utils.single_style_from_args(dummy_product,
                                                              {
                                                                  "code": "2*(red-nir)/(red+nir)",
                                                                  "colorscheme": "viridis",
                                                                  "colorscalerange": "spam,2"
                                                              })
    assert "Colorscale range must be two numbers, sorted and separated by a comma." in str(e.value)


def test_parse_unsorted_colorscalerange(dummy_product):
    with pytest.raises(WMSException) as e:
        style = datacube_ows.wms_utils.single_style_from_args(dummy_product,
                          {
                              "code": "2*(red-nir)/(red+nir)",
                              "colorscheme": "viridis",
                              "colorscalerange": "0,spam",
                          })
    assert "Colorscale range must be two numbers, sorted and separated by a comma." in str(e.value)
    with pytest.raises(WMSException) as e:
        style = datacube_ows.wms_utils.single_style_from_args(dummy_product,
                            {
                                "code": "2*(red-nir)/(red+nir)",
                                "colorscheme": "viridis",
                                "colorscalerange": "2,0"
                            })
    assert "Colorscale range must be two numbers, sorted and separated by a comma." in str(e.value)

def test_parse_item_1(dummy_product):
    dummy_product.ranges = {
        "times": [
            datetime.date(2021, 1, 6),
            datetime.date(2021, 1, 7),
            datetime.date(2021, 1, 8),
            datetime.date(2021, 1, 9),
            datetime.date(2021, 1, 10),
        ]
    }
    dt = datacube_ows.wms_utils.parse_time_item("2010-01-01/2021-01-08", dummy_product)
    assert dt == dummy_product.ranges["times"][0]
    dummy_product.regular_time_axis = True
    with pytest.raises(WMSException) as e:
        dt = datacube_ows.wms_utils.parse_time_item("2010-01-01/2010-01-08", dummy_product)
    assert "No data available for time dimension range" in str(e.value)
    dummy_product.regular_time_axis = False
    with pytest.raises(WMSException) as e:
        dt = datacube_ows.wms_utils.parse_time_item("2010-01-01/2010-01-08", dummy_product)
    assert "Time dimension range" in str(e.value)
    assert "not valid for this layer" in str(e.value)
    dt = datacube_ows.wms_utils.parse_time_item("", dummy_product)
    assert dt == dummy_product.ranges["times"][-1]
    with pytest.raises(WMSException) as e:
        dt = datacube_ows.wms_utils.parse_time_item("this_is_not_a_date, mate", dummy_product)
    assert "Time dimension value" in str(e.value)
    assert "not valid for this layer" in str(e.value)


def test_parse_item_2(dummy_product):
    dummy_product.ranges = {
        "times": [
            datetime.date(2021, 1, 6),
            datetime.date(2021, 1, 7),
            datetime.date(2021, 1, 8),
            datetime.date(2021, 1, 10),
        ]
    }
    dummy_product.ranges["time_set"] = set(dummy_product.ranges["times"])
    dummy_product.time_range.return_value = (
        datetime.date(2021, 1, 6), datetime.date(2021, 1, 10),
    )
    dummy_product.regular_time_axis = False

    dt = datacube_ows.wms_utils.parse_time_item("2021-01-08", dummy_product)
    assert dt == datetime.date(2021, 1, 8)

    with pytest.raises(WMSException) as e:
        dt = datacube_ows.wms_utils.parse_time_item("2021-01-01", dummy_product)
    assert "Time dimension value" in str(e.value)
    assert "not valid for this layer" in str(e.value)

    dummy_product.regular_time_axis = True
    dummy_product.time_axis_interval = 1

    dt = datacube_ows.wms_utils.parse_time_item("2021-01-08", dummy_product)
    assert dt == datetime.date(2021, 1, 8)

    dt = datacube_ows.wms_utils.parse_time_item("2021-01-09", dummy_product)
    assert dt == datetime.date(2021, 1, 9)

    with pytest.raises(WMSException) as e:
        dt = datacube_ows.wms_utils.parse_time_item("2021-01-01", dummy_product)
    assert "Time dimension value" in str(e.value)
    assert "not valid for this layer" in str(e.value)

    with pytest.raises(WMSException) as e:
        dt = datacube_ows.wms_utils.parse_time_item("2021-01-15", dummy_product)
    assert "Time dimension value" in str(e.value)
    assert "not valid for this layer" in str(e.value)

    dummy_product.time_axis_interval = 3

    with pytest.raises(WMSException) as e:
        dt = datacube_ows.wms_utils.parse_time_item("2021-01-07", dummy_product)
    assert "Time dimension value" in str(e.value)
    assert "not valid for this layer" in str(e.value)

