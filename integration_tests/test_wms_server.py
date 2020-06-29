import pytest
from owslib.wms import WebMapService
from urllib import request
from lxml import etree
from imghdr import what
import requests

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

        # Confirm error message is appropriate, ignore case
        if expected_error_message:
            assert resp_xml[0].text.strip().casefold() == expected_error_message.casefold()


def test_no_request(ows_server):
    # Make empty request to server:
    check_wms_error(ows_server.url + "/wms", "No operation specified", 400)


def test_invalid_operation(ows_server):
    # Make invalid operation request to server:
    check_wms_error(ows_server.url + "/wms?request=NoSuchOperation", "Unrecognised operation: NoSuchOperation", 400)


def test_getcap_badsvc(ows_server):
    # Make bad service request to server:
    check_wms_error(ows_server.url + "/wms?request=GetCapabilities&service=NotWMS", "Invalid service", 400)

@pytest.mark.xfail(reason="OWS Getcaps don't pass XSD")
def test_getcap(ows_server):
    resp = request.urlopen(ows_server.url + "/wms?request=GetCapabilities&service=WMS&version=1.3.0", timeout=10)

    # Confirm success
    assert resp.code == 200

    # Validate XML Schema
    resp_xml = etree.parse(resp.fp)
    gc_xds = get_xsd("capabilities_1_3_0.xsd")
    assert gc_xds.validate(resp_xml)


def enclosed_bbox(bbox, output_format='getmap'):
    lon_min, lat_min, lon_max, lat_max = bbox
    lon_range = lon_max - lon_min
    lat_range = lat_max - lat_min

    if output_format == 'string':
        return '{1},{0},{3},{2}'.format(
            lon_min + 0.2 * lon_range,
            lat_min + 0.2 * lat_range,
            lon_max - 0.2 * lon_range,
            lat_max - 0.2 * lat_range
        )
    return (
        lon_min + 0.2 * lon_range,
        lat_min + 0.2 * lat_range,
        lon_max - 0.2 * lon_range,
        lat_max - 0.2 * lat_range
    )


def disjoint_bbox(bbox, output_format='getmap'):
    lon_min, lat_min, lon_max, lat_max = bbox
    lon_range = lon_max - lon_min
    lat_range = lat_max - lat_min


    if output_format == 'string':
        return '{1},{0},{3},{2}'.format(
        lon_min - 0.4 * lon_range,
        lat_min - 0.4 * lat_range,
        lon_min - 0.2 * lon_range,
        lat_min - 0.2 * lat_range
        )

    return (
        lon_min - 0.4 * lon_range,
        lat_min - 0.4 * lat_range,
        lon_min - 0.2 * lon_range,
        lat_min - 0.2 * lat_range
    )

def test_wms_server(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WMS service
    wms = WebMapService(url=ows_server.url+"/wms", version="1.3.0")

    assert wms.identification.type == "WMS"

    # Ensure that we have at least some layers available
    contents = list(wms.contents)
    assert contents

def test_wms_getmap(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WMS service
    wms = WebMapService(url=ows_server.url+"/wms", version="1.3.0")

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


def test_wms_getfeatureinfo(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WMS service
    wms = WebMapService(url=ows_server.url+"/wms", version="1.3.0")

    # Ensure that we have at least some layers available
    contents = list(wms.contents)
    test_layer_name = contents[0]
    test_layer = wms.contents[test_layer_name]

    bbox = test_layer.boundingBoxWGS84
    response = wms.getfeatureinfo(
        layers=[test_layer_name],
        srs='EPSG:4326',
        bbox=enclosed_bbox(bbox),
        size=(256, 256),
        format="image/png",
        query_layers=[test_layer_name],
        info_format="application/json",
        xy=(250,250)
    )

    assert response
    assert response.info()['Content-Type'] == 'application/json'

def test_wms_getlegend(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WMS service
    wms = WebMapService(url=ows_server.url+"/wms", version="1.3.0")

    # Ensure that we have at least some layers available
    contents = list(wms.contents)
    test_layer_name = contents[0]

    test_layer_styles = wms.contents[test_layer_name].styles
    for style in test_layer_styles:
        # check if this layer has a legend
        legend_url = test_layer_styles[style].get('legend')
        if legend_url:
            resp = requests.head(legend_url, allow_redirects=False)
            assert resp.headers.get('content-type') == 'image/png'