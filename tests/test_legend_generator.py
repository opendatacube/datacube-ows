import datacube_ows.legend_generator

import pytest
import datetime
from decimal import Decimal

from unittest.mock import patch, MagicMock

import numpy as np

from datacube_ows.styles.ramp import ColorRamp, ColorRampDef
from datacube_ows.styles.base import StyleDefBase
from datacube_ows.ogc_exceptions import WMSException
from datacube_ows.legend_utils import  get_image_from_url


@pytest.fixture
def prelegend_style():
    style = StyleDefBase.__new__(StyleDefBase)
    style._unready_attributes = []
    return style

@pytest.fixture
def prelegend_colorramp_style():
    style = ColorRampDef.__new__(ColorRampDef)
    style._unready_attributes = []
    return style


def test_legend_parser_nolegend(prelegend_style):
    prelegend_style.parse_legend_cfg(
        {
            "show_legend": False,
        }
    )
    assert not prelegend_style.show_legend
    assert prelegend_style.legend_url_override is None


def test_legend_parser_urllegend(prelegend_style):
    url = "http://whatevs"
    prelegend_style.parse_legend_cfg(
        {
            "show_legend": True,
            "url": url
        }
    )
    assert prelegend_style.show_legend
    assert prelegend_style.legend_url_override == url

@pytest.fixture
def image_url():
    return "https://github.com/fluidicon.png"

@pytest.fixture
def bad_image_url():
    return "https://github.com/not-a-real-github-image-i-hope-asdfgaskjdfghaskjdh.png"


def test_image_from_url(image_url):
    img = get_image_from_url(image_url)
    assert img is not None
    assert img.model == "RGBA"


def test_image_from_url(bad_image_url):
    img = get_image_from_url(bad_image_url)
    assert img is None


def test_parse_colorramp_defaults():
    ramp = ColorRamp(None, {
        "range": [0.0, 1.0],
    })
    assert ramp.legend_begin == Decimal(0.0)
    assert ramp.legend_end == Decimal(1.0)
    assert ramp.ticks == [Decimal(0.0), Decimal(1.0)]
    assert ramp.legend_units == ""
    assert ramp.tick_labels == ["0.0", "1.0"]
    assert ramp.legend_width == 4.0
    assert ramp.legend_height == 1.25
    assert ramp.legend_strip_location == [0.05, 0.5, 0.9, 0.15]


def test_parse_colorramp_legend_beginend():
    ramp = ColorRamp(None, {
        "range": [-1.0, 2.5],
        "legend": {
            "begin": "0.0",
            "end": "2.0"
        }
    })
    assert ramp.legend_begin == Decimal("0.0")
    assert ramp.legend_end == Decimal("2.0")
    assert ramp.ticks == [Decimal("0.0"), Decimal("2.0")]
    assert ramp.legend_units == ""
    assert ramp.tick_labels == ["0.0", "2.0"]


def test_parse_colorramp_legend_ticksevery():
    ramp = ColorRamp(None, {
        "range": [-1.0, 2.5],
        "legend": {
            "begin": "0.0",
            "end": "2.0",
            "ticks_every": "0.4"
        }
    })
    assert ramp.ticks == [Decimal("0.0"), Decimal("0.4"), Decimal("0.8"),
                          Decimal("1.2"), Decimal("1.6"), Decimal("2.0")]
    assert ramp.tick_labels == ["0.0", "0.4", "0.8", "1.2", "1.6", "2.0"]


def test_parse_colorramp_legend_tickcount():
    ramp = ColorRamp(None, {
        "range": [-1.0, 2.5],
        "legend": {
            "begin": "0.0",
            "end": "2.0",
            "tick_count": 2
        }
    })
    assert ramp.ticks == [Decimal("0.0"), Decimal("1.0"), Decimal("2.0")]
    assert ramp.tick_labels == ["0.0", "1.0", "2.0"]


def test_parse_colorramp_legend_ticks():
    ramp = ColorRamp(None, {
        "range": [-1.0, 2.5],
        "legend": {
            "begin": "0.0",
            "end": "2.0",
            "ticks": ["0.3", "0.9", "1.1", "1.9", "2.0"]
        }
    })
    assert ramp.ticks == [Decimal("0.3"), Decimal("0.9"),
                          Decimal("1.1"), Decimal("1.9"), Decimal("2.0")]
    assert ramp.tick_labels == ["0.3", "0.9", "1.1", "1.9", "2.0"]


def test_parse_colorramp_legend_find_end():
    ramp = ColorRamp(None, {
         'color_ramp': [
            {
                'value': 999,
                'color': '#000000',
                'alpha': 0.0
            },
            {
                'value': 1000,
                'color': '#000000'
            },
            {
                'value': 2500,
                'color': '#BA7500'
            },
            {
                'value': 6500,
                'color': '#BF4000'
            },
            {
                'value': 51500,
                'color': '#EF1000'
            }
        ],
        'legend': {
            'show_legend': True,
            'begin': '1000',
            'end': '6000',
            'ticks': ['1000', '2000', '3000', '6000'],
            'tick_labels': {
                '1000': {
                    'label': '-1.0'
                },
                '2000': {
                    'label': '0.0'
                },
                '3000': {
                    'label': '1.0'
                },
                '6000': {
                    'label': '4.0'
                }
            }
        }
    })
    assert ramp.values == [999.0, 1000.0, 2500.0, 6000.0, 6500.0, 51500.0]

def test_parse_colorramp_legend_tick_labels():
    ramp = ColorRamp(None, {
        "range": [-1.0, 2.5],
        "legend": {
            "begin": "0.0",
            "end": "2.0",
            "ticks": ["0.3", "0.5", "0.8", "0.9", "1.0",
                      "1.1", "1.7", "1.9", "2.0"],
            "tick_labels": {
                "default": {
                    "prefix": "p",
                    "suffix": "s"
                },
                "0.3": {},
                "0.8": {
                    "prefix": "",
                    "suffix": "Zz"
                },
                "0.9": {
                    "suffix": "Zz"
                },
                "1.1": {
                    "prefix": "#",
                },
                "1.7": {
                    "prefix": "pre",
                    "label": "fixe"
                },
                "1.9": {
                    "label": "o",
                },
                "2.0": {
                    "prefix": ":",
                    "label": "-",
                    "suffix": ")",
                }
            }
        }
    })
    assert ramp.ticks == [Decimal("0.3"), Decimal("0.5"), Decimal("0.8"),
              Decimal("0.9"), Decimal("1.0"),
              Decimal("1.1"), Decimal("1.7"), Decimal("1.9"), Decimal("2.0")]
    assert ramp.tick_labels == ["p0.3s", "p0.5s", "0.8Zz", "p0.9Zz", "p1.0s",
                                "#1.1s", "prefixes", "pos", ":-)"]


