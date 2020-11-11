import datetime
from unittest.mock import MagicMock

import pytest

@pytest.fixture
def flask_client(monkeypatch):
    monkeypatch.setenv("DEFER_CFG_PARSE", "yes")
    from datacube_ows.ogc import app
    with app.test_client() as client:
        yield client


@pytest.fixture
def minimal_dc():
    dc = MagicMock()
    nb = MagicMock()
    nb.index = ['band1', 'band2', 'band3', 'band4']
    nb.__getitem__.return_value = {
        "band1": -999,
        "band2": -999,
        "band3": float("nan"),
        "band4": "nan",
    }
    lmo = MagicMock()
    lmo.loc = {
        "foo_nativeres": nb,
        "foo_nonativeres": nb,
        "foo_badnativecrs": nb,
        "foo_nativecrs": nb,
        "foo_nonativecrs": nb,
        "foo": nb,
        "bar": nb,
    }
    dc.list_measurements.return_value = lmo

    def product_by_name(s):
        if 'lookupfail' in s:
            return None
        mprod  = MagicMock()
        flag_def = {
            "moo":   {"bits": 0},
            "floop": {"bits": 1},
            "blat":  {"bits": 2},
            "pow":   {"bits": 3},
            "zap":   {"bits": 4},
            "dang":  {"bits": 5},
        }
        mprod.lookup_measurements.return_value = {
            "band4": {
                "flags_definition": flag_def
            }
        }
        mprod.definition = {"storage": {}}
        if 'nonativecrs' in s:
            pass
        elif 'badnativecrs' in s:
            mprod.definition["storage"]["crs"] = "EPSG:9999"
        elif 'nativecrs' in s:
            mprod.definition["storage"]["crs"] = "EPSG:4326"
        else:
            pass
        if 'nonativeres' in s:
            pass
        elif 'nativeres' in s:
            mprod.definition["storage"]["resolution"] = {
                "latitude": 0.001,
                "longitude": 0.001,
            }
        else:
            pass
        return mprod
    dc.index.products.get_by_name = product_by_name
    return dc


@pytest.fixture
def minimal_global_cfg():
    global_cfg=MagicMock()
    global_cfg.keywords = {"global"}
    global_cfg.attribution = "Global Attribution"
    global_cfg.authorities = {
        "auth0": "http://test.url/auth0",
        "auth1": "http://test.url/auth1",
    }
    global_cfg.published_CRSs = {
        "EPSG:3857": {  # Web Mercator
            "geographic": False,
            "horizontal_coord": "x",
            "vertical_coord": "y",
            "vertical_coord_first": False,
            "gml_name": "http://www.opengis.net/def/crs/EPSG/0/3857",
            "alias_of": None,
        },
        "EPSG:4326": {  # WGS-84
            "geographic": True,
            "vertical_coord_first": True,
            "horizontal_coord": "longitude",
            "vertical_coord": "latitude",
            "gml_name": "http://www.opengis.net/def/crs/EPSG/0/4326",
            "alias_of": None,
        },
        "EPSG:3577": {
            "geographic": False,
            "horizontal_coord": "x",
            "vertical_coord": "y",
            "vertical_coord_first": False,
            "gml_name": "http://www.opengis.net/def/crs/EPSG/0/3577",
            "alias_of": None,
        },
        "TEST:CRS": {
            "geographic": False,
            "horizontal_coord": "horrible_zonts",
            "vertical_coord": "vertex_calories",
            "vertical_coord_first": False,
            "gml_name": "TEST/CRS",
            "alias_of": None,
        },
        "TEST:NATIVE_CRS": {
            "geographic": False,
            "horizontal_coord": "hortizonal_cults",
            "vertical_coord": "verbal_tics",
            "vertical_coord_first": False,
            "gml_name": "TEST/NATIVE_CRS",
            "alias_of": None,
        },
    }
    return global_cfg


@pytest.fixture
def minimal_parent():
    parent = MagicMock()
    parent.abstract = "Parent Abstract"
    parent.keywords = {"global", "parent"}
    parent.attribution = "Parent Attribution"
    return parent


@pytest.fixture
def minimal_layer_cfg():
    return {
        "title": "The Title",
        "abstract": "The Abstract",
        "name": "a_layer",
        "product_name": "foo",
        "image_processing": {
            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
        },
        "styling": {
            "default_style": "band1",
            "styles": [
                {
                    "name": "band1",
                    "title": "Single Band Test Style",
                    "abstract": "",
                    "components": {
                        "red": {"band1": 1.0},
                        "green": {"band1": 1.0},
                        "blue": {"band1": 1.0},
                    },
                    "scale_range": [0, 1024]
                }
            ]
        }
    }


@pytest.fixture
def minimal_multiprod_cfg():
    return {
        "title": "The Title",
        "abstract": "The Abstract",
        "name": "a_layer",
        "multi_product": True,
        "product_names": ["foo", "bar"],
        "image_processing": {
            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
        },
        "styling": {
            "default_style": "band1",
            "styles": [
                {
                    "name": "band1",
                    "title": "Single Band Test Style",
                    "abstract": "",
                    "components": {
                        "red": {"band1": 1.0},
                        "green": {"band1": 1.0},
                        "blue": {"band1": 1.0},
                    },
                    "scale_range": [0, 1024]
                }
            ]
        }
    }

@pytest.fixture
def mock_range():
    times = [datetime.datetime(2010, 1, 1), datetime.datetime(2010, 1, 2)]
    return {
        "lat": {
            "min": -0.1,
            "max": 0.1,
        },
        "lon": {
            "min": -0.1,
            "max": 0.1,
        },
        "times": times,
        "start_time": times[0],
        "end_time": times[-1],
        "time_set": set(times),
        "bboxes": {
            "EPSG:4326": {"top": 0.1, "bottom": -0.1, "left": 0.1, "right": -0.1,},
            "EPSG:3577": {"top": 0.1, "bottom": -0.1, "left": 0.1, "right": -0.1,},
            "EPSG:3857": {"top": 0.1, "bottom": -0.1, "left": 0.1, "right": -0.1,},
        }
    }
