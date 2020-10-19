import pytest
from unittest.mock import MagicMock

from datacube_ows.ogc_utils import ConfigException
from datacube_ows.ows_configuration import OWSLayer, OWSFolder

@pytest.fixture
def minimal_global_cfg():
    global_cfg=MagicMock()
    global_cfg.keywords = {"global"}
    global_cfg.attribution = "Global Attribution"
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


