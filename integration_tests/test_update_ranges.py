"""Test update ranges on DB using Click testing
https://click.palletsprojects.com/en/7.x/testing/
"""
import os

from datacube_ows.update_ranges import main

def test_updates_ranges_schema(runner):
    result = runner.invoke(main,["--schema","--role",os.getenv("DB_USERNAME")])
    assert result.exit_code == 0

def test_update_ranges_views(runner):
    result = runner.invoke(main,["--views","--blocking"])
    assert result.exit_code == 0

    result = runner.invoke(main,["--views"])
    assert result.exit_code == 0

def test_update_version(runner):
    result = runner.invoke(main,["--version"])
    assert result.exit_code == 0

def test_update_ranges_product(runner):
    result = runner.invoke(main,["ls8_usgs_level1_scene"])
    assert result.exit_code == 0

def test_update_ranges(runner):
    result = runner.invoke(main)
    assert result.exit_code == 0