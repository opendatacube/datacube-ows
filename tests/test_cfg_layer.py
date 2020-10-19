import pytest
from unittest.mock import MagicMock

from datacube_ows.ogc_utils import ConfigException
from datacube_ows.ows_configuration import OWSLayer

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

