from datacube_ows.ows_configuration import get_config

import datacube
import pytest


def test_get_layers():
    layers = get_config()

    # assert layers.platforms
    # for p in layers:
    #     assert p.products
    #     for prd in p.products:
    #         assert prd.styles
    #        assert layers.product_index[prd.name] == prd
    #        assert prd.title
