import requests


def test_wms_i18n(ows_server):
    resp = requests.get(
        ows_server.url + "/wms?request=GetCapabilities&service=WMS&version=1.3.0",
        timeout=10,
        headers={"Accept-Language": "de"}
    )
    # Confirm successf
    assert "German translation" in resp.text

def test_wcs1_i18n(ows_server):
    resp = requests.get(
        ows_server.url + "/wcs?request=GetCapabilities&service=WCS&version=1.0.0",
        timeout=10,
        headers={"Accept-Language": "de"}
    )
    # Confirm success
    assert "German translation" in resp.text


def test_wcs1_bands_i18n(ows_server):
    resp = requests.get(
        ows_server.url + "/wcs?request=DescribeCoverage&service=WCS&version=1.0.0&coverageid=s2_l2a",
        timeout=10,
        headers={"Accept-Language": "de"}
    )
    # Confirm success
    assert "gruen" in resp.text


def test_wcs2_i18n(ows_server):
    resp = requests.get(
        ows_server.url + "/wcs?request=GetCapabilities&service=WCS&version=2.0.1",
        timeout=10,
        headers={"Accept-Language": "de"}
    )
    # Confirm success
    assert "German translation" in resp.text


def test_wcs2_bands_i18n(ows_server):
    resp = requests.get(
        ows_server.url + "/wcs?request=DescribeCoverage&service=WCS&version=2.0.1&coverageid=s2_l2a",
        timeout=10,
        headers={"Accept-Language": "de"}
    )
    # Confirm success
    assert "gruen" in resp.text
