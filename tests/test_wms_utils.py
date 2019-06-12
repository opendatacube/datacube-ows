import datacube_ows.wms_utils


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
