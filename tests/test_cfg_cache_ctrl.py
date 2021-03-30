import pytest
from unittest.mock import MagicMock
from datacube_ows.ogc_utils import ConfigException
from datacube_ows.ows_configuration import CacheControlRules


@pytest.fixture
def ccr_min_layer():
    lyr = MagicMock()
    lyr.name = "a_layer"
    return lyr


def test_no_rules(ccr_min_layer):
    ccr = CacheControlRules(None, ccr_min_layer, 0)
    assert ccr.rules is None
    assert not ccr.use_caching
    assert ccr.cache_headers(0) == {}
    assert ccr.cache_headers(2) == {}
    assert ccr.cache_headers(10) == {}


def test_never_cache(ccr_min_layer):
    ccr = CacheControlRules([], ccr_min_layer, 8)
    assert ccr.rules == []
    assert ccr.use_caching
    assert ccr.cache_headers(0) == {"cache-control": "no-cache"}
    assert ccr.cache_headers(2) == {"cache-control": "no-cache"}
    assert ccr.cache_headers(10) == {"cache-control": "no-cache"}


def test_complex_case(ccr_min_layer):
    ccr = CacheControlRules([
        {"min_datasets": 3, "max_age": 10000},
        {"min_datasets": 8, "max_age": 20000},
    ], ccr_min_layer, 12)
    assert ccr.use_caching
    assert ccr.cache_headers(0) == {"cache-control": "no-cache"}
    assert ccr.cache_headers(2) == {"cache-control": "no-cache"}
    assert ccr.cache_headers(3) == {"cache-control": "max-age=10000"}
    assert ccr.cache_headers(7) == {"cache-control": "max-age=10000"}
    assert ccr.cache_headers(8) == {"cache-control": "max-age=20000"}
    assert ccr.cache_headers(12) == {"cache-control": "max-age=20000"}
    assert ccr.cache_headers(13) == {"cache-control": "no-cache"}


def test_no_min_datasets_element(ccr_min_layer):
    with pytest.raises(ConfigException) as e:
        ccr = CacheControlRules([
            {"max_age": 20000},
        ], ccr_min_layer, 12)
    assert "Dataset cache rule does not contain" in str(e.value)
    assert "min_datasets" in str(e.value)
    assert "a_layer" in str(e.value)


def test_no_max_age_element(ccr_min_layer):
    with pytest.raises(ConfigException) as e:
        ccr = CacheControlRules([
            {"min_datasets": 2},
        ], ccr_min_layer, 12)
    assert "Dataset cache rule does not contain" in str(e.value)
    assert "max_age" in str(e.value)
    assert "a_layer" in str(e.value)


def test_nonint_min_ds(ccr_min_layer):
    with pytest.raises(ConfigException) as e:
        ccr = CacheControlRules([
            {"min_datasets": "2", "max_age": 2000},
        ], ccr_min_layer, 12)
    assert "Dataset cache rule" in str(e.value)
    assert "min_datasets" in str(e.value)
    assert "non-integer" in str(e.value)
    assert "a_layer" in str(e.value)


def test_nonint_max_age(ccr_min_layer):
    with pytest.raises(ConfigException) as e:
        ccr = CacheControlRules([
            {"min_datasets": 2, "max_age": 2000.5},
        ], ccr_min_layer, 12)
    assert "Dataset cache rule" in str(e.value)
    assert "max_age" in str(e.value)
    assert "non-integer" in str(e.value)
    assert "a_layer" in str(e.value)


def test_negative_min_datasets(ccr_min_layer):
    with pytest.raises(ConfigException) as e:
        ccr = CacheControlRules([
            {"min_datasets": -2, "max_age": 2000},
        ], ccr_min_layer, 12)
    assert "Invalid dataset cache rule" in str(e.value)
    assert "min_datasets" in str(e.value)
    assert "must be greater than zero" in str(e.value)
    assert "a_layer" in str(e.value)


def test_unsorted_min_datasets(ccr_min_layer):
    with pytest.raises(ConfigException) as e:
        ccr = CacheControlRules([
            {"min_datasets": 4, "max_age": 2000},
            {"min_datasets": 2, "max_age": 4000},
        ], ccr_min_layer, 12)
    assert "Dataset cache rules must be sorted" in str(e.value)
    assert "ascending" in str(e.value)
    assert "min_datasets" in str(e.value)
    assert "a_layer" in str(e.value)


def test_min_datasets_max_datasets(ccr_min_layer):
    with pytest.raises(ConfigException) as e:
        ccr = CacheControlRules([
            {"min_datasets": 2, "max_age": 2000},
            {"min_datasets": 4, "max_age": 4000},
        ], ccr_min_layer, 2)
    assert "Dataset cache rule" in str(e.value)
    assert "min_datasets" in str(e.value)
    assert "exceeds the max_datasets limit" in str(e.value)
    assert "a_layer" in str(e.value)


def test_non_negative_max_age(ccr_min_layer):
    with pytest.raises(ConfigException) as e:
        ccr = CacheControlRules([
            {"min_datasets": 2, "max_age": -2},
        ], ccr_min_layer, 12)
    assert "Dataset cache rule" in str(e.value)
    assert "max_age" in str(e.value)
    assert "must be greater than zero" in str(e.value)
    assert "a_layer" in str(e.value)


def test_unsorted_max_age(ccr_min_layer):
    with pytest.raises(ConfigException) as e:
        ccr = CacheControlRules([
            {"min_datasets": 2, "max_age": 4000},
            {"min_datasets": 4, "max_age": 2000},
        ], ccr_min_layer, 12)
    assert "dataset cache rules" in str(e.value)
    assert "must increase monotonically" in str(e.value)
    assert "max_age" in str(e.value)
    assert "a_layer" in str(e.value)
