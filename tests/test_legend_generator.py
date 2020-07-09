import datacube_ows.legend_generator

import pytest
import datetime

from unittest.mock import patch, MagicMock

import numpy as np

from datacube_ows.band_mapper import StyleDefBase, RgbaColorRampDef
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
