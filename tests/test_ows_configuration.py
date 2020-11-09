import datacube_ows.config_utils
import datacube_ows.ogc_utils


import datacube_ows.ows_configuration
from datacube_ows.ows_configuration import BandIndex
from unittest.mock import patch, MagicMock
import pytest


def test_function_wrapper_lyr():
    lyr = MagicMock()
    func_cfg = "tests.utils.test_function"
    f = datacube_ows.ogc_utils.FunctionWrapper(lyr, func_cfg)
    assert f(7)[0] == "a7  b2  c3"
    assert f.band_mapper is None
    func_cfg = {
        "function": "tests.utils.test_function",
    }
    f = datacube_ows.ogc_utils.FunctionWrapper(lyr, func_cfg)
    assert f(7, 8)[0] == "a7  b8  c3"
    func_cfg = {
        "function": "tests.utils.test_function",
        "kwargs": {
            "foo": "bar",
            "c": "ouple"
        }
    }
    f = datacube_ows.ogc_utils.FunctionWrapper(lyr, func_cfg)
    result = f("pple", "eagle")
    assert result[0] == "apple  beagle  couple"
    assert result[1]["foo"] == "bar"
    assert f.band_mapper is None

