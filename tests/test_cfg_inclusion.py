import pytest
import os
from datacube_ows.ows_configuration import read_config


def test_cfg_py_simple_0():
    os.environ["DATACUBE_OWS_CFG"] = "tests.cfg.simple.simple"
    cfg = read_config()

    assert cfg["test"] == 123


def test_cfg_py_simple_1():
    os.environ["DATACUBE_OWS_CFG"] = "tests.cfg.simple.simple1"
    cfg = read_config()

    assert cfg["test"] == 1


def test_cfg_py_nested_0():
    os.environ["DATACUBE_OWS_CFG"] = "tests.cfg.nested.nested"
    cfg = read_config()

    assert cfg["test"] == 123


def test_cfg_py_nested_1():
    os.environ["DATACUBE_OWS_CFG"] = "tests.cfg.nested.nested_1"
    cfg = read_config()

    assert len(cfg) == 2
    assert cfg[0]["test"] == 8888
    assert cfg[1]["test"] == 1


def test_cfg_py_nested_2():
    os.environ["DATACUBE_OWS_CFG"] = "tests.cfg.nested.nested_2"
    cfg = read_config()

    assert cfg["subtest"]["test"] == 2


def test_cfg_py_nested_3():
    os.environ["DATACUBE_OWS_CFG"] = "tests.cfg.nested.nested_3"
    cfg = read_config()

    assert cfg["test"] == 233
    assert len(cfg["things"]) == 3
    assert cfg["things"][0]["test"] == 2562
    assert cfg["things"][0]["thing"] is None
    assert cfg["things"][1]["test"] == 2563
    assert cfg["things"][1]["thing"]["test"] == 123
    assert cfg["things"][2]["test"] == 2564
    assert cfg["things"][2]["thing"]["test"] == 3


def test_cfg_py_nested_4():
    os.environ["DATACUBE_OWS_CFG"] = "tests.cfg.nested.nested_4"
    cfg = read_config()

    assert cfg["test"] == 222
    assert len(cfg["things"]) == 3
    assert cfg["things"][0]["test"] == 2572
    assert cfg["things"][0]["thing"] is None
    assert cfg["things"][1]["test"] == 2573
    assert cfg["things"][1]["thing"]["test"] == 123
    assert cfg["things"][2]["test"] == 2574
    ncfg = cfg["things"][2]["thing"]

    assert ncfg["test"] == 233
    assert len(ncfg["things"]) == 3
    assert ncfg["things"][0]["test"] == 2562
    assert ncfg["things"][0]["thing"] is None
    assert ncfg["things"][1]["test"] == 2563
    assert ncfg["things"][1]["thing"]["test"] == 123
    assert ncfg["things"][2]["test"] == 2564
    assert ncfg["things"][2]["thing"]["test"] == 3



