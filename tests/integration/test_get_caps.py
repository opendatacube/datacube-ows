# pylint: skip-file

import datacube
import pytest
import datetime
import os

import xml.etree.ElementTree as et

from datacube_wms.wms import get_capabilities
import flask
import os


def test_caps(cube, release_cube_dummy, mocker):
    mocker.patch('datacube_wms.data.get_cube', cube)
    mocker.patch('datacube_wms.wms_layers.get_cube', cube)
    mocker.patch('datacube_wms.data.release_cube', release_cube_dummy)
    mocker.patch('datacube_wms.wms_layers.release_cube', release_cube_dummy)

    app = flask.Flask(
        "test",
        root_path=os.path.dirname(os.path.realpath(__file__) + "/../.."))
    with app.test_request_context('/?GetCapabilities'):
        resp = get_capabilities(None)
        root = et.fromstring(resp[0])

        query_layers = root.findall(
            ".//{http://www.opengis.net/wms}Layer[@queryable]")
        assert len(query_layers) == 1
        names = [
            t.find("{http://www.opengis.net/wms}Name").text for t in query_layers]
        assert "ls8_nbart_geomedian_annual" in names
        assert query_layers[0].find(
            "./{http://www.opengis.net/wms}EX_GeographicBoundingBox/{http://www.opengis.net/wms}westBoundLongitude").text == "117.38198877598595"
        assert query_layers[0].find(
            "./{http://www.opengis.net/wms}EX_GeographicBoundingBox/{http://www.opengis.net/wms}eastBoundLongitude").text == "118.45187549676838"
        assert query_layers[0].find(
            "./{http://www.opengis.net/wms}EX_GeographicBoundingBox/{http://www.opengis.net/wms}southBoundLatitude").text == "-21.625127734743167"
        assert query_layers[0].find(
            "./{http://www.opengis.net/wms}EX_GeographicBoundingBox/{http://www.opengis.net/wms}northBoundLatitude").text == "-20.63475508625344"
        boundingbox_3577 = query_layers[0].find(
            "./{http://www.opengis.net/wms}BoundingBox[@CRS='EPSG:3577']")
        assert boundingbox_3577.get("minx") == "-1500000.0"
        assert boundingbox_3577.get("maxx") == "-1400000.0"
        assert boundingbox_3577.get("miny") == "-2400000.0"
        assert boundingbox_3577.get("maxy") == "-2300000.0"
        boundingbox_3857 = query_layers[0].find(
            "./{http://www.opengis.net/wms}BoundingBox[@CRS='EPSG:3857']")
        assert boundingbox_3857.get("minx") == "13066903.218844512"
        assert boundingbox_3857.get("maxx") == "13186002.4638085"
        assert boundingbox_3857.get("miny") == "-2466576.4072137373"
        assert boundingbox_3857.get("maxy") == "-2348379.93955229"
        boundingbox_4326 = query_layers[0].find(
            "./{http://www.opengis.net/wms}BoundingBox[@CRS='EPSG:4326']")
        assert boundingbox_4326.get("minx") == "-21.625127734743167"
        assert boundingbox_4326.get("maxx") == "-20.63475508625344"
        assert boundingbox_4326.get("miny") == "117.38198877598595"
        assert boundingbox_4326.get("maxy") == "118.45187549676838"
        time = query_layers[0].find(
            "./{http://www.opengis.net/wms}Dimension[@name='time']")
        assert time.get("units") == "ISO8601"
        assert "2015-01-01" in time.text
