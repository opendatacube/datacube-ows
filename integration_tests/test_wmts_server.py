# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from urllib import request

import requests
import pytest
from lxml import etree
from owslib.util import ServiceException
from owslib.wmts import WebMapTileService


def get_xsd(name):
    # since this function is only being called by getcapabilities set to wmts/1.0.0
    # the exception schema is available from http://schemas.opengis.net/ows/1.1.0/
    xsd_f = request.urlopen("http://schemas.opengis.net/wmts/1.0/" + name)
    schema_doc = etree.parse(xsd_f)
    return etree.XMLSchema(schema_doc)


def check_wmts_error(url, expected_error_message=None, expected_status_code=400):
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
    check_wmts_error(ows_server.url + "/wmts", "No operation specified", 400)


def test_invalid_operation(ows_server):
    # Make invalid operation request to server:
    check_wmts_error(
        ows_server.url + "/wmts?request=NoSuchOperation",
        "Unrecognised operation: NOSUCHOPERATION",
        400,
    )


def test_getcap_badsvc(ows_server):
    # Make bad service request to server:
    check_wmts_error(
        ows_server.url + "/wmts?request=GetCapabilities&service=NotWMTS",
        "Invalid service",
        400,
    )


@pytest.mark.xfail(reason="OWS Getcaps don't pass XSD")
def test_wmts_getcap(ows_server):
    resp = request.urlopen(
        ows_server.url + "/wmts?request=GetCapabilities&service=WMTS&version=1.0.0",
        timeout=10,
    )

    # Confirm success
    assert resp.code == 200

    # Validate XML Schema
    resp_xml = etree.parse(resp.fp)
    gc_xds = get_xsd("wmtsGetCapabilities_response.xsd")
    assert gc_xds.validate(resp_xml)


def test_wmts_getcap_section(ows_server):
    section_options = [
        "all",
        "serviceidentification",
        "serviceprovider",
        "operationsmetadata",
        "contents",
        "themes",
    ]
    for section in section_options:
        resp = request.urlopen(
            ows_server.url
            + "/wmts?request=GetCapabilities&service=WMTS&version=1.0.0&section={}".format(
                section
            ),
            timeout=10,
        )

        # Confirm success
        assert resp.code == 200


def test_wmts_server(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wmts = WebMapTileService(url=ows_server.url + "/wmts")

    assert wmts.identification.type == "OGC WMTS"
    assert wmts.identification.version == "1.0.0"

    # Ensure that we have at least some layers available
    contents = list(wmts.contents)
    assert contents


def test_wmts_gettile(ows_server):
    wmts = WebMapTileService(url=ows_server.url + "/wmts")

    contents = list(wmts.contents)
    test_layer_name = contents[0]

    tile = wmts.gettile(
        layer=test_layer_name,
        tilematrixset="WholeWorld_WebMercator",
        tilematrix="0",
        row=0,
        column=0,
        format="image/png",
    )

    assert tile
    assert tile.info()["Content-Type"] == "image/png"

def test_wmts_getfeatinfo(ows_server):
    url = ows_server.url + ("wmts?SERVICE=WMTS&REQUEST=GetFeatureInfo&VERSION=1.0.0&" +
                            "LAYER=ls8_usgs_level1_scene_layer&STYLE=simple_rgb&" +
                            "TILEMATRIXSET=WholeWorld_WebMercator&TILEMATRIX=13&" +
                            "TILEROW=5171&TILECOL=7458&I=102&J=204&INFOFORMAT=application%2Fjson")
    resp = requests.get(url)
    assert resp
    assert resp.headers["content-type"] == "application/json"
    js = resp.json()
    assert js


def test_wmts_gettile_wkss(ows_server):
    wmts = WebMapTileService(url=ows_server.url + "/wmts")

    contents = list(wmts.contents)
    test_layer_name = contents[0]

    tile = wmts.gettile(
        layer=test_layer_name,
        tilematrixset="urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible",
        tilematrix="0",
        row=0,
        column=0,
        format="image/png",
    )

    assert tile
    assert tile.info()["Content-Type"] == "image/png"


def test_wmts_gettile_exception(ows_server):
    wmts = WebMapTileService(url=ows_server.url + "/wmts")

    contents = list(wmts.contents)
    test_layer_name = contents[0]
    try:
        # supplying an unsupported tilematrixset
        wmts.gettile(
            layer=test_layer_name,
            tilematrixset="WholeWorld_WebMercatorxxx",
            tilematrix="0",
            row=0,
            column=0,
            format="image/png",
        )
    except ServiceException as e:
        assert "Invalid Tile Matrix Set:" in str(e)
    else:
        assert False
