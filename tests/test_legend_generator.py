import datacube_ows.legend_generator

import pytest
import datetime
from decimal import Decimal

from unittest.mock import patch, MagicMock

import numpy as np

from datacube_ows.band_mapper import StyleDefBase, RgbaColorRampDef, RgbaColorRamp
from datacube_ows.ogc_exceptions import WMSException


@pytest.fixture
def prelegend_style():
    style = StyleDefBase.__new__(StyleDefBase)
    return style

@pytest.fixture
def prelegend_colorramp_style():
    style = RgbaColorRampDef.__new__(RgbaColorRampDef)
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


@patch("datacube_ows.legend_generator.make_response")
def test_create_legends_from_styles(make_response):

    def fake_img(bytesio):
        from PIL import Image
        Image.new('RGB', (256, 256)).save(bytesio, format="PNG")

    class fakestyle:
        def __init__(self):
            self.single_date_legend = MagicMock()
            self.single_date_legend.side_effect = fake_img
            self.legend_override_with_url = MagicMock()
            self.legend_override_with_url.return_value = None
            self.multi_date_handlers = [
            ]

    datacube_ows.legend_generator.create_legends_from_styles([fakestyle()])

    from io import BytesIO
    from PIL import Image
    bs = BytesIO()
    Image.new('RGB', (256, 256)).save(bs, format="PNG")

    make_response.assert_called_with(bs.getvalue())

@patch("datacube_ows.legend_generator.make_response")
def test_legend_graphic(make_response):

    def fake_img(bytesio):
        from PIL import Image
        Image.new('RGB', (256, 256)).save(bytesio, format="PNG")

    class FakeRequestResult:
        def __init__(self, status_code=200, mime="image/png"):
            self.status_code = status_code
            self.headers = {
                'content-type': mime
            }
            from io import BytesIO
            from PIL import Image
            bs = BytesIO()
            Image.new('RGB', (256, 256)).save(bs, format="PNG")
            bs.seek(0)
            self.content = bs.read()

    class fakeproduct:
        def __init__(self, legend, style_index):
            self.legend = legend
            self.style_index = style_index

    class fakeparams:
        def __init__(self, style_name, product):
            self.product = product
            self.times = [datetime.date(2017,1,1)]
            self.styles = [MagicMock()]
            self.styles[0].name = style_name
            self.styles[0].single_date_legend = MagicMock()
            self.styles[0].single_date_legend.side_effect = fake_img
            self.styles[0].legend_override_with_url = MagicMock()
            self.styles[0].legend_override_with_url.return_value = "anurl"
            self.styles[0].multi_date_handlers = [
            ]

    with patch("datacube_ows.legend_generator.GetLegendGraphicParameters") as lgp, patch("requests.get") as rg:
        lgp.return_value = fakeparams("test_style", None)
        rg.return_value = FakeRequestResult()
        lg = datacube_ows.legend_generator.legend_graphic(None)

        assert lg.mimetype == 'image/png'
    with patch("datacube_ows.legend_generator.GetLegendGraphicParameters") as lgp, patch("requests.get") as rg:
        lgp.return_value = fakeparams("test_style", fakeproduct({"url": "test_bad_url"}, dict()))
        rg.return_value = FakeRequestResult(status_code=404)
        try:
            lg = datacube_ows.legend_generator.legend_graphic(None)
            assert False
        except WMSException:
            assert True

    with patch("datacube_ows.legend_generator.GetLegendGraphicParameters") as lgp, patch("requests.get") as rg:
        rg.return_value = FakeRequestResult()
        lgp.return_value = fakeparams("test_style", fakeproduct({"url": "test_good_url"}, dict()))

        lg = datacube_ows.legend_generator.legend_graphic(None)

        make_response.assert_called_with(rg.return_value.content)


    with patch("datacube_ows.legend_generator.GetLegendGraphicParameters") as lgp, patch("datacube_ows.legend_generator.create_legends_from_styles") as clfs:
        lgp.return_value = fakeparams("test", fakeproduct({"styles": ["test"]}, {"test": "foobarbaz"}))
        lg = datacube_ows.legend_generator.legend_graphic(None)

        clfs.assert_called_with(lgp.return_value.styles, ndates=1)


def test_parse_colorramp_defaults():
    ramp = RgbaColorRamp(None, {
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
    ramp = RgbaColorRamp(None, {
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
    ramp = RgbaColorRamp(None, {
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
    ramp = RgbaColorRamp(None, {
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
    ramp = RgbaColorRamp(None, {
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


def test_parse_colorramp_legend_tick_labels():
    ramp = RgbaColorRamp(None, {
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


