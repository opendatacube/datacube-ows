import pytest
import os
from datacube_ows.ows_configuration import read_config, ConfigException


def test_cfg_direct():
    os.environ["DATACUBE_OWS_CFG"] = "{\"test\": 12345}"
    cfg = read_config()

    assert cfg["test"] == 12345


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


def test_cfg_py_infinite_1():
    os.environ["DATACUBE_OWS_CFG"] = "tests.cfg.nested.infinite_1"
    try:
        cfg = read_config()
        assert False
    except ConfigException as e:
        assert str(e).startswith("Cyclic inclusion")


def test_cfg_py_infinite_2():
    os.environ["DATACUBE_OWS_CFG"] = "tests.cfg.nested.infinite_2"
    try:
        cfg = read_config()
        assert False
    except ConfigException as e:
        assert str(e).startswith("Cyclic inclusion")


def test_cfg_json_simple():
    os.environ["DATACUBE_OWS_CFG"] = "tests/cfg/simple.json"
    cfg = read_config()

    assert cfg["test"] == 1234


def test_cfg_json_nested_1():
    os.environ["DATACUBE_OWS_CFG"] = "tests/cfg/nested_1.json"
    cfg = read_config()

    assert cfg["test"] == 1234


def test_cfg_json_nested_2():
    os.environ["DATACUBE_OWS_CFG"] = "tests/cfg/nested_2.json"
    cfg = read_config()

    assert len(cfg) == 2
    assert cfg[0]["test"] == 88888
    assert cfg[1]["test"] == 1234


def validated_nested_3(cfg):
    assert cfg["test"] == 2222
    assert len(cfg["things"]) == 3
    assert cfg["things"][0]["test"] == 22562
    assert cfg["things"][0]["thing"] is None
    assert cfg["things"][1]["test"] == 22563
    assert cfg["things"][1]["thing"]["test"] == 1234
    assert cfg["things"][2]["test"] == 22564
    assert cfg["things"][2]["thing"]["test"] == 1234


def test_cfg_json_nested_3():
    os.environ["DATACUBE_OWS_CFG"] = "tests/cfg/nested_3.json"
    cfg = read_config()
    validated_nested_3(cfg)


def test_cfg_json_nested_4():
    os.environ["DATACUBE_OWS_CFG"] = "tests/cfg/nested_4.json"
    cfg = read_config()

    assert cfg["test"] == 3222
    assert len(cfg["things"]) == 3
    assert cfg["things"][0]["test"] == 2572
    assert cfg["things"][0]["thing"] is None
    assert cfg["things"][1]["test"] == 2573
    assert cfg["things"][1]["thing"]["test"] == 1234
    assert cfg["things"][2]["test"] == 2574
    validated_nested_3(cfg["things"][2]["thing"])


def test_cfg_json_infinite_1():
    os.environ["DATACUBE_OWS_CFG"] = "tests/cfg/infinite_1.json"
    try:
        cfg = read_config()
        assert False
    except ConfigException as e:
        assert str(e).startswith("Cyclic inclusion")


def test_cfg_json_infinite_2():
    os.environ["DATACUBE_OWS_CFG"] = "tests/cfg/infinite_2.json"
    try:
        cfg = read_config()
        assert False
    except ConfigException as e:
        assert str(e).startswith("Cyclic inclusion")


def test_cfg_py_mixed_1():
    os.environ["DATACUBE_OWS_CFG"] = "tests.cfg.mixed_nested.mixed_1"
    cfg = read_config()

    assert cfg["test"] == 1234


def test_cfg_py_mixed_2():
    os.environ["DATACUBE_OWS_CFG"] = "tests.cfg.mixed_nested.mixed_2"
    cfg = read_config()

    assert cfg["test"] == 5224
    assert cfg["subtest"]["test"] == 1234


def test_cfg_py_mixed_3():
    os.environ["DATACUBE_OWS_CFG"] = "tests.cfg.mixed_nested.mixed_3"
    cfg = read_config()

    assert cfg["test"] == 2634
    assert cfg["subtest"]["test_py"]["test"] == 123
    assert cfg["subtest"]["test_json"]["test"] == 1234


def test_cfg_json_mixed():
    os.environ["DATACUBE_OWS_CFG"] = "tests/cfg/mixed_nested.json"
    cfg = read_config()

    assert cfg["test"] == 9364
    assert cfg["subtest"]["test_py"]["test"] == 123
    assert cfg["subtest"]["test_json"]["test"] == 1234

