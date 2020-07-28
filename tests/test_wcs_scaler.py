import pytest

from datacube_ows.ows_configuration import OWSProductLayer, OWSConfig
from datacube_ows.wcs_scaler import WCSScaler, SpatialParameter
from datacube_ows.wcs_scaler import WCSScalerUnknownDimension, WCSScalerException, WCSScalerOverspecifiedDimension, WCSScalarIllegalSize

@pytest.fixture
def layer_crs_mock():
    product_layer = OWSProductLayer.__new__(OWSProductLayer)
    product_layer.name = "test_layer"
    product_layer.global_cfg = OWSConfig.__new__(OWSConfig)
    product_layer.global_cfg.published_CRSs = {
        "EPSG:3857": {  # Web Mercator
            "geographic": False,
            "horizontal_coord": "x",
            "vertical_coord": "y",
            "vertical_coord_first": False,
            "gml_name": "http://www.opengis.net/def/crs/EPSG/0/3857"
        },
        "EPSG:4326": {  # WGS-84
            "geographic": True,
            "vertical_coord_first": True,
            "horizontal_coord": "longitude",
            "vertical_coord": "latitude",
            "gml_name": "http://www.opengis.net/def/crs/EPSG/0/4326"
        },
        "EPSG:3577": {
            "geographic": False,
            "horizontal_coord": "x",
            "vertical_coord": "y",
            "vertical_coord_first": False,
            "gml_name": "http://www.opengis.net/def/crs/EPSG/0/3577"
        },
        "TEST:CRS": {
            "geographic": False,
            "horizontal_coord": "horrible_zonts",
            "vertical_coord": "vertex_calories",
            "vertical_coord_first": False,
            "gml_name": "TEST/CRS"
        },
        "TEST:NATIVE_CRS": {
            "geographic": False,
            "horizontal_coord": "hortizonal_cults",
            "vertical_coord": "verbal_tics",
            "vertical_coord_first": False,
            "gml_name": "TEST/NATIVE_CRS"
        },
    }
    product_layer.native_CRS_def = {
        "geographic": False,
        "horizontal_coord": "hortizonal_cults",
        "vertical_coord": "verbal_tics",
        "vertical_coord_first": False,
        "gml_name": "TEST/NATIVE_CRS"
    }
    return product_layer
def test_spatial_parameter(layer_crs_mock):
    param1 = SpatialParameter(layer_crs_mock, "TEST:CRS")
    assert param1.y is None
    assert param1.x is None
    assert param1["x"] is None
    assert param1["y"] is None

    param1.set(7, -13)
    assert param1.x == 7
    assert param1.y == -13
    assert param1.longitude == 7
    assert param1.latitude == -13
    assert param1.i == 7
    assert param1.j == -13
    assert param1.horrible_zonts == 7
    assert param1.vertex_calories == -13
    assert param1.hortizonal_cults == 7
    assert param1.verbal_tics == -13
    try:
       _ = param1.horivertal_calzones
       assert "Should have thrown a WCSScalarUnknownDimension" == False
    except WCSScalerUnknownDimension as e:
       assert e.dim == "horivertal_calzones"

    param2 = SpatialParameter(layer_crs_mock, "EPSG:3577",
                              x=2, y=-7)
    assert param2.y == -7
    assert param2.x == 2

    param2.long = 22
    param2.lat = -77

    assert param2.lat == -77
    assert param2.long == 22
    assert param2.hortizonal_cults == 22
    assert param2.verbal_tics == -77

    try:
        _ = param2.horrible_zonts
        assert "Should have thrown a WCSScalarUnknownDimension" == False
    except WCSScalerUnknownDimension as e:
        assert e.dim == "horrible_zonts"
