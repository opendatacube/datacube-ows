# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from datacube_ows.legend_utils import get_image_from_url
from datacube_ows.ogc_exceptions import WMSException
from datacube_ows.styles.base import StyleDefBase
from datacube_ows.styles.ramp import ColorRamp, ColorRampDef
from tests.test_band_utils import dummy_layer  # noqa: F401,F811


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


def test_create_legend_for_style(dummy_layer): # noqa: F811
    from datacube_ows.legend_generator import create_legend_for_style
    assert create_legend_for_style(dummy_layer, "stylish_steve") is None


@pytest.fixture
def image_url():
    return "https://github.com/fluidicon.png"


@pytest.fixture
def bad_image_url():
    return "https://github.com/not-a-real-github-image-i-hope-asdfgaskjdfghaskjdh.png"


def test_image_from_url(image_url):
    img = get_image_from_url(image_url)
    assert img is not None
    assert img.mode == "RGBA"


def test_image_from_bad_image_url(bad_image_url):
    with pytest.raises(WMSException) as e:
        img = get_image_from_url(bad_image_url)

def test_parse_colorramp_defaults():
    legend = ColorRampDef.Legend(MagicMock(), {})
    ramp = ColorRamp(MagicMock(),
                     {
                        "range": [0.0, 1.0],
                     },
                     legend)
    assert legend.begin == Decimal(0.0)
    assert legend.end == Decimal(1.0)
    assert legend.ticks == [Decimal(0.0), Decimal(1.0)]
    assert legend.units is None
    assert legend.tick_labels == ["0.0", "1.0"]
    assert legend.width == 4.0
    assert legend.height == 1.25
    assert legend.strip_location == [0.05, 0.5, 0.9, 0.15]


def test_parse_colorramp_legend_beginend():
    legend = ColorRampDef.Legend(MagicMock(), {
        "begin": "0.0",
        "end": "2.0"
    })
    assert legend.begin == Decimal("0.0")
    assert legend.end == Decimal("2.0")