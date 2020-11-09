import pytest
from unittest.mock import MagicMock

from datacube_ows.ogc_utils import ConfigException
from datacube_ows.ows_configuration import OWSLayer, OWSFolder, parse_ows_layer

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

def test_minimal_layer_create(minimal_global_cfg):
    lyr = OWSLayer({
            "title": "The Title",
            "abstract": "The Abstract"
        },
        global_cfg=minimal_global_cfg)
    assert lyr.title == "The Title"
    assert len(lyr.keywords) == 1
    assert "global" in lyr.keywords
    assert lyr.abstract == "The Abstract"
    assert lyr.global_cfg == minimal_global_cfg
    assert lyr.attribution == "Global Attribution"
    assert lyr.layer_count() == 0
    assert lyr.unready_layer_count() == 0
    assert "The Title" in str(lyr)

def test_missing_title(minimal_global_cfg):
    with pytest.raises(ConfigException) as excinfo:
        lyr = OWSLayer({
            "abstract": "The Abstract"
            },
            global_cfg=minimal_global_cfg)
    assert "Layer without title" in str(excinfo.value)
    assert "None" in str(excinfo.value)


def test_inherit_no_abstract(minimal_global_cfg):
    with pytest.raises(ConfigException) as excinfo:
        lyr = OWSLayer({
            "title": "The Title",
        },
        global_cfg=minimal_global_cfg)
    assert "No abstract" in str(excinfo.value)
    assert "top-level layer" in str(excinfo.value)
    assert "The Title" in str(excinfo.value)


def test_inherit_parent(minimal_global_cfg, minimal_parent):
    lyr = OWSLayer({
            "title": "The Title",
        },
        parent_layer=minimal_parent,
        global_cfg=minimal_global_cfg)
    assert lyr.abstract == "Parent Abstract"
    assert lyr.attribution == "Parent Attribution"
    assert "global" in lyr.keywords
    assert "parent" in lyr.keywords


def test_override_parent(minimal_global_cfg, minimal_parent):
    lyr = OWSLayer({
        "title": "The Title",
        "attribution": {},
        "abstract": "The Abstract",
        "keywords": ["merged"]
    },
        parent_layer=minimal_parent,
        global_cfg=minimal_global_cfg)
    assert lyr.abstract == "The Abstract"
    assert lyr.attribution is None
    assert "global" in lyr.keywords
    assert "parent" in lyr.keywords
    assert "merged" in lyr.keywords


def test_minimal_folder(minimal_global_cfg):
    lyr = OWSFolder({
        "title": "The Title",
        "abstract": "The Abstract",
        "layers": []
    }, global_cfg=minimal_global_cfg)
    assert lyr.child_layers == []
    assert lyr.layer_count() == 0
    assert lyr.unready_layer_count() == 0


def test_folder_nolayers(minimal_global_cfg):
    with pytest.raises(ConfigException) as excinfo:
        lyr = OWSFolder({
            "title": "The Title",
            "abstract": "The Abstract",
        }, global_cfg=minimal_global_cfg)
    assert "No layers section" in str(excinfo.value)
    assert "The Title" in str(excinfo.value)


def test_folder_counts(minimal_global_cfg):
    lyr = OWSFolder({
        "title": "The Title",
        "abstract": "The Abstract",
        "layers": []
    }, global_cfg=minimal_global_cfg)
    l1 = MagicMock()
    l2 = MagicMock()
    l3 = MagicMock()
    l4 = MagicMock()
    l1.layer_count.return_value = 1
    l2.layer_count.return_value = 2
    l3.layer_count.return_value = 1
    l4.layer_count.return_value = 3
    lyr.child_layers = [l1, l2]
    lyr.unready_layers = [l3, l4]
    assert lyr.layer_count() == 3
    assert lyr.unready_layer_count() == 4


def test_catch_invalid_folder_layers(minimal_global_cfg):
    lyr = OWSFolder({
        "title": "The Title",
        "abstract": "The Abstract",
        "layers": [
            {"invalid": "config"}
        ]
    }, global_cfg=minimal_global_cfg)
    assert len(lyr.unready_layers) == 0


def test_make_ready_empty(minimal_global_cfg, minimal_dc):
    lyr = OWSFolder({
        "title": "The Title",
        "abstract": "The Abstract",
        "layers": [
        ]
    }, global_cfg=minimal_global_cfg)
    lyr.make_ready(minimal_dc)
    assert len(lyr.unready_layers) == 0
    assert lyr.ready


def test_make_ready_catch_errors(minimal_global_cfg, minimal_dc):
    lyr = OWSFolder({
        "title": "The Title",
        "abstract": "The Abstract",
        "layers": [
        ]
    }, global_cfg=minimal_global_cfg)
    testchild = MagicMock()
    testchild.make_ready.side_effect = ConfigException("KerPow!")
    lyr.unready_layers.append(testchild)
    lyr.make_ready(minimal_dc)
    assert len(lyr.unready_layers) == 1
    assert len(lyr.child_layers) == 0
    assert lyr.ready


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

def test_minimal_named_layer(minimal_layer_cfg, minimal_global_cfg, minimal_dc):
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    assert lyr.name == "a_layer"
    assert not lyr.ready
    lyr.make_ready(minimal_dc)
    assert lyr.ready
    assert "a_layer" in str(lyr)
    assert len(lyr.low_res_products) == 0


def test_lowres_named_layer(minimal_layer_cfg, minimal_global_cfg, minimal_dc):
    minimal_layer_cfg["low_res_product_name"] = "smol_foo"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    lyr.make_ready(minimal_dc)
    assert len(lyr.low_res_products) == 1


