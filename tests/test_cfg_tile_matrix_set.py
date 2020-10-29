import pytest
from unittest.mock import MagicMock

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
            },
            "EPSG:4326": {  # WGS-84
                "geographic": True,
                "vertical_coord_first": True
            },
            "EPSG:3111": {  # VicGrid94 for delwp.vic.gov.au
                "geographic": False,
                "horizontal_coord": "x",
                "vertical_coord": "y",
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

    wwwm_tms_cfg["matrix_origin"] = [3.3,6.3, 7.8]
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
