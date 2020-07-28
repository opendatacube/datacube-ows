import datetime

from affine import Affine

import pytest

from datacube_ows.ows_configuration import OWSProductLayer, OWSConfig
from datacube_ows.wcs_scaler import WCSScaler, SpatialParameter
from datacube_ows.wcs_scaler import WCSScalerUnknownDimension, WCSScalerException, WCSScalerOverspecifiedDimension, WCSScalarIllegalSize

@pytest.fixture
def layer_crs_nongeom():
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


@pytest.fixture
def layer_crs_geom():
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
    }
    product_layer.native_CRS = "EPSG:3577"
    product_layer.native_CRS_def = \
        product_layer.global_cfg.published_CRSs[
            product_layer.native_CRS
        ]
    product_layer.grids = {
        'EPSG:3857': {
            'origin': (12324052.573696733, -5742240.963567746),
            'resolution': (24.631092099500425, -27.828535092231032)
        },
        'EPSG:4326': {
            'origin': (-8.95553593506657, 157.105656164263),
            'resolution': (-0.00017552732376162043, 0.0002723248887547909)
        },
        'EPSG:3577': {
            'origin': (-2407984.8524648934, -5195512.771063174),
            'resolution': (25, -25)
        },
    }
    times = [datetime.date(2013, 1, 1), datetime.date(2014, 1, 1), datetime.date(2015, 1, 1),
              datetime.date(2016, 1, 1), datetime.date(2017, 1, 1), datetime.date(2018, 1, 1)]
    product_layer.dynamic = False
    product_layer._ranges = {
        'lat': {
            'min': -34.5250413940276,
            'max': -33.772472435988
        },
        'lon': {
            'min': 150.330509919584,
            'max': 151.258021405841
        },
        'times': times,
        'start_time': datetime.date(2013, 1, 1),
        'end_time': datetime.date(2018, 1, 1),
        'time_set': set(times),
        'bboxes': {
            'EPSG:3111': {
                'top': 5725844.213533809, 'left': -1623290.9363678931,
                'right': 3983581.449863785, 'bottom': 1042109.9920098772
            },
            'EPSG:3577': {
                'top': -936185.3115191332, 'left': -2407984.8524648934,
                'right': 2834259.110253384, 'bottom': -5195512.771063174
            },
            'EPSG:3857': {
                'top': -1001009.9542990683, 'left': 12324052.573696733,
                'right': 17488921.644948877, 'bottom': -5742240.963567746
            },
            'EPSG:4326': {
                'top': -8.95553593506657, 'left': 110.708847892443,
                'right': 157.105656164263, 'bottom': -45.761684927317
            }
        }
    }
    return product_layer


def test_spatial_parameter_defaults(layer_crs_nongeom):
    param = SpatialParameter(layer_crs_nongeom, "TEST:CRS")
    assert param.y is None
    assert param.x is None
    assert param["x"] is None
    assert param["y"] is None


def test_spatial_parameter_set(layer_crs_nongeom):
    param = SpatialParameter(layer_crs_nongeom, "TEST:CRS")
    param.set(7, -13)
    assert param.x == 7
    assert param.y == -13


def test_spatial_parameter_init(layer_crs_nongeom):
    param = SpatialParameter(layer_crs_nongeom, "TEST:CRS", 7, -13)
    assert param.x == 7
    assert param.y == -13


def test_spatial_parameter_setters(layer_crs_nongeom):
    param = SpatialParameter(layer_crs_nongeom, "TEST:CRS")
    param.lng = 7
    param.lat = -13
    assert param.x == 7
    assert param.y == -13

def test_spatial_parameter_isdim_1(layer_crs_nongeom):
    param = SpatialParameter(layer_crs_nongeom, "TEST:CRS", 7, -13)
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

def test_spatial_parameter_isdim_1(layer_crs_nongeom):
    param = SpatialParameter(layer_crs_nongeom, "EPSG:3577", 2, 7)

    assert param.lat == 7
    assert param.long == 2
    assert param.hortizonal_cults == 2
    assert param.verbal_tics == 7

    try:
        _ = param.horrible_zonts
        assert "Should have thrown a WCSScalarUnknownDimension" == False
    except WCSScalerUnknownDimension as e:
        assert e.dim == "horrible_zonts"

def test_scaler_constructor(layer_crs_nongeom):
    scaler = WCSScaler(layer_crs_nongeom)
    assert scaler.crs == "TEST:NATIVE_CRS"
    assert scaler.crs_def["gml_name"] == "TEST/NATIVE_CRS"
    scaler = WCSScaler(layer_crs_nongeom, "EPSG:3577")
    assert scaler.crs == "EPSG:3577"