def test_double_underscore_product_name(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["product_name"] = "no__double__underscores"
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "double underscore" in str(excinfo.value)


def test_no_product_name(minimal_layer_cfg, minimal_global_cfg):
    del minimal_layer_cfg["product_name"]
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "product names" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_bad_product_name(minimal_layer_cfg, minimal_global_cfg, minimal_dc):
    minimal_layer_cfg["product_name"] = "foolookupfail"
    minimal_dc.index.products.get_by_name.return_value = None
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    with pytest.raises(ConfigException) as excinfo:
        lyr.make_ready(dc=minimal_dc)
    assert "Could not find product" in str(excinfo.value)
    assert "foolookupfail" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_bad_lowres_product_name(minimal_layer_cfg, minimal_global_cfg, minimal_dc):
    minimal_layer_cfg["low_res_product_name"] = "smolfoolookupfail"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    with pytest.raises(ConfigException) as excinfo:
        lyr.make_ready(dc=minimal_dc)
    assert "Could not find product" in str(excinfo.value)
    assert "smolfoolookupfail" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_noprod_multiproduct(minimal_multiprod_cfg, minimal_global_cfg, minimal_dc):
    minimal_multiprod_cfg["product_names"] = []
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_multiprod_cfg,
                          global_cfg=minimal_global_cfg)

    assert "a_layer" in str(excinfo.value)
    assert "No products declared" in str(excinfo.value)

def test_minimal_multiproduct(minimal_multiprod_cfg, minimal_global_cfg, minimal_dc):
    lyr = parse_ows_layer(minimal_multiprod_cfg,
                          global_cfg=minimal_global_cfg)
    assert lyr.name == "a_layer"
    assert not lyr.ready
    lyr.make_ready(minimal_dc)
    assert lyr.ready
    assert "a_layer" in str(lyr)


def test_multi_product_lowres(minimal_multiprod_cfg, minimal_global_cfg, minimal_dc):
    minimal_multiprod_cfg["low_res_product_names"] = ["smol_foo", "smol_bar"]
    lyr = parse_ows_layer(minimal_multiprod_cfg,
                              global_cfg=minimal_global_cfg)
    lyr.make_ready(minimal_dc)
    assert len(lyr.products) == 2
    assert len(lyr.low_res_products) == 2


def test_multi_product_name_mismatch(minimal_multiprod_cfg, minimal_global_cfg):
    minimal_multiprod_cfg["low_res_product_names"] = ["smol_foo"]
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_multiprod_cfg,
                              global_cfg=minimal_global_cfg)
    assert "low_res_product_names" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_manual_merge(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["image_processing"]["manual_merge"] = True
    minimal_layer_cfg["image_processing"]["apply_solar_corrections"] = False
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    assert not lyr.ready
    minimal_layer_cfg["image_processing"]["manual_merge"] = False
    minimal_layer_cfg["image_processing"]["apply_solar_corrections"] = True
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "Solar correction requires manual_merge" in str(excinfo.value)


def test_bad_timeres(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["time_resolution"] = "prime_ministers"
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "Invalid time resolution" in str(excinfo.value)
    assert "prime_ministers" in str(excinfo.value)


def test_flag_no_band(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["flags"] = {
        "product": "foo",
    }

    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "required" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)
    assert "band" in str(excinfo.value)


def test_flag_bad_prod(minimal_layer_cfg, minimal_global_cfg, minimal_dc):
    minimal_layer_cfg["flags"] = {
        "product": "foolookupfail",
        "band": "band1"
    }
    lyr = parse_ows_layer(minimal_layer_cfg, global_cfg=minimal_global_cfg)
    with pytest.raises(ConfigException) as excinfo:
        lyr.make_ready(dc=minimal_dc)
    assert "foolookupfail" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_img_proc_no_extent_func(minimal_layer_cfg, minimal_global_cfg):
    del minimal_layer_cfg["image_processing"]["extent_mask_func"]
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "required" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)
    assert "extent_mask_func" in str(excinfo.value)


def test_id_badauth(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["identifiers"] = {
        "auth0": "5318008",
        "authn": "mnnnmnnh"
    }
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "non-declared authority" in str(excinfo.value)
    assert "authn" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_no_styles(minimal_layer_cfg, minimal_global_cfg):
    del minimal_layer_cfg["styling"]["styles"]
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "Missing required" in str(excinfo.value)
    assert "styles" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_bad_default_style(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["styling"]["default_style"] = "nonexistent"
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "not in the 'styles'" in str(excinfo.value)
    assert "nonexistent" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_no_default_style(minimal_layer_cfg, minimal_global_cfg):
    del minimal_layer_cfg["styling"]["default_style"]
    lyr = parse_ows_layer(minimal_layer_cfg,
                      global_cfg=minimal_global_cfg)
    assert lyr.default_style.name == 'band1'

def test_no_wcs_default_bands(minimal_layer_cfg, minimal_global_cfg):
    minimal_global_cfg.wcs = True
    minimal_layer_cfg["wcs"] = {}
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "Missing required" in str(excinfo.value)
    assert "wcs" in str(excinfo.value)
    assert "default_bands" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_invalid_native_format(minimal_layer_cfg, minimal_global_cfg):
    minimal_global_cfg.wcs = True
    minimal_layer_cfg["wcs"] = {
        "default_bands": ["band1", "band2"],
        "native_format": "geosplunge"
    }
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "a_layer" in str(excinfo.value)
    assert "geosplunge" in str(excinfo.value)
