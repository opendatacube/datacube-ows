# pylint: skip-file

import datacube
import pytest
import datetime

import xml.etree.ElementTree as et

from datacube_wms.data import get_map
import flask
import os

zoomedout_testdata = [
    (1,
     {"srs": "EPSG:3857",
      "styles": "",
      "tiled": True,
      "feature_count": 101,
      "version": "1.1.1",
      "layers": "ls8_nbart_geomedian_annual",
      "format": "image/png",
      "width": "256",
      "height": "256",
      "bbox": "13149614.84995544,-2504688.542848654,13306157.883883484,-2348145.5089206137"},
     "data/get_map_zoomedout/zoomedout_1.png"),
    (2,
     {"srs": "EPSG:3857",
      "styles": "",
      "tiled": True,
      "feature_count": 101,
      "version": "1.1.1",
      "layers": "ls8_nbart_geomedian_annual",
      "format": "image/png",
      "width": "256",
      "height": "256",
      "bbox": "12993071.8160274,-2504688.542848654,13149614.84995544,-2348145.5089206137"},
     "data/get_map_zoomedin/zoomedin_2.png"),
    (3,
     {"srs": "EPSG:3857",
      "styles": "",
      "tiled": True,
      "feature_count": 101,
      "version": "1.1.1",
      "layers": "ls8_nbart_geomedian_annual",
      "format": "image/png",
      "width": "1015",
      "height": "786",
      "bbox": "12523442.714243278,-2504688.542848654,13149614.84995544,-1878516.4071364924"},
     "data/get_map_zoomedin/zoomedin_3.png")
]


@pytest.mark.parametrize("id, test_args, expect_png", zoomedout_testdata)
def test_map_zoomedout(cube, release_cube_dummy, mocker,
                       id, test_args, expect_png):
    app = flask.Flask(
        "test",
        root_path=os.path.dirname(os.path.realpath(__file__) + "/../.."))
    with app.test_request_context('/?GetMap'):
        args = {}
        resp = get_map(test_args)
        with open(expect_png) as png:
            resp == png


zoomedin_testdata = [
    (1,
     {"srs": "EPSG:3857",
      "styles": "",
      "tiled": True,
      "feature_count": 101,
      "version": "1.1.1",
      "layers": "ls8_nbart_geomedian_annual",
      "format": "image/png",
      "width": "256",
      "height": "256",
      "bbox": "13149614.84995544,-2387281.2674026266,13188750.608437452,-2348145.5089206137"},
     "data/get_map_zoomedin/zoomedin_1.png"),
    (2,
     {"srs": "EPSG:3857",
      "styles": "",
      "tiled": True,
      "feature_count": 101,
      "version": "1.1.1",
      "layers": "ls8_nbart_geomedian_annual",
      "format": "image/png",
      "width": "256",
      "height": "256",
      "bbox": "13032207.574509412,-2426417.0258846357,13071343.332991421,-2387281.2674026266"},
     "data/get_map_zoomedin/zoomedin_2.png"),
    (3,
     {"srs": "EPSG:3857",
      "styles": "infra_red",
      "tiled": True,
      "feature_count": 101,
      "version": "1.1.1",
      "layers": "ls8_nbart_geomedian_annual",
      "format": "image/png",
      "width": "256",
      "height": "256",
      "bbox": "13071343.332991421,-2387281.2674026266,13110479.09147343,-2348145.5089206137"},
     "data/get_map_zoomedin/zoomedin_3.png"),
    (4,
     {"srs": "EPSG:3857",
      "styles": "infrared_green",
      "tiled": True,
      "feature_count": 101,
      "version": "1.1.1",
      "layers": "ls8_nbart_geomedian_annual",
      "format": "image/png",
      "width": "256",
      "height": "256",
      "bbox": "13071343.332991421,-2387281.2674026266,13110479.09147343,-2348145.5089206137"},
     "data/get_map_zoomedin/zoomedin_4.png"),
    (5,
     {"srs": "EPSG:3857",
      "styles": "infrared_green",
      "tiled": True,
      "feature_count": 101,
      "version": "1.1.1",
      "layers": "ls8_nbart_geomedian_annual",
      "format": "image/png",
      "width": "512",
      "height": "256",
      "bbox": "13071343.332991421,-2387281.2674026266,13110479.09147343,-2348145.5089206137"},
     "data/get_map_zoomedin/zoomedin_5.png"),
    (6,
     {"srs": "EPSG:3857",
      "styles": "infrared_green",
      "tiled": True,
      "feature_count": 101,
      "version": "1.1.1",
      "layers": "ls8_nbart_geomedian_annual",
      "format": "image/png",
      "width": "1017",
      "height": "257",
      "bbox": "13071343.332991421,-2387281.2674026266,13110479.09147343,-2348145.5089206137"},
     "data/get_map_zoomedin/zoomedin_6.png"),
    (7,
     {"srs": "EPSG:3577",
      "styles": "infrared_green",
      "tiled": True,
      "feature_count": 101,
      "version": "1.1.1",
      "layers": "ls8_nbart_geomedian_annual",
      "format": "image/png",
      "width": "1017",
      "height": "257",
      "bbox": "-1503093.67,-2336982.04,-1471065.71,-2296511.45"},
     "data/get_map_zoomedin/zoomedin_7.png"),
    (8,
     {"srs": "EPSG:4326",
      "styles": "infrared_green",
      "tiled": True,
      "feature_count": 101,
      "version": "1.1.1",
      "layers": "ls8_nbart_geomedian_annual",
      "format": "image/png",
      "width": "1017",
      "height": "257",
      "bbox": "-20.9614396,117.421875,-20.6327842,117.7734375"},
     "data/get_map_zoomedin/zoomedin_7.png")
]


@pytest.mark.parametrize("id, test_args, expect_png", zoomedin_testdata)
def test_map_zoomedin(cube, release_cube_dummy, mocker,
                      id, test_args, expect_png):
    app = flask.Flask(
        "test",
        root_path="/Users/robbie/dev/datacube-wms/datacube_wms")
    with app.test_request_context('/?GetMap'):
        args = {}
        resp = get_map(test_args)
        with open(expect_png) as png:
            resp == png
