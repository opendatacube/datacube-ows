from datacube_ows import ogc

import pytest
from pytest_localserver.http import WSGIServer
from owslib.wcs import WebCoverageService
from urllib import request
from lxml import etree
from imghdr import what

import os


class generic_obj(object):
    pass


@pytest.fixture
def wcs_server(request):
    """
    Run the WCS server for the duration of these tests
    """
    external_url = os.environ.get("SERVER_URL")
    if external_url:
        server = generic_obj()
        server.url = external_url
    else:
        server = WSGIServer(application=ogc.app)
        server.start()
        request.addfinalizer(server.stop)

    return server

def get_xsd(name):
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
        resp_xml = etree.XML(resp_content)

        # Validate response against Schema
        ex_xsd = get_xsd("OGC-exception.xsd")
        assert ex_xsd.validate(resp_xml)

        # Confirm error message is appropriate, ignore case
        if expected_error_message:
            assert resp_xml[0].text.strip().casefold() == expected_error_message.casefold()


def test_no_request(wcs_server):
    # Make empty request to server:
    check_wcs_error(wcs_server.url + "/wcs", "No operation specified", 400)


def test_invalid_operation(wcs_server):
    # Make invalid operation request to server:
    check_wcs_error(wcs_server.url + "/wcs?request=NoSuchOperation", "Unrecognised operation: NoSuchOperation", 400)


def test_getcap_badsvc(wcs_server):
    # Make bad service request to server:
    check_wcs_error(wcs_server.url + "/wcs?request=GetCapabilities&service=NotWCS", "Invalid service", 400)


@pytest.mark.xfail(reason="OWS Getcaps don't pass XSD")
def test_getcap(wcs_server):
    resp = request.urlopen(wcs_server.url + "/wcs?request=GetCapabilities&service=WCS&version=1.3.0", timeout=10)

    # Confirm success
    assert resp.code == 200

    # Validate XML Schema
    resp_xml = etree.parse(resp.fp)
    gc_xds = get_xsd("wcsCapabilities.xsd")
    assert gc_xds.validate(resp_xml)


def test_wcs_server(wcs_server):
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=wcs_server.url+"/wcs", version="2.0.1")

    # Ensure that we have at least some layers available
    contents = list(wcs.contents)
    assert contents