def test_scalar_trim(layer_crs_nongeom):
    scaler = WCSScaler(layer_crs_nongeom)
    scaler.trim("x", 5, 10)
    assert scaler.dim("x") == (None, 5, 10)
    assert scaler.subsetted.x
    assert not scaler.is_slice("x")
    assert scaler.dim("y") == (None, None, None)
    assert not scaler.subsetted.y
    assert not scaler.is_slice("y")

def test_scalar_slice(layer_crs_nongeom):
    scaler = WCSScaler(layer_crs_nongeom)
    scaler.slice("y", 5)
    assert scaler.dim("y") == (None, 5, 5)
    assert scaler.subsetted.y
    assert scaler.is_slice("y")
    assert scaler.dim("x") == (None, None, None)
    assert not scaler.subsetted.x
    assert not scaler.is_slice("x")

def test_transform_unsubsetted(layer_crs_geom):
    scaler = WCSScaler(layer_crs_geom, "EPSG:4326")
    scaler.to_crs("EPSG:3577")
    assert scaler.crs == "EPSG:3577"
    assert scaler.dim("x") == (None, -2407984.8524648934, 2834259.110253384)
    assert scaler.dim("y") == (None, -5195512.771063174, -936185.3115191332)


def test_transform_one_slice(layer_crs_geom):
    scaler = WCSScaler(layer_crs_geom, "EPSG:4326")
    scaler.slice("x", 120.0)
    scaler.to_crs("EPSG:3577")
    assert scaler.crs == "EPSG:3577"
    assert scaler.dim("y") == (None, -5195512.771063174, -936185.3115191332)
    assert scaler.dim("x") == (None, -1361473.6681777071, -980861.0939271128)

def test_transform_one_trim(layer_crs_geom):
    scaler = WCSScaler(layer_crs_geom, "EPSG:4326")
    scaler.trim("x", 120.0, 130.0)
    scaler.to_crs("EPSG:3577")
    assert scaler.dim("x") == (None, -1361473.6681777071, -163710.79405154017)
    assert scaler.dim("y") == (None, -5195512.771063174, -936185.3115191332)

def test_transform_two_trims(layer_crs_geom):
    scaler = WCSScaler(layer_crs_geom, "EPSG:4326")
    scaler.trim("x", 120.0, 130.0)
    scaler.trim("y", -30.0, -20.0)
    scaler.to_crs("EPSG:3577")
    assert scaler.dim("x") == (None, -1248178.532656371, -190806.89815343948)
    assert scaler.dim("y") == (None, -3317050.4161210703, -2145729.370620175)

def test_transform_slice_trim(layer_crs_geom):
    scaler = WCSScaler(layer_crs_geom, "EPSG:4326")
    scaler.trim("x", 120.0, 130.0)
    scaler.slice("y", -20.0)
    scaler.to_crs("EPSG:3577")
    assert scaler.dim("x") == (None, -1248178.532656371, -208327.4583571618)
    assert scaler.dim("y") == (None, -2202762.0236987285, -2145729.370620175)

def test_transform_two_slices(layer_crs_geom):
    scaler = WCSScaler(layer_crs_geom, "EPSG:4326")
    scaler.slice("x", 120.0)
    scaler.slice("y", -20.0)
    scaler.to_crs("EPSG:3577")
    assert scaler.dim("x") == (1, -1248178.532656371, -1248153.532656371)
    assert scaler.dim("y") == (1, -2202762.0236987285, -2202787.0236987285)

def test_scale_axis(layer_crs_geom):
    scaler = WCSScaler(layer_crs_geom, "EPSG:4326")
    scaler.to_crs("EPSG:3577")
    scaler.scale_axis("x", 2.0)
    scaler.scale_axis("y", 0.5)
    assert scaler.dim("x") == (419380, -2407984.8524648934, 2834259.110253384)
    assert scaler.dim("y") == (85187, -5195512.771063174, -936185.3115191332)

def test_scale_size(layer_crs_geom):
    scaler = WCSScaler(layer_crs_geom, "EPSG:4326")
    scaler.to_crs("EPSG:3577")
    scaler.scale_size("x", 512)
    scaler.scale_size("y", 512)
    assert scaler.dim("x") == (512, -2407984.8524648934, 2834259.110253384)
    assert scaler.dim("y") == (512, -5195512.771063174, -936185.3115191332)

def test_scaler_default(layer_crs_geom):
    scaler = WCSScaler(layer_crs_geom, "EPSG:4326")
    scaler.to_crs("EPSG:3577")
    affine = scaler.affine()
    assert affine == Affine(
        24.999971208537733, 0.0, -2407984.8524648934,
        0.0, -25.000014436231336, -936185.3115191332)
