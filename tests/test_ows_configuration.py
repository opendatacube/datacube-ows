# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from unittest.mock import MagicMock

import pytest

import datacube_ows.config_utils
import datacube_ows.ogc_utils
import datacube_ows.ows_configuration
from tests.utils import a_function


def test_function_wrapper_lyr():
    lyr = MagicMock()
    func_cfg = "tests.utils.a_function"
    f = datacube_ows.ogc_utils.FunctionWrapper(lyr, func_cfg)
    assert f(7)[0] == "a7  b2  c3"
    assert f.band_mapper is None
    func_cfg = {
        "function": "tests.utils.a_function",
    }
    f = datacube_ows.ogc_utils.FunctionWrapper(lyr, func_cfg)
    assert f(7, 8)[0] == "a7  b8  c3"
    func_cfg = {
        "function": "tests.utils.a_function",
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


def test_func_naked():
    lyr = MagicMock()
    with pytest.raises(datacube_ows.config_utils.ConfigException) as e:
        f = datacube_ows.ogc_utils.FunctionWrapper(lyr, {
            "function": a_function,
        })
    assert str("Directly including callable objects in configuration is no longer supported.")
    with pytest.raises(datacube_ows.config_utils.ConfigException) as e:
        f = datacube_ows.ogc_utils.FunctionWrapper(lyr, a_function)
    assert str("Directly including callable objects in configuration is no longer supported.")
    f = datacube_ows.ogc_utils.FunctionWrapper(lyr, {
        "function": a_function,
    }, stand_alone=True)
    assert f("ardvark", "bllbbll")[0] == "aardvark  bbllbbll  c3"
    f = datacube_ows.ogc_utils.FunctionWrapper(lyr, a_function, stand_alone=True)
    assert f("ardvark", "bllbbll")[0] == "aardvark  bbllbbll  c3"

