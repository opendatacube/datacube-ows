# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
"""Test update ranges on DB using Click testing
https://click.palletsprojects.com/en/7.x/testing/
"""
from datacube_ows.update_ranges_impl import main


def test_updates_ranges_schema(runner, role_name):
    result = runner.invoke(main, ["--schema", "--role", role_name])
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
    assert "Unrecognised product name" in result.output
    assert result.exit_code == 1


def test_update_ranges(runner):
    result = runner.invoke(main)
    assert "ERROR" not in result.output
    assert result.exit_code == 0


def test_update_ranges_misuse_cases(runner, role_name, product_name):
    result = runner.invoke(main, ["--schema"])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--role", role_name])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--views", product_name])
    assert "Sorry" in result.output
    assert result.exit_code == 1

    result = runner.invoke(main, ["--schema", product_name])
    assert "Sorry" in result.output
    assert result.exit_code == 1
