# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import os
import sys

import pytest

from datacube_ows.config_utils import ConfigException, get_file_loc
from datacube_ows.ows_configuration import read_config

src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.append(src_dir)


def test_get_file_loc(monkeypatch) -> None:
    monkeypatch.setenv("DATACUBE_OWS_CFG_ALLOW_S3", "YES")
    cwd = os.getcwd()

    assert get_file_loc("foo.bar") == cwd
    assert get_file_loc("./foo.bar") == cwd
    assert get_file_loc("baz/foo.bar") == os.path.join(cwd, "baz")
    assert get_file_loc("/etc/conf/foo.bar") == "/etc/conf"
    assert get_file_loc("s3://testbucket/foo.bar") == "s3://testbucket"
    assert (
        get_file_loc("s3://testbucket/frobnicate/biz/baz.bar")
        == "s3://testbucket/frobnicate/biz"
    )


def test_get_file_loc_s3_disable(monkeypatch) -> None:
    with pytest.raises(ConfigException):
        _ = get_file_loc("s3://testbucket/foo.bar")

    monkeypatch.setenv("DATACUBE_OWS_CFG_ALLOW_S3", "NO")
    with pytest.raises(ConfigException):
        _ = get_file_loc("s3://testbucket/foo.bar")

    monkeypatch.setenv("DATACUBE_OWS_CFG_ALLOW_S3", "FALSE")
    with pytest.raises(ConfigException):
        _ = get_file_loc("s3://testbucket/foo.bar")

    monkeypatch.setenv("DATACUBE_OWS_CFG_ALLOW_S3", "0")
    with pytest.raises(ConfigException):
        _ = get_file_loc("s3://testbucket/foo.bar")

    monkeypatch.setenv("DATACUBE_OWS_CFG_ALLOW_S3", "N")
    with pytest.raises(ConfigException):
        _ = get_file_loc("s3://testbucket/foo.bar")


def test_get_file_loc_s3_enable(monkeypatch) -> None:
    monkeypatch.setenv("DATACUBE_OWS_CFG_ALLOW_S3", "YES")
    assert get_file_loc("s3://testbucket/foo.bar") == "s3://testbucket"

    monkeypatch.setenv("DATACUBE_OWS_CFG_ALLOW_S3", "TRUE")
    assert get_file_loc("s3://testbucket/dir/foo.bar") == "s3://testbucket/dir"

    monkeypatch.setenv("DATACUBE_OWS_CFG_ALLOW_S3", "1")
    assert (
        get_file_loc("s3://testbucket/nested/dir/foo.bar")
        == "s3://testbucket/nested/dir"
    )

    monkeypatch.setenv("DATACUBE_OWS_CFG_ALLOW_S3", "Y")
    assert get_file_loc("s3://testbucket/foo.bar") == "s3://testbucket"


def tests_get_file_loc_other_url(monkeypatch) -> None:
    monkeypatch.setenv("DATACUBE_OWS_CFG_ALLOW_S3", "N")
    with pytest.raises(ConfigException):
        _ = get_file_loc("http://testbucket/directory/foo.bar")
    monkeypatch.setenv("DATACUBE_OWS_CFG_ALLOW_S3", "Y")
    with pytest.raises(ConfigException):
        _ = get_file_loc("http://testbucket/another_directory/bar.foo")


def test_cfg_inject() -> None:
    cfg = read_config('{"test": 12345}')
    assert cfg["test"] == 12345


def test_cfg_not_a_dict(monkeypatch) -> None:
    with pytest.raises(ConfigException):
        read_config("nested.not_a_dict")


def test_cfg_direct(monkeypatch) -> None:
    monkeypatch.setenv("DATACUBE_OWS_CFG", '{"test": 12345}')
    cfg = read_config()

    assert cfg["test"] == 12345


def test_cfg_py_simple_0(monkeypatch) -> None:
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.simple.simple")
    cfg = read_config()

    assert cfg["test"] == 123


def test_cfg_py_simple_1(monkeypatch) -> None:
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.simple.simple1")
    cfg = read_config()

    assert cfg["test"] == 1


