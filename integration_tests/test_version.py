# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

"""Test update ranges on DB using Click testing
https://click.palletsprojects.com/en/7.x/testing/
"""
from datacube_ows.__init__ import __version__
from datacube_ows.update_ranges_impl import main


def test_updates_ranges_schema(runner, role_name):
    result = runner.invoke(main, ["--version"])
    assert __version__ in result.output
    assert result.exit_code == 0
