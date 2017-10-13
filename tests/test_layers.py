from datacube_wms.wms_layers import get_layers

import datacube
import pytest

@pytest.fixture
def wms_datacube(request):
    return datacube.Datacube(app="wms_test")

def test_get_layers(wms_datacube):
    layers = get_layers(dc=wms_datacube)

    assert layers.platforms
    for p in layers:
        assert p.styles
        assert p.products
        for prd in p.products:
            assert layers.product_index[prd.name] == prd
            assert prd.title