def test_cfg_py_nested_0(monkeypatch) -> None:
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.nested.nested")
    cfg = read_config()

    assert cfg["test"] == 123


def test_cfg_py_nested_1(monkeypatch) -> None:
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.nested.nested_1")
    cfg = read_config()

    member = cfg.get("this_test")
    assert member is not None
    assert isinstance(member, list)
    assert len(member) == 2
    first = member[0]
    assert isinstance(first, dict)
    assert first["test"] == 8888
    second = member[1]
    assert isinstance(second, dict)
    assert second["test"] == 1


def test_cfg_py_nested_2(monkeypatch) -> None:
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.nested.nested_2")
    cfg = read_config()
    subtest = cfg["subtest"]
    assert isinstance(subtest, dict)
    assert subtest["test"] == 2


def test_cfg_py_nested_3(monkeypatch) -> None:
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.nested.nested_3")
    cfg = read_config()

    assert cfg["test"] == 233
    things = cfg.get("things")
    assert isinstance(things, list)
    assert len(things) == 3
    first = things[0]
    assert isinstance(first, dict)
    assert first["test"] == 2562
    assert first["thing"] is None
    second = things[1]
    assert isinstance(second, dict)
    assert second["test"] == 2563
    second_thing = second.get("thing")
    assert isinstance(second_thing, dict)
    assert second_thing["test"] == 123
    third = things[2]
    assert isinstance(third, dict)
    assert third["test"] == 2564
    third_thing = third.get("thing")
    assert isinstance(third_thing, dict)
    assert third_thing["test"] == 3


def test_cfg_py_nested_4(monkeypatch) -> None:
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.nested.nested_4")
    cfg = read_config()

    assert cfg["test"] == 222
    things = cfg.get("things")
    assert isinstance(things, list)
    assert len(things) == 3
    first = things[0]
    assert isinstance(first, dict)
    assert first["test"] == 2572
    assert first["thing"] is None
    second = things[1]
    assert isinstance(second, dict)
    assert second["test"] == 2573
    second_thing = second.get("thing")
    assert isinstance(second_thing, dict)
    assert second_thing["test"] == 123
    third = things[2]
    assert isinstance(third, dict)
    assert third["test"] == 2574
    ncfg = third["thing"]

    assert isinstance(ncfg, dict)
    assert ncfg.get("test") == 233
    n_things = ncfg.get("things")
    assert isinstance(n_things, list)
    assert len(n_things) == 3
    n_first = n_things[0]
    assert isinstance(n_first, dict)
    assert n_first["test"] == 2562
    assert n_first["thing"] is None
    n_second = n_things[1]
    assert isinstance(n_second, dict)
    assert n_second["test"] == 2563
    n_second_thing = n_second.get("thing")
    assert isinstance(n_second_thing, dict)
    assert n_second_thing["test"] == 123
    n_third = n_things[2]
    assert isinstance(n_third, dict)
    assert n_third["test"] == 2564
    n_third_thing = n_third.get("thing")
    assert isinstance(n_third_thing, dict)
    assert n_third_thing["test"] == 3


def test_cfg_py_infinite_1(monkeypatch) -> None:
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.nested.infinite_1")
    with pytest.raises(ConfigException) as e:
        _ = read_config()
    assert str(e.value).startswith("Cyclic inclusion")


def test_cfg_py_infinite_2(monkeypatch) -> None:
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.nested.infinite_2")
    with pytest.raises(ConfigException) as e:
        _ = read_config()
    assert str(e.value).startswith("Cyclic inclusion")


def test_cfg_json_simple(monkeypatch) -> None:
    monkeypatch.chdir(src_dir)
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests/cfg/nested_1.json")
    cfg = read_config()

    assert cfg["test"] == 1234


def test_cfg_json_nested_2(monkeypatch) -> None:
    monkeypatch.chdir(src_dir)
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests/cfg/nested_2.json")
    cfg = read_config()

    this_test = cfg.get("this_test")
    assert isinstance(this_test, list)
    assert len(this_test) == 2
    first = this_test[0]
    assert isinstance(first, dict)
    assert first["test"] == 88888
    second = this_test[1]
    assert isinstance(second, dict)
    assert second["test"] == 1234


