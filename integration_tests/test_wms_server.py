# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from urllib import request

import pytest
import requests
from lxml import etree
from owslib.wms import WebMapService


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
            assert (
                resp_xml[0].text.strip().casefold() == expected_error_message.casefold()
            )


def test_no_request(ows_server):
    # Make empty request to server:
    check_wms_error(ows_server.url + "/wms", "No operation specified", 400)


def test_invalid_operation(ows_server):
    # Make invalid operation request to server:
    check_wms_error(
        ows_server.url + "/wms?request=NoSuchOperation",
        "Unrecognised operation: NoSuchOperation",
        400,
    )


def test_getcap_badsvc(ows_server):
    # Make bad service request to server:
    check_wms_error(
        ows_server.url + "/wms?request=GetCapabilities&service=NotWMS",
        "Invalid service",
        400,
    )


def test_getcap_xsd(ows_server):
    resp = requests.get(
        ows_server.url + "/wms?request=GetCapabilities&service=WMS&version=1.3.0",
        timeout=10,
    )

    # Confirm success
    assert resp.status_code == 200

    caps_document = resp.text

    # Validate XML Schema
    resp_xml = etree.fromstring(resp.content)
    gc_xds = get_xsd("capabilities_extensions_local.xsd")
    result = gc_xds.validate(resp_xml)
    if not result:
        assert gc_xds.error_log.last_error == caps_document
    assert gc_xds.error_log.last_error is None
    assert result


def test_getcap_response(ows_server):
    resp = request.urlopen(
        ows_server.url + "/wms?request=GetCapabilities&service=WMS&version=1.3.0",
        timeout=10,
    )

    # Confirm success
    assert resp.code == 200

    # Check cache header
    assert resp.headers["cache-control"] == "max-age=5"

    # Validate XML Schema
    resp_xml = etree.parse(resp.fp)
    root = resp_xml.getroot()
    layers = root.findall(".//{http://www.opengis.net/wms}Layer[@queryable='1']")
    for layer in layers:
        wLong = layer.findall(".//{http://www.opengis.net/wms}westBoundLongitude")[0]
        geo_bbox = layer.findall(
            "./{http://www.opengis.net/wms}BoundingBox[@CRS='EPSG:4326']"
        )[0]
        assert wLong.text == geo_bbox.attrib["miny"]


