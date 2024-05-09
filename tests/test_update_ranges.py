# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

"""Test update ranges on DB using Click testing
https://click.palletsprojects.com/en/7.x/testing/
"""
import pytest
from click.testing import CliRunner
from datacube_ows.update_ranges_impl import main, run_sql


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def role_name():
    return "role1"


@pytest.fixture
def layer_name():
    return "a_layer"


def test_update_ranges_misuse_cases(runner, role_name, layer_name):
    result = runner.invoke(main, ["--schema", layer_name])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--cleanup", layer_name])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--read-role", role_name, layer_name])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--write-role", role_name, layer_name])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--views", "--cleanup"])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--views", layer_name])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--views", "--schema"])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--views", "--read-role", role_name])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--views", "--write-role", role_name])
    assert "Sorry" in result.output
    assert result.exit_code == 1


def test_run_sql(minimal_dc):
    assert not run_sql(minimal_dc, "sql/no_such_directory")

    assert not run_sql(minimal_dc, "templates")

    assert not run_sql(minimal_dc, "ows_schema/grants/read_only")
