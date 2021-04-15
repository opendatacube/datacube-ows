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
