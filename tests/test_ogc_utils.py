from unittest.mock import MagicMock

import datacube_ows.ogc_utils
import datetime

import pytest

class DSCT:
    def __init__(self, meta):
        self.center_time = datetime.datetime(1970,1,1,0,0,0)
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
    allowed_urls = ["https://foo.hello.world","https://foo.bar.baz", "https://alice.bob.eve"]
    request_url = "https://foo.bar.baz"
    ret = datacube_ows.ogc_utils.get_service_base_url(allowed_urls, request_url)
    assert ret == "https://foo.bar.baz"

    # Trailing /
    allowed_urls = ["https://foo.bar.baz", "https://alice.bob.eve"]
    request_url = "https://foo.bar.baz/"
    ret = datacube_ows.ogc_utils.get_service_base_url(allowed_urls, request_url)
    assert ret == "https://foo.bar.baz"

    #include path
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