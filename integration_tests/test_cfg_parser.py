import os

import pytest

from datacube_ows.cfg_parser import main


def test_cfg_parser_simple(runner):
    result = runner.invoke(main, [])
    assert result.exit_code == 0


def test_cfg_parser_parse_only(runner):
    result = runner.invoke(main, ["-p"])
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
def test_cfg_parser_output_file_compare(runner):
    result = runner.invoke(main, ["-o", "inventory.json"])
    assert result.exit_code == 0


def test_cfg_parser_version(runner):
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
