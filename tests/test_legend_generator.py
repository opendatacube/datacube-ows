import datacube_ows.legend_generator

import pytest

from unittest.mock import patch, MagicMock

import numpy as np

from datacube_ows.ogc_exceptions import WMSException


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

    class fakeproduct:
        def __init__(self, legend, style_index):
            self.legend = legend
            self.style_index = style_index

    class fakeparams:
        def __init__(self, style_name, product):
            self.product = product
            self.times = []
            self.styles = [MagicMock()]
            self.styles[0].name = style_name
            self.styles[0].single_date_legend = MagicMock()
            self.styles[0].single_date_legend.side_effect = fake_img
            self.styles[0].legend_override_with_url = MagicMock()
            self.styles[0].legend_override_with_url.return_value = None
            self.styles[0].multi_date_handlers = [
            ]

    with patch("datacube_ows.legend_generator.GetLegendGraphicParameters") as lgp:
        lgp.return_value = fakeparams("test_style", None)
        lg = datacube_ows.legend_generator.legend_graphic(None)

        assert lg.mimetype == 'image/png'
    with patch("datacube_ows.legend_generator.GetLegendGraphicParameters") as lgp, patch("requests.get") as rg:
        lgp.return_value = fakeparams(False, fakeproduct({"url": "test_bad_url"}, dict()))
        lg = datacube_ows.legend_generator.legend_graphic(None)
        assert lg.mimetype == 'image/png'

    with patch("datacube_ows.legend_generator.GetLegendGraphicParameters") as lgp, patch("requests.get") as rg:
        class fakeresponse:
            def __init__(self):
                self.status_code = 200
                self.headers = {
                    "content-type": "image/png"
                }
                self.content = 1000
        rg.return_value = fakeresponse()
        lgp.return_value = fakeparams(False, fakeproduct({"url": "test_good_url"}, dict()))

        lg = datacube_ows.legend_generator.legend_graphic(None)

        # TODO: This test needs love.
        # make_response.assert_called_with(1000)


    with patch("datacube_ows.legend_generator.GetLegendGraphicParameters") as lgp, patch("datacube_ows.legend_generator.create_legends_from_styles") as clfs:
        lgp.return_value = fakeparams(False, fakeproduct({"styles": ["test"]}, {"test": "foobarbaz"}))
        lg = datacube_ows.legend_generator.legend_graphic(None)

        # TODO: This test needs love.
        #  clfs.assert_called_with(["foobarbaz"])
