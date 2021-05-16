# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import os

import pytest

from datacube_ows.cfg_parser import main


def test_cfg_parser_simple(runner):
    result = runner.invoke(main, [])
    assert result.exit_code == 0


def test_cfg_parser_parse_only(runner):
    result = runner.invoke(main, ["-p"])
    assert result.exit_code == 0


def test_cfg_parser_folder_hierarchy(runner):
    result = runner.invoke(main, ["-f"])
    assert result.exit_code == 0


def test_cfg_parser_styles(runner):
    result = runner.invoke(main, ["-s"])
    assert result.exit_code == 0


def test_cfg_parser_folder_hierarchy_and_styles(runner):
    result = runner.invoke(main, ["-f", "-s"])
    assert result.exit_code == 0


def test_cfg_parser_folders_parse_only(runner):
    result = runner.invoke(main, ["-f", "-p"])
    assert result.exit_code == 1


def test_cfg_parser_input_file_compare(runner):
    this_dir = os.path.dirname(os.path.dirname(__file__))
    result = runner.invoke(main, ["-i", f"{this_dir}/ows_cfg_report.json"])
    assert result.exit_code == 0


@pytest.mark.xfail(reason="Permission denied")
def test_cfg_parser_msg_file(runner):
    result = runner.invoke(main, ["-m", "messages.po"])
    assert result.exit_code == 0


def test_cfg_parser_msg_file_null(runner):
    result = runner.invoke(main, ["-m", "/dev/null"])
    assert result.exit_code == 0


@pytest.mark.xfail(reason="Permission denied")
def test_cfg_parser_output_file_compare(runner):
    result = runner.invoke(main, ["-o", "inventory.json"])
    assert result.exit_code == 0


def test_cfg_parser_output_file_compare_null(runner):
    result = runner.invoke(main, ["-o", "/dev/null"])
    assert result.exit_code == 0


def test_cfg_parser_version(runner):
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0


def test_cfg_parser_bad_cfgenv(runner):
    result = runner.invoke(main, [], env={"DATACUBE_OWS_CFG": "integration_tests.cfg.ows_test_cfg_bad.ows_cfg"})
    assert result.exit_code == 1


def test_cfg_parser_bad_cfgarg(runner):
    result = runner.invoke(main, ["integration_tests.cfg.ows_test_cfg.ows,cfg", "integration_tests.cfg.ows_test_cfg_bad.ows_cfg"])
    assert result.exit_code == 1

