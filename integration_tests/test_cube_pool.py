import pytest
from datacube import Datacube

from datacube_ows.cube_pool import get_cube, release_cube, pool_size


def test_basic_cube_pool():
    dc_1 = get_cube(app="test")
    dc_2 = get_cube(app="test")
    assert dc_1 != dc_2
    release_cube(dc_1, app="test")
    release_cube(dc_2, app="test")
    assert pool_size(app="test") >= 2


def test_release_nonalloc():
    dc_alloc = get_cube(app="test")
    dc_unalloc = Datacube(app="test")
    assert dc_alloc != dc_unalloc
    release_cube(dc_alloc, app="test")
    with pytest.raises(Exception) as e:
        release_cube(dc_unalloc, app="test")
    assert "non-pool database" in str(e.value)

