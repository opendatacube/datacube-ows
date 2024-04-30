# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import os

import pytest

from datacube_ows.cfg_parser_impl import main


def test_cfg_parser_simple(runner):
    result = runner.invoke(main, [])
    assert result.exit_code == 0


def test_cfg_parser_parse_only(runner):
    result = runner.invoke(main, ["check", "-p"])
    print(repr(result))
    assert result.exit_code == 0


def test_cfg_parser_folder_hierarchy(runner):
    result = runner.invoke(main, ["check", "-f"])
    assert result.exit_code == 0


def test_cfg_parser_styles(runner):
    result = runner.invoke(main, ["check", "-s"])
    assert result.exit_code == 0


def test_cfg_parser_folder_hierarchy_and_styles(runner):
    result = runner.invoke(main, ["check", "-f", "-s"])
    assert result.exit_code == 0


def test_cfg_parser_folders_parse_only(runner):
    result = runner.invoke(main, ["check", "-f", "-p"])
    assert result.exit_code == 1


def test_cfg_parser_input_file_compare(runner):
    this_dir = os.path.dirname(os.path.dirname(__file__))
    result = runner.invoke(main, ["check", "-i", f"{this_dir}/ows_cfg_report.json"])
    assert result.exception is None
    assert b"Configuration parsed OK" in result.stdout_bytes
    assert result.exit_code == 0


@pytest.mark.xfail(reason="Permission denied")
def test_cfg_parser_msg_file(runner):
    result = runner.invoke(main, ["extract", "-m", "messages.po"])
    assert result.exit_code == 0


def test_cfg_parser_msg_file_null(runner):
    result = runner.invoke(main, ["extract", "-m", "/dev/null"])
    assert result.exit_code == 0


def test_cfg_parser_msg_file_null_badcfg(runner):
    result = runner.invoke(main, ["extract", "-m", "/dev/null", "integration_tests.cfg.ows_test_cfg_bad.ows_cfg"])
    assert result.exit_code == 0


@pytest.mark.xfail(reason="Permission denied")
def test_cfg_parser_output_file_compare(runner):
    result = runner.invoke(main, ["check", "-o", "inventory.json"])
    assert result.exit_code == 0


def test_cfg_parser_output_file_compare_null(runner):
    result = runner.invoke(main, ["check", "-o", "/dev/null"])
    assert result.exception is None
    assert b"Configuration parsed OK" in result.stdout_bytes
    assert result.exit_code == 0


def test_cfg_parser_version(runner):
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0


def test_cfg_parser_bad_cfgenv(runner):
    result = runner.invoke(main, ["check"], env={"DATACUBE_OWS_CFG": "integration_tests.cfg.ows_test_cfg_bad.ows_cfg"})
    assert result.exit_code == 1


def test_cfg_parser_good_cfgarg(runner):
    result = runner.invoke(main, ["check", "integration_tests.cfg.ows_test_cfg.ows_cfg"])
    assert result.exit_code == 0


def test_cfg_parser_bad_cfgarg(runner):
    result = runner.invoke(main, ["check", "integration_tests.cfg.ows_test_cfg.ows_cfg", "integration_tests.cfg.ows_test_cfg_bad.ows_cfg"])
    assert result.exit_code == 1


def test_cfg_write_new_translation_directory(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["translation", "-n", "-m", f"{this_dir}/cfg/message.po", "-d", f"{this_dir}/cfg/test_translations", "-D", "ows_cfg", "de"])
    assert result.exit_code == 0


def test_cfg_write_update_translation_directory(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["translation", "-m", f"{this_dir}/cfg/message.po", "-d", f"{this_dir}/cfg/test_translations", "-D", "ows_cfg", "de"])
    assert result.exit_code == 0


def test_cfg_write_new_translation_directory_cfg(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["translation", "-n",
                                  "-d", f"{this_dir}/cfg/test_translations",
                                  "-D", "ows_cfg",
                                  "-c", "integration_tests.cfg.ows_test_cfg.ows_cfg",
                                  "de"])
    assert result.exit_code == 0


def test_cfg_write_new_translation_directory_all_langs(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["translation", "-n", "-m", f"{this_dir}/cfg/message.po", "-d", f"{this_dir}/cfg/test_translations", "-D", "ows_cfg", "all"])
    assert result.exit_code == 0


