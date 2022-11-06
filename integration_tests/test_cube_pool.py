from datacube import Datacube

from datacube_ows.cube_pool import get_cube


def test_basic_cube_pool():
    dc_1 = get_cube(app="test")
    dc_2 = get_cube(app="test")
    assert dc_1 == dc_2
    dc_unalloc = Datacube(app="test")
    assert dc_1 != dc_unalloc
