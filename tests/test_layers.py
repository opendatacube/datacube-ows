from datacube_wms.wms_layers import get_layers

import datacube
import pytest


def test_get_layers():
    layers = get_layers()

    assert layers.platforms
    for p in layers:
        assert p.products
        for prd in p.products:
            assert prd.styles
            assert layers.product_index[prd.name] == prd
            assert prd.title
