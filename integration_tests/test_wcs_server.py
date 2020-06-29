import pytest

from owslib.wcs import WebCoverageService
from urllib import request
from lxml import etree
from imghdr import what


def get_xsd(name):
    # TODO: Get XSD's for different versions
    xsd_f = request.urlopen("http://schemas.opengis.net/wcs/1.0.0/" + name)
    schema_doc = etree.parse(xsd_f)

    return etree.XMLSchema(schema_doc)


def check_wcs_error(url, expected_error_message=None, expected_status_code=400):
    try:
        resp = request.urlopen(url, timeout=10)

        # Should not get here
        assert False
    except Exception as e:
        # Validate status code
        assert e.getcode() == expected_status_code

        resp_content = e.fp.read()
        assert expected_error_message in str(resp_content)
        resp_xml = etree.XML(resp_content)
        assert resp_xml is not None


def test_no_request(ows_server):
    # Make empty request to server:
    check_wcs_error(ows_server.url + "/wcs", "No operation specified", 400)


def test_invalid_operation(ows_server):
    # Make invalid operation request to server:
    check_wcs_error(ows_server.url + "/wcs?request=NoSuchOperation", "Unrecognised operation: NOSUCHOPERATION", 400)


def test_getcap_badsvc(ows_server):
    # Make bad service request to server:
    check_wcs_error(ows_server.url + "/wcs?request=GetCapabilities&service=NotWCS", "Invalid service", 400)


def test_getcap(ows_server):
    resp = request.urlopen(ows_server.url + "/wcs?request=GetCapabilities&service=WCS&version=1.0.0", timeout=10)

    # Confirm success
    assert resp.code == 200

    # Validate XML Schema
    resp_xml = etree.parse(resp.fp)
    gc_xds = get_xsd("wcsCapabilities.xsd")
    assert gc_xds.validate(resp_xml)

def test_wcs1_server(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0")

    # Ensure that we have at least some layers available
    contents = list(wcs.contents)
    assert contents


@pytest.mark.xfail(reason="GetCoverage BaseURL is confused")
def test_wcs1_getcoverage(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0")

    # Ensure that we have at least some layers available
    contents = list(wcs.contents)
    output = wcs.getCoverage(identifier=contents[0], format='GeoTIFF', bbox=(10,40,18,45), crs='EPSG:4326', width=400, height=300)

    assert output

def test_wcs1_pattern_generated_getcoverage(ows_server):
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0")

    contents = list(wcs.contents)
    test_layer_name = contents[0]

    import requests
    resp = requests.head(ows_server.url +"/wcs?version=1.0.0&request=GetCoverage&service=WCS&Coverage={}&BBox=10%2C40%2C18%2C45&crs=EPSG%3A4326&format=GeoTIFF&width=1024&height=415".format(
        test_layer_name
    ), timeout=10)

    assert resp.headers.get('content-type') == 'image/geotiff'

def test_wcs20_server(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="2.0.0")

    # Ensure that we have at least some layers available
    contents = list(wcs.contents)
    assert contents

@pytest.mark.xfail(reason="returns 500")
def test_wcs20_pattern_generated_getcoverage(ows_server):
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="2.0.0")

    contents = list(wcs.contents)
    test_layer_name = contents[0]

    import requests
    resp = requests.head(ows_server.url +"/wcs?version=2.0.0&request=GetCoverage&service=WCS&coverageid={}&subsettingcrs=EPSG%3A4326&format=image/geotiff&scalesize=x(1024),y(415)&subset=y(40,45)&subset=x(10,18)".format(
        test_layer_name
    ), timeout=10)

    assert resp.headers.get('content-type') == 'image/geotiff'


def test_wcs21_server(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="2.0.1")

    # Ensure that we have at least some layers available
    contents = list(wcs.contents)
    assert contents
