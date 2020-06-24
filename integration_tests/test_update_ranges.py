"""Test update ranges on DB using Click testing
https://click.palletsprojects.com/en/7.x/testing/
"""
from datacube_ows.update_ranges import main

def test_update_ranges_views(runner):
    result = runner.invoke(main,["--views","--blocking"])
    assert result.exit_code == 0

def test_update_ranges(runner):
    result = runner.invoke(main)
    assert result.exit_code == 0