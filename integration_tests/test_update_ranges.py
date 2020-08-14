"""Test update ranges on DB using Click testing
https://click.palletsprojects.com/en/7.x/testing/
"""
import os

from datacube_ows.update_ranges import main

def test_updates_ranges_schema(runner):
    result = runner.invoke(main,["--schema","--role",os.getenv("DB_USERNAME")])
    assert 'Cannot find SQL resource' not in result.output
    assert result.exit_code == 0

def test_update_ranges_views(runner):
    result = runner.invoke(main,["--views","--blocking"])
    assert 'Cannot find SQL resource' not in result.output
    assert result.exit_code == 0

    result = runner.invoke(main,["--views"])
    assert 'Cannot find SQL resource' not in result.output
    assert result.exit_code == 0

def test_update_version(runner):
    result = runner.invoke(main,["--version"])
    assert 'Open Data Cube Open Web Services (datacube-ows) version' in result.output
    assert result.exit_code == 0

def test_update_ranges_product(runner):
    result = runner.invoke(main,["ls8_usgs_level1_scene_layer"])
    assert 'ERROR' not in result.output
    assert result.exit_code == 0

def test_update_ranges(runner):
    result = runner.invoke(main)
    assert 'ERROR' not in result.output
    assert result.exit_code == 0
