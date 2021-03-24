from unittest.mock import MagicMock

import pytest

from datacube_ows.ogc_utils import ConfigException
from datacube_ows.tile_matrix_sets import TileMatrixSet


@pytest.fixture
def wwwm_tms_cfg():
    return TileMatrixSet.default_tm_sets["WholeWorld_WebMercator"].copy()


@pytest.fixture
def tmsmin_global_cfg():
    gcfg = MagicMock()
    gcfg.published_CRSs = {
        "EPSG:3857": {  # Web Mercator
            "geographic": False,
            "horizontal_coord": "x",
            "vertical_coord": "y",
            "vertical_coord_first": False,
        },
        "I:CANT:BELIEVE:ITS:NOT:EPSG:3857": {  # I Can't Believe It's Not Web Mercator
            "geographic": False,
            "horizontal_coord": "x",
            "vertical_coord": "y",
            "vertical_coord_first": True,
        },
        "EPSG:4326": {"geographic": True, "vertical_coord_first": True},  # WGS-84
        "EPSG:3111": {  # VicGrid94 for delwp.vic.gov.au
            "geographic": False,
            "horizontal_coord": "x",
            "vertical_coord": "y",
            "vertical_coord_first": False,
        },
    }
    return gcfg


def test_tms_unpublished_crs(wwwm_tms_cfg):
    global_cfg = MagicMock()
    global_cfg.published_CRSs = {}
    with pytest.raises(ConfigException) as excinfo:
        tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    assert "test" in str(excinfo.value)
    assert "unpublished CRS" in str(excinfo.value)
    assert "EPSG:3857" in str(excinfo.value)


def test_matrix_origin_float_array(wwwm_tms_cfg, tmsmin_global_cfg):
    global_cfg = tmsmin_global_cfg
    wwwm_tms_cfg["matrix_origin"] = None
    with pytest.raises(ConfigException) as excinfo:
        tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    assert "test" in str(excinfo.value)
    assert "Matrix origin" in str(excinfo.value)
    assert "must be a list" in str(excinfo.value)

    wwwm_tms_cfg["matrix_origin"] = [3.3, 6.3, 7.8]
    with pytest.raises(ConfigException) as excinfo:
        tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    assert "test" in str(excinfo.value)
    assert "Matrix origin" in str(excinfo.value)
    assert "must have two values" in str(excinfo.value)

    wwwm_tms_cfg["matrix_origin"] = [6.3, "spaghetti bolognaise"]
    with pytest.raises(ConfigException) as excinfo:
        tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    assert "test" in str(excinfo.value)
    assert "Matrix origin" in str(excinfo.value)
    assert "spaghetti bolognaise" in str(excinfo.value)
    assert "non-float" in str(excinfo.value)
    assert "str" in str(excinfo.value)


def test_tile_size_int_array(wwwm_tms_cfg, tmsmin_global_cfg):
    global_cfg = tmsmin_global_cfg
    wwwm_tms_cfg["tile_size"] = None
    with pytest.raises(ConfigException) as excinfo:
        tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    assert "test" in str(excinfo.value)
    assert "Tile size" in str(excinfo.value)
    assert "must be a list" in str(excinfo.value)

    wwwm_tms_cfg["tile_size"] = [256, 512, 1024]
    with pytest.raises(ConfigException) as excinfo:
        tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    assert "test" in str(excinfo.value)
    assert "Tile size" in str(excinfo.value)
    assert "must have two values" in str(excinfo.value)

    wwwm_tms_cfg["tile_size"] = [64, "spaghetti bolognaise"]
    with pytest.raises(ConfigException) as excinfo:
        tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    assert "test" in str(excinfo.value)
    assert "Tile size" in str(excinfo.value)
    assert "spaghetti bolognaise" in str(excinfo.value)
    assert "non-int" in str(excinfo.value)
    assert "str" in str(excinfo.value)


def test_scale_set_array(wwwm_tms_cfg, tmsmin_global_cfg):
    global_cfg = tmsmin_global_cfg
    wwwm_tms_cfg["scale_set"] = None
    with pytest.raises(ConfigException) as excinfo:
        tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    assert "test" in str(excinfo.value)
    assert "scale_set" in str(excinfo.value)
    assert "is not a list" in str(excinfo.value)


def test_scale_set_array(wwwm_tms_cfg, tmsmin_global_cfg):
    global_cfg = tmsmin_global_cfg
    wwwm_tms_cfg["scale_set"] = None
    with pytest.raises(ConfigException) as excinfo:
        tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    assert "test" in str(excinfo.value)
    assert "scale_set" in str(excinfo.value)
    assert "is not a list" in str(excinfo.value)
    wwwm_tms_cfg["scale_set"] = []
    with pytest.raises(ConfigException) as excinfo:
        tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    assert "test" in str(excinfo.value)
    assert "scale_set" in str(excinfo.value)
    assert "no scale denominators" in str(excinfo.value)


def test_tms_crs_cfg(wwwm_tms_cfg, tmsmin_global_cfg):
    global_cfg = tmsmin_global_cfg
    tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    assert not tms.crs_cfg["vertical_coord_first"]


def test_tms_crs_display(wwwm_tms_cfg, tmsmin_global_cfg):
    global_cfg = tmsmin_global_cfg
    tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    assert tms.crs_display == "urn:ogc:def:crs:EPSG::3857"
    wwwm_tms_cfg["crs"] = "I:CANT:BELIEVE:ITS:NOT:EPSG:3857"
    tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    assert tms.crs_display == "I:CANT:BELIEVE:ITS:NOT:EPSG:3857"
    wwwm_tms_cfg["crs"] = "EPSG:3857"
    wwwm_tms_cfg["force_raw_crs_name"] = True
    tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    assert tms.crs_display == "EPSG:3857"


def test_tms_exponent(wwwm_tms_cfg, tmsmin_global_cfg):
    global_cfg = tmsmin_global_cfg
    tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    assert tms.width_exponent(0) == 0
    assert tms.width_exponent(1) == 1
    assert tms.width_exponent(12) == 12
    assert tms.height_exponent(0) == 0
    assert tms.height_exponent(1) == 1
    assert tms.height_exponent(12) == 12
    wwwm_tms_cfg["matrix_exponent_initial_offsets"] = [-2, 2]
    tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    assert tms.width_exponent(0) == 0
    assert tms.width_exponent(1) == 0
    assert tms.width_exponent(2) == 0
    assert tms.width_exponent(3) == 1
    assert tms.width_exponent(12) == 10
    assert tms.height_exponent(0) == 2
    assert tms.height_exponent(1) == 3
    assert tms.height_exponent(12) == 14


def test_tms_wms_bbox(wwwm_tms_cfg, tmsmin_global_cfg):
    global_cfg = tmsmin_global_cfg
    tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    a, b, c, d = tms.wms_bbox_coords(7, 32, 24)
    assert a == pytest.approx(-12523442.7142, 0.001)
    assert b == pytest.approx(9705668.103538, 0.001)
    assert c == pytest.approx(-12210356.64638, 0.001)
    assert d == pytest.approx(10018754.17139, 0.001)
    wwwm_tms_cfg["crs"] = "I:CANT:BELIEVE:ITS:NOT:EPSG:3857"
    tms = TileMatrixSet("test", wwwm_tms_cfg, global_cfg)
    a, b, c, d = tms.wms_bbox_coords(7, 32, 24)
    assert b == pytest.approx(-12523442.7142, 0.001)
    assert a == pytest.approx(9705668.103538, 0.001)
    assert d == pytest.approx(-12210356.64638, 0.001)
    assert c == pytest.approx(10018754.17139, 0.001)
