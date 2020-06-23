from datacube_ows import ogc

import pytest
from pytest_localserver.http import WSGIServer
from owslib.wms import WebMapService
from urllib import request
from lxml import etree
from imghdr import what

import os


class generic_obj(object):
    pass


@pytest.fixture
def wms_server(request):
    """
    Run the WMS server for the duration of these tests
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
    xsd_f = open("wms_xsds/" + name)
    schema_doc = etree.parse(xsd_f)

    return etree.XMLSchema(schema_doc)


def check_wms_error(url, expected_error_message=None, expected_status_code=400):
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
        ex_xsd = get_xsd("exceptions_1_3_0.xsd")
        assert ex_xsd.validate(resp_xml)

        # Confirm error message is appropriate
        if expected_error_message:
            assert resp_xml[0].text.strip() == expected_error_message


def test_no_request(wms_server):
    # Make empty request to server:
    check_wms_error(wms_server.url + "/", "No operation specified", 400)


def test_invalid_operation(wms_server):
    # Make invalid operation request to server:
    check_wms_error(wms_server.url + "/?request=NoSuchOperation", "Unrecognised operation: NoSuchOperation", 400)


def test_getcap_badsvc(wms_server):
    # Make bad service request to server:
    check_wms_error(wms_server.url + "/?request=GetCapabilities&service=NotWMS", "Invalid service", 400)


def test_getcap(wms_server):
    resp = request.urlopen(wms_server.url + "/?request=GetCapabilities&service=WMS", timeout=10)

    # Confirm success
    assert resp.code == 200

    # Validate XML Schema
    resp_xml = etree.parse(resp.fp)
    gc_xds = get_xsd("capabilities_1_3_0.xsd")
    assert gc_xds.validate(resp_xml)


def enclosed_bbox(bbox):
    lon_min, lat_min, lon_max, lat_max = bbox
    lon_range = lon_max - lon_min
    lat_range = lat_max - lat_min

    return (
        lon_min + 0.2 * lon_range,
        lat_min + 0.2 * lat_range,
        lon_max - 0.2 * lon_range,
        lat_max - 0.2 * lat_range
    )


def disjoint_bbox(bbox):
    lon_min, lat_min, lon_max, lat_max = bbox
    lon_range = lon_max - lon_min
    lat_range = lat_max - lat_min

    return (
        lon_min - 0.4 * lon_range,
        lat_min - 0.4 * lat_range,
        lon_min - 0.2 * lon_range,
        lat_min - 0.2 * lat_range
    )


def test_wms_server(wms_server):
    # Use owslib to confirm that we have a somewhat compliant WMS service
    wms = WebMapService(url=wms_server.url, version="1.3.0")

    assert wms.identification.type == "WMS"

    # Ensure that we have at least some layers available
    contents = list(wms.contents)
    assert contents


def test_wms_getmap(wms_server):
    # Use owslib to confirm that we have a somewhat compliant WMS service
    wms = WebMapService(url=wms_server.url, version="1.3.0")

    # Ensure that we have at least some layers available
    contents = list(wms.contents)
    test_layer_name = contents[0]
    test_layer = wms.contents[test_layer_name]

    bbox = test_layer.boundingBoxWGS84

    img = wms.getmap(layers=[test_layer_name],
                     styles=[],
                     srs="EPSG:4326",
                     bbox=enclosed_bbox(bbox),
                     size=(256, 256),
                     format="image/png",
                     transparent=True,
                     time=test_layer.timepositions[len(test_layer.timepositions) // 2].strip(),
                     )
    assert img
    assert what("", h=img.read()) == "png"

    img = wms.getmap(layers=[test_layer_name],
                     styles=[],
                     srs="EPSG:4326",
                     bbox=disjoint_bbox(bbox),
                     size=(256, 256),
                     format="image/png",
                     transparent=True,
                     time=test_layer.timepositions[len(test_layer.timepositions) // 2].strip(),
                     )
    assert img
    assert what("", h=img.read()) == "png"
