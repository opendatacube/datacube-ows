# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

"""Test update ranges on DB using Click testing
https://click.palletsprojects.com/en/7.x/testing/
"""
from datacube_ows.update_ranges_impl import main


def test_update_ranges_schema_without_roles(runner):
    result = runner.invoke(main, ["--schema"])
    assert "Cannot find SQL resource" not in result.output
    assert result.exit_code == 0


def test_update_ranges_schema_with_roles(runner, role_name):
    result = runner.invoke(main, ["--schema", "--read-role", role_name, "--write-role", role_name])
    assert "Cannot find SQL resource" not in result.output
    assert result.exit_code == 0


def test_update_ranges_roles_only(runner, role_name):
    result = runner.invoke(main, ["--read-role", role_name, "--write-role", role_name])
    assert "Cannot find SQL resource" not in result.output
    assert result.exit_code == 0


def test_update_ranges_cleanup(runner):
    result = runner.invoke(main, ["--cleanup"])
    assert "Cannot find SQL resource" not in result.output
    assert result.exit_code == 0


def test_update_ranges_views(runner):
    result = runner.invoke(main, ["--views"])
    assert "Cannot find SQL resource" not in result.output
    assert result.exit_code == 0


def test_update_version(runner):
    result = runner.invoke(main, ["--version"])
    assert "Open Data Cube Open Web Services (datacube-ows) version" in result.output
    assert result.exit_code == 0


def test_update_ranges_product(runner, product_name):
    result = runner.invoke(main, [product_name])
    assert "ERROR" not in result.output
    assert result.exit_code == 0


def test_update_ranges_bad_product(runner, product_name):
    result = runner.invoke(main, ["not_a_real_product_name"])
    assert "not_a_real_product_name" in result.output
    assert "does not exist in the OWS configuration - skipping" in result.output
    assert result.exit_code == 1


def test_update_ranges(runner):
    result = runner.invoke(main)
    assert "ERROR" not in result.output
    assert result.exit_code == 0


def test_update_ranges_misuse_cases(runner, role_name, product_name):
    result = runner.invoke(main, ["--schema", product_name])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--cleanup", product_name])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--read-role", "role", product_name])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--write-role", "role", product_name])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--views", "--schema"])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--views", "--read-role", "role"])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--views", "--write-role", "role"])
    assert "Sorry" in result.output
    assert result.exit_code == 1

