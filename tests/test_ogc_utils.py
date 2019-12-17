import datacube_ows.ogc_utils

import pytest

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