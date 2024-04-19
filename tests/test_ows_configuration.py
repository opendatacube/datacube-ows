# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
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
    f = datacube_ows.config_utils.FunctionWrapper(lyr, func_cfg)
    assert f(7)[0] == "a7  b2  c3"
    assert f(5, c=4)[0] == "a5  b2  c4"
    assert f.band_mapper is None
    func_cfg = {
        "function": "tests.utils.a_function",
    }
    f = datacube_ows.config_utils.FunctionWrapper(lyr, func_cfg)
    assert f(7, 8)[0] == "a7  b8  c3"
    func_cfg = {
        "function": "tests.utils.a_function",
        "kwargs": {
            "foo": "bar",
            "c": "ouple"
        }
    }
    f = datacube_ows.config_utils.FunctionWrapper(lyr, func_cfg)
    result = f("pple", "eagle")
    assert result[0] == "apple  beagle  couple"
    assert result[1]["foo"] == "bar"
    assert f.band_mapper is None
    f = datacube_ows.config_utils.FunctionWrapper(lyr, func_cfg)
    result = f(a="pple", b="eagle")
    assert result[0] == "apple  beagle  couple"
    assert result[1]["foo"] == "bar"
    assert "a" not in f._kwargs
    func_cfg = {
        "function": "tests.utils.a_function",
        "args": ["bar", "ouple"]
    }
    f = datacube_ows.config_utils.FunctionWrapper(lyr, func_cfg)
    result = f("pple")
    assert result[0] == "apple  bbar  couple"
    assert f.band_mapper is None
    f = datacube_ows.config_utils.FunctionWrapper(lyr, func_cfg)
    result = f()
    assert result[0] == "abar  bouple  c3"
    assert f.band_mapper is None
    func_cfg = {
        "function": "so_fake.not_real.not_a_function",
        "args": ["bar", "ouple"]
    }
    with pytest.raises(datacube_ows.config_utils.ConfigException) as e:
        f = datacube_ows.config_utils.FunctionWrapper(lyr, func_cfg)
    assert "Could not import python object" in str(e.value)
    assert "so_fake.not_real.not_a_function" in str(e.value)

def test_func_naked():
    lyr = MagicMock()
    with pytest.raises(datacube_ows.config_utils.ConfigException) as e:
        f = datacube_ows.config_utils.FunctionWrapper(lyr, {
            "function": a_function,
        })
    assert str("Directly including callable objects in configuration is no longer supported.")
    with pytest.raises(datacube_ows.config_utils.ConfigException) as e:
        f = datacube_ows.config_utils.FunctionWrapper(lyr, a_function)
    assert str("Directly including callable objects in configuration is no longer supported.")
    f = datacube_ows.config_utils.FunctionWrapper(lyr, {
        "function": a_function,
    }, stand_alone=True)
    assert f("ardvark", "bllbbll")[0] == "aardvark  bbllbbll  c3"
    f = datacube_ows.config_utils.FunctionWrapper(lyr, a_function, stand_alone=True)
    assert f("ardvark", "bllbbll")[0] == "aardvark  bbllbbll  c3"


def test_base_class_unready():
    cfg = datacube_ows.config_utils.OWSConfigEntry({"foo": "bar", "pot": "noodle"})
    cfg.declare_unready("wow")
    cfg.declare_unready("pow")
    with pytest.raises(datacube_ows.config_utils.ConfigException) as e:
        assert cfg.wow == "bagger"
    assert "wow" in str(e.value)
    assert "The following parameters have not been initialised" in str(e.value)
    cfg.wow = "bagger"
    with pytest.raises(datacube_ows.config_utils.ConfigException) as e:
        cfg.make_ready(MagicMock())
    assert "pow" in str(e.value)
    assert "The following parameters have not been initialised" in str(e.value)
    cfg.pow = "splat"
    cfg.make_ready(MagicMock())
    with pytest.raises(datacube_ows.config_utils.ConfigException) as e:
        cfg.declare_unready("woah")
    assert "Cannot declare woah as unready on a ready object" in str(e.value)

def test_base_class_get():
    cfg = datacube_ows.config_utils.OWSConfigEntry({"foo": "bar", "pot": "noodle"})
    assert cfg.get("wow", "bagger") == "bagger"
