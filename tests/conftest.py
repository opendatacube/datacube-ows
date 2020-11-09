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
