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
    product_layer.native_CRS = "TEST:NATIVE_CRS"
    product_layer.native_CRS_def = \
        product_layer.global_cfg.published_CRSs[
            product_layer.native_CRS
        ]
    return product_layer


def test_spatial_parameter_defaults(layer_crs_mock):
    param = SpatialParameter(layer_crs_mock, "TEST:CRS")
    assert param.y is None
    assert param.x is None
    assert param["x"] is None
    assert param["y"] is None


def test_spatial_parameter_set(layer_crs_mock):
    param = SpatialParameter(layer_crs_mock, "TEST:CRS")
    param.set(7, -13)
    assert param.x == 7
    assert param.y == -13


def test_spatial_parameter_init(layer_crs_mock):
    param = SpatialParameter(layer_crs_mock, "TEST:CRS", 7, -13)
    assert param.x == 7
    assert param.y == -13


def test_spatial_parameter_setters(layer_crs_mock):
    param = SpatialParameter(layer_crs_mock, "TEST:CRS")
    param.lng = 7
    param.lat = -13
    assert param.x == 7
    assert param.y == -13

def test_spatial_parameter_isdim_1(layer_crs_mock):
    param = SpatialParameter(layer_crs_mock, "TEST:CRS", 7, -13)
    assert param.x == 7
    assert param.y == -13
    assert param.longitude == 7
    assert param.latitude == -13
    assert param.i == 7
    assert param.j == -13
    assert param.horrible_zonts == 7
    assert param.vertex_calories == -13
    assert param.hortizonal_cults == 7
    assert param.verbal_tics == -13
    try:
       _ = param.horivertal_calzones
       assert "Should have thrown a WCSScalarUnknownDimension" == False
    except WCSScalerUnknownDimension as e:
       assert e.dim == "horivertal_calzones"

def test_spatial_parameter_isdim_1(layer_crs_mock):
    param = SpatialParameter(layer_crs_mock, "EPSG:3577", 2, 7)

    assert param.lat == 7
    assert param.long == 2
    assert param.hortizonal_cults == 2
    assert param.verbal_tics == 7

    try:
        _ = param.horrible_zonts
        assert "Should have thrown a WCSScalarUnknownDimension" == False
    except WCSScalerUnknownDimension as e:
        assert e.dim == "horrible_zonts"

def test_scaler_constructor(layer_crs_mock):
    scaler = WCSScaler(layer_crs_mock)
    assert scaler.crs == "TEST:NATIVE_CRS"
    assert scaler.crs_def["gml_name"] == "TEST/NATIVE_CRS"
    scaler = WCSScaler(layer_crs_mock, "EPSG:3577")
    assert scaler.crs == "EPSG:3577"

def test_scalar_trim(layer_crs_mock):
    scaler = WCSScaler(layer_crs_mock)
    scaler.trim("x", 5, 10)
    assert scaler.dim("x") == (None, 5, 10)
    assert scaler.subsetted.x
    assert not scaler.is_slice("x")
    assert scaler.dim("y") == (None, None, None)
    assert not scaler.subsetted.y
    assert not scaler.is_slice("y")

def test_scalar_slice(layer_crs_mock):
    scaler = WCSScaler(layer_crs_mock)
    scaler.slice("y", 5)
    assert scaler.dim("y") == (None, 5, 5)
    assert scaler.subsetted.y
    assert scaler.is_slice("y")
    assert scaler.dim("x") == (None, None, None)
    assert not scaler.subsetted.x
    assert not scaler.is_slice("x")