def test_wms_server(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WMS service
    wms = WebMapService(url=ows_server.url + "/wms", version="1.3.0")

    assert wms.identification.type == "WMS"

    # Ensure that we have at least some layers available
    contents = list(wms.contents)
    assert contents


def test_wms_getmap(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WMS service
    wms = WebMapService(url=ows_server.url + "/wms", version="1.3.0", timeout=120)

    # Ensure that we have at least some layers available
    contents = list(wms.contents)
    test_layer_name = contents[0]
    test_layer = wms.contents[test_layer_name]

    bbox = test_layer.boundingBoxWGS84

    for time in test_layer.timepositions:
        img = wms.getmap(
            layers=[test_layer_name],
            styles=[],
            srs="EPSG:4326",
            bbox=pytest.helpers.enclosed_bbox(bbox),
            size=(150, 150),
            format="image/png",
            transparent=True,
            time=time.strip(),
        )
        assert img
        assert img.info()["Content-Type"] == "image/png"


def test_wms_getmap_requests(ows_server, product_name):
    resp = requests.get(ows_server.url + '/wms', params={
        "service": "WMS",
        "version": "1.3.0",
        "request": "GetMap",
        "layers": product_name,
        "width": "150",
        "height": "150",
        "crs": "EPSG:4326",
        "bbox": "-15.28507087113431,123.98504300790977,-14.27072582535469,124.64289867785524",
        "format": "image/png",
        "exceptions": "XML",
        "time": "2021-12-31 02:01:38"
    })
    # Confirm success
    assert resp.status_code == 200

def test_wms_getmap_bad_requests(ows_server):
    resp = requests.get(ows_server.url + '/wms', params={
        "service": "WMS",
        "version": "1.3.0",
        "request": "GetMap",
        "layers": "s2_l2a,some_other_layer",
        "width": "150",
        "height": "150",
        "crs": "EPSG:4326",
        "bbox": "-43.28507087113431,146.18504300790977,-43.07072582535469,146.64289867785524",
        "format": "image/png",
        "exceptions": "XML",
        "time": "2019-07-09"
    })
    # Confirm success
    assert resp.status_code == 400
    assert "Multi-layer requests not supported" in resp.text
    resp = requests.get(ows_server.url + '/wms', params={
        "service": "WMS",
        "version": "1.3.0",
        "request": "GetMap",
        "layers": "not_a_real_layer",
        "width": "150",
        "height": "150",
        "crs": "EPSG:4326",
        "bbox": "-43.28507087113431,146.18504300790977,-43.07072582535469,146.64289867785524",
        "format": "image/png",
        "exceptions": "XML",
        "time": "2019-07-09"
    })
    # Confirm success
    assert resp.status_code == 400
    assert "Layer not_a_real_layer is not defined" in resp.text


def test_wms_getmap_qprof(ows_server, product_name):
    resp = requests.get(ows_server.url + '/wms', params={
                            "service": "WMS",
                            "version": "1.3.0",
                            "request": "GetMap",
                            "layers": product_name,
                            "width": "150",
                            "height": "150",
                            "crs": "EPSG:4326",
                            "bbox": "-15.28507087113431,123.98504300790977,-14.27072582535469,124.64289867785524",
                            "format": "image/png",
                            "exceptions": "XML",
                            "time": "2021-12-31 02:01:38",
                            "ows_stats": "yes"
    })
    # Confirm success
    assert resp.status_code == 200
    js = resp.json()
    assert js["info"]["zoom_factor"] > 0.0


def test_wms_multiproduct_getmap(ows_server, multiproduct_name):
    # Use owslib to confirm that we have a somewhat compliant WMS service
    wms = WebMapService(url=ows_server.url + "/wms", version="1.3.0", timeout=120)

    # Run test against dedicated multiproduct
    test_layer = wms.contents[multiproduct_name]

    bbox = test_layer.boundingBoxWGS84

    img = wms.getmap(
        layers=[multiproduct_name],
        styles=[],
        srs="EPSG:3577",
        bbox=pytest.helpers.enclosed_bbox(bbox),
        size=(150, 150),
        format="image/png",
        transparent=True,
        time=test_layer.timepositions[len(test_layer.timepositions) // 2].strip(),
    )
    assert img
    assert img.info()["Content-Type"] == "image/png"


def test_wms_multidate_getmap(ows_server):
    # This one will only work with specially prepared test data, sorry.
    wms = WebMapService(url=ows_server.url + "/wms", version="1.3.0", timeout=120)

    img = wms.getmap(
        layers=["s2_l2a"],
        styles=["ndvi_delta"],
        srs="EPSG:4326",
        bbox=(122.32, -15.25,
              124.64, -12.66),
        size=(150, 150),
        format="image/png",
        transparent=True,
        time="2021-12-31 02:01:38,2022-01-03 02:11:03",
    )
    assert img.info()["Content-Type"] == "image/png"


def test_wms_style_looping_getmap(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WMS service
    wms = WebMapService(url=ows_server.url + "/wms", version="1.3.0", timeout=120)

    # Ensure that we have at least some layers available
    contents = list(wms.contents)
    test_layer_names = ["s2_l2a", "s2_l2a_clone"]
    test_time = '2021-12-21T02:01:19'
    for test_layer_name in test_layer_names:
        test_layer = wms.contents[test_layer_name]

        test_layer_styles = wms.contents[test_layer_name].styles

        bbox = test_layer.boundingBoxWGS84
        layer_bbox = pytest.helpers.enclosed_bbox(bbox)

        for style in test_layer_styles:
            img = wms.getmap(
                layers=[test_layer_name],
                styles=[style],
                srs="EPSG:4326",
                bbox=layer_bbox,
                size=(150, 150),
                format="image/png",
                transparent=True,
                time=test_time,
            )
            assert img.info()["Content-Type"] == "image/png"


def test_wms_getfeatureinfo(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WMS service
    wms = WebMapService(url=ows_server.url + "/wms", version="1.3.0", timeout=300)

    # Ensure that we have at least some layers available
    contents = list(wms.contents)
    for test_layer_name in contents:
        test_layer = wms.contents[test_layer_name]

        test_times = test_layer.timepositions
        if test_times is None:
            test_times = [None]
        elif len(test_times) > 8:
            test_times = [test_times[0], test_times[6], test_times[-1]]
        elif len(test_times) == 1 and '/' in test_times[0]:
            test_times = test_times[0].split('/')
            test_times = list(test_times[0:2])
        for test_time in test_times:
            bbox = test_layer.boundingBoxWGS84
            response = wms.getfeatureinfo(
                layers=[test_layer_name],
                srs="EPSG:4326",
                bbox=pytest.helpers.enclosed_bbox(bbox),
                size=(256, 256),
                format="image/png",
                query_layers=[test_layer_name],
                info_format="application/json",
                times=test_time,
                xy=(250, 250),
            )

            assert response
            assert response.info()["Content-Type"] == "application/json"

            response = wms.getfeatureinfo(
                layers=[test_layer_name],
                srs="EPSG:4326",
                bbox=pytest.helpers.enclosed_bbox(bbox),
                size=(256, 256),
                format="image/png",
                query_layers=[test_layer_name],
                info_format="text/html",
                times=test_time,
                xy=(250, 250),
            )

            assert response
            assert response.info()["Content-Type"] == "text/html"


def test_custom_feature_info(ows_server, product_name):
    wms = WebMapService(url=ows_server.url + "/wms", version="1.3.0", timeout=300)

    test_layer = wms.contents[product_name]
    query_times = ['2021-12-21T02:01:19', '2021-12-26T02:01:29']
    bbox = test_layer.boundingBoxWGS84
    response = requests.get(ows_server.url + '/wms', params={
        "service": "WMS",
        "version": "1.3.0",
        "request": "GetFeatureInfo",
        "query_layers": product_name,
        "width": "256",
        "height": "256",
        "crs": "EPSG:4326",
        "bbox": ",".join(str(f) for f in pytest.helpers.enclosed_bbox(bbox, flip=True)),
        "info_format": "application/json",
        "feature_count": "20",
        "styles": "ndvi_delta",
        "time": ",".join(query_times),
        "i": "250",
        "j": "250",
    })
    js = response.json()
    feature = js["features"][0]
    data = feature["properties"]["data"]
    for time_slice in data:
        if time_slice["time"] == "all":
            assert "red_diff" in time_slice
            assert "nir_diff" in time_slice
        else:
            assert "Sen2Cor Scene Classification" in time_slice["legacy_data"]["SCL"]
            assert time_slice["legacy_data"]["red_edge_2"] > 0
            assert "SCL" in time_slice["override"]
            assert "B8A" in time_slice["override"]
            assert time_slice["platform"] in ("sentinel-2a", "sentinel-2b")


def test_wms_getlegend(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WMS service
    wms = WebMapService(url=ows_server.url + "/wms", version="1.3.0")

    # Ensure that we have at least some layers available
    contents = list(wms.contents)
    test_layer_name = contents[0]

    test_layer_styles = wms.contents[test_layer_name].styles
    for style in test_layer_styles:
        # check if this layer has a legend
        legend_url = test_layer_styles[style].get("legend")
        if legend_url:
            resp = requests.head(legend_url, headers={
                                "Accept-Language": "en-US,en,q=0.7"
                            },
                            allow_redirects=False
            )
            assert resp.headers.get("content-type") == "image/png"
            resp = requests.head(legend_url, headers={
                                "Accept-Language": "sw,sw,q=0.7"
                            },
                        allow_redirects=False
            )
            assert resp.headers.get("content-type") == "image/png"


def test_wms_getlegendgraphic(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WMS service
    wms = WebMapService(url=ows_server.url + "/wms", version="1.3.0")

    # Ensure that we have at least some layers available
    contents = list(wms.contents)
    test_layer_name = contents[0]

    test_layer_styles = wms.contents[test_layer_name].styles
    for style in test_layer_styles:
        # check if this layer has a legend
        legend_url = test_layer_styles[style].get("legend")
        url = ows_server.url + "/wms"
        resp = requests.get(
            url,
            allow_redirects=False,
            params={
                "request": "GetLegendGraphic",
                "layer": test_layer_name,
                "version": "1.3.0",
                "service": "WMS",
                "styles": style,
                "format": "image/png",
            },
        )
        if legend_url:
            assert resp.headers.get("content-type") == "image/png"
            assert resp.status_code == 200
        else:
            assert resp.status_code == 404