def validated_nested_3(cfg) -> None:
    assert cfg["test"] == 2222
    assert len(cfg["things"]) == 3
    assert cfg["things"][0]["test"] == 22562
    assert cfg["things"][0]["thing"] is None
    assert cfg["things"][1]["test"] == 22563
    assert cfg["things"][1]["thing"]["test"] == 1234
    assert cfg["things"][2]["test"] == 22564
    assert cfg["things"][2]["thing"]["test"] == 1234


def test_cfg_json_nested_3(monkeypatch) -> None:
    monkeypatch.chdir(src_dir)
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests/cfg/nested_3.json")
    cfg = read_config()
    validated_nested_3(cfg)


def test_cfg_json_nested_4(monkeypatch) -> None:
    monkeypatch.chdir(src_dir)
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests/cfg/nested_4.json")
    cfg = read_config()

    assert cfg["test"] == 3222
    things = cfg.get("things")
    assert isinstance(things, list)
    assert len(things) == 3
    first = things[0]
    assert isinstance(first, dict)
    assert first["test"] == 2572
    assert first["thing"] is None
    second = things[1]
    assert isinstance(second, dict)
    assert second["test"] == 2573
    second_thing = second.get("thing")
    assert isinstance(second_thing, dict)
    assert second_thing["test"] == 1234
    third = things[2]
    assert isinstance(third, dict)
    assert third["test"] == 2574
    validated_nested_3(third["thing"])


def test_cfg_json_infinite_1(monkeypatch) -> None:
    monkeypatch.chdir(src_dir)
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests/cfg/infinite_1.json")
    with pytest.raises(ConfigException) as e:
        _ = read_config()
    assert str(e.value).startswith("Cyclic inclusion")


def test_cfg_json_infinite_2(monkeypatch) -> None:
    monkeypatch.chdir(src_dir)
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests/cfg/infinite_2.json")
    with pytest.raises(ConfigException) as e:
        _ = read_config()
    assert str(e.value).startswith("Cyclic inclusion")


def test_cfg_py_mixed_1(monkeypatch) -> None:
    monkeypatch.chdir(src_dir)
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.mixed_nested.mixed_1")
    cfg = read_config()

    assert cfg["test"] == 1234


def test_cfg_py_broken_mixed(monkeypatch) -> None:
    monkeypatch.chdir(src_dir)
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.broken_nested.mixed_3")
    with pytest.raises(ConfigException) as e:
        _ = read_config()
    assert "Could not import python object" in str(e.value)
    assert "tests.cfg.simple.doesnt_exist" in str(e.value)


def test_cfg_py_mixed_2(monkeypatch) -> None:
    monkeypatch.chdir(src_dir)
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.mixed_nested.mixed_2")
    cfg = read_config()

    assert cfg["test"] == 5224
    subtest = cfg.get("subtest")
    assert isinstance(subtest, dict)
    assert subtest["test"] == 1234


def test_cfg_py_mixed_3(monkeypatch) -> None:
    monkeypatch.chdir(src_dir)
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.mixed_nested.mixed_3")
    cfg = read_config()

    assert cfg["test"] == 2634
    subtest = cfg.get("subtest")
    assert isinstance(subtest, dict)
    subtest_test_py = subtest.get("test_py")
    assert isinstance(subtest_test_py, dict)
    assert subtest_test_py["test"] == 123
    subtest_test_json = subtest.get("test_json")
    assert isinstance(subtest_test_json, dict)
    assert subtest_test_json["test"] == 1234


def test_cfg_json_mixed(monkeypatch) -> None:
    monkeypatch.chdir(src_dir)
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests/cfg/mixed_nested.json")
    cfg = read_config()

    assert cfg["test"] == 9364
    subtest = cfg.get("subtest")
    assert isinstance(subtest, dict)
    subtest_test_py = subtest.get("test_py")
    assert isinstance(subtest_test_py, dict)
    assert subtest_test_py["test"] == 123
    subtest_test_json = subtest.get("test_json")
    assert isinstance(subtest_test_json, dict)
    assert subtest_test_json["test"] == 1234
