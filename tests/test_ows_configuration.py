import datacube_ows.ows_configuration

import pytest

def test_accum_max():
    ret = datacube_ows.ows_configuration.accum_max(1, 3)
    assert ret == 3

def test_accum_min():
    ret = datacube_ows.ows_configuration.accum_min(1, 3)
    assert ret == 1