def test_cfg_write_update_translation_directory_all_langs(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["translation", "-m", f"{this_dir}/cfg/message.po", "-d", f"{this_dir}/cfg/test_translations", "-D", "ows_cfg", "all"])
    assert result.exit_code == 0


def test_cfg_write_new_translation_directory_all_bad_cfg(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["translation", "-n",
                                  "-m", f"{this_dir}/cfg/message.po",
                                  "-d", f"{this_dir}/cfg/test_translations",
                                  "-D", "ows_cfg",
                                  "-c", "integration_tests.cfg.ows_test_cfg_bad.ows_cfg",
                                  "all"])
    assert result.exit_code == 1


def test_cfg_write_new_translation_directory_no_domain(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["translation", "-n",
                                  "-m", f"{this_dir}/cfg/message.po",
                                  "-d", f"{this_dir}/cfg/test_translations",
                                  "all"])
    assert result.exit_code == 0


def test_cfg_write_new_translation_directory_no_msg_file(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["translation", "-n",
                                  "-d", f"{this_dir}/cfg/test_translations",
                                  "-D", "ows_cfg",
                                  "-c", "integration_tests.cfg.ows_test_cfg_bad.ows_cfg",
                                  "all"])
    assert result.exit_code == 1

def test_cfg_write_new_translation_directory_missing_msg_file(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["translation", "-n",
                                  "-d", f"{this_dir}/cfg/test_translations",
                                  "-m", f"{this_dir}/cfg/non_existent_file.po",
                                  "-D", "ows_cfg",
                                  "all"])
    assert result.exit_code == 1

def test_cfg_write_translation_directory_cfg_directory(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["translation",
                                  "-m", f"{this_dir}/cfg/message.po",
                                  "-D", "ows_cfg",
                                  "all"])
    assert result.exit_code == 0

def test_cfg_write_new_translation_directory_no_directory(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["translation", "-n",
                                  "-m", f"{this_dir}/cfg/message.po",
                                  "-D", "ows_cfg",
                                  "-c", "integration_tests.cfg.ows_test_cfg_no_i18n.ows_cfg",
                                  "all"])
    assert result.exit_code == 1
    result = runner.invoke(main, ["translation", "-n",
                                  "-D", "ows_cfg",
                                  "-d", f"{this_dir}/cfg/test_translations",
                                  "-c", "integration_tests.cfg.ows_test_cfg_no_i18n.ows_cfg",
                                  "all"])
    assert result.exit_code == 1


def test_cfg_new_translation_no_language(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["translation", "-n", "-m", f"{this_dir}/cfg/message.po", "-d", f"{this_dir}/cfg/test_translations", "-D", "ows_cfg"])
    assert result.exit_code == 1


@pytest.mark.xfail(reason="Permission denied")
def test_cfg_parser_compile(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["compile", "-d", f"{this_dir}/cfg/test_translations", "-D", "ows_cfg", "en"])
    assert result.exit_code == 0

@pytest.mark.xfail(reason="Permission denied")
def test_cfg_parser_compile_all(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["compile", "-d", f"{this_dir}/cfg/test_translations", "-D", "ows_cfg", "all"])
    assert result.exit_code == 0


def test_cfg_parser_compile_no_lang(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["compile", "-d", f"{this_dir}/cfg/test_translations", "-D", "ows_cfg"])
    assert result.exit_code == 1


def test_cfg_parser_compile_no_domain(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["compile", "-d", f"{this_dir}/cfg/test_translations", "en"])
    assert result.exit_code == 0


@pytest.mark.xfail(reason="Permission denied")
def test_cfg_parser_compile_default_dir(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["compile", "en"])
    assert result.exit_code == 0


def test_cfg_parser_compile_no_dir(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["compile", "-c", "integration_tests.cfg.ows_test_cfg_no_i18n.ows_cfg", "en"])
    assert result.exit_code == 1

def test_cfg_parser_compile_bad_cfg(runner):
    this_dir = os.path.dirname(__file__)
    result = runner.invoke(main, ["compile",
                                  "-c", f"integration_tests.cfg.ows_test_cfg_bad.ows_cfg",
                                  "-d", f"{this_dir}/cfg/test_translations",
                                  "en"])
    assert result.exit_code == 1
