import datacube_wms.ogc_utils

import pytest

def test_get_service_base_url():

    # not a list
    allowed_urls = "https://foo.hello.world"
    request_url = "https://foo.bar.baz"
    ret = datacube_wms.ogc_utils.get_service_base_url(allowed_urls, request_url)
    assert ret == "https://foo.hello.world"

    # Value not in list
    allowed_urls = ["https://foo.hello.world", "https://alice.bob.eve"]
    request_url = "https://foo.bar.baz"
    ret = datacube_wms.ogc_utils.get_service_base_url(allowed_urls, request_url)
    assert ret == "https://foo.hello.world"

    # Value in list
    allowed_urls = ["https://foo.hello.world","https://foo.bar.baz", "https://alice.bob.eve"]
    request_url = "https://foo.bar.baz"
    ret = datacube_wms.ogc_utils.get_service_base_url(allowed_urls, request_url)
    assert ret == "https://foo.bar.baz"

    # Trailing /
    allowed_urls = ["https://foo.bar.baz", "https://alice.bob.eve"]
    request_url = "https://foo.bar.baz/"
    ret = datacube_wms.ogc_utils.get_service_base_url(allowed_urls, request_url)
    assert ret == "https://foo.bar.baz"

