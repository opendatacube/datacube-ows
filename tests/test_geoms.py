import json

from shapely.geometry import shape
from datacube.utils.geometry import Geometry
import pytest

from datacube_ows.data import get_coordlist

TEST_GEOMS = "tests/geoms/all_sorts.json"

def get_shape(geojson_file: str, index: int):
    with open(geojson_file) as f:
        feature = json.load(f)["features"][index]
        try:
            geom = Geometry(feature["geometry"])
        except AssertionError:
            geom = shape(feature["geometry"])
    return geom


def test_coordlists_point():
    # Test exception handling
    with pytest.raises(Exception) as excinfo:
        bad_coords = get_coordlist(get_shape(TEST_GEOMS, 0))
    assert "Unexpected extent/geobox polygon geometry type:" in str(excinfo.value)

def test_coordlists_polygon():
    # Polygons
    assert len(get_coordlist(get_shape(TEST_GEOMS, 2))) > 0

def test_coordlists_mpolygon():
    # MultiPolygon
    assert len(get_coordlist(get_shape(TEST_GEOMS, 3))) > 0

def test_coordlists_gcollection():
    #`GeometryCollection
    assert len(get_coordlist(get_shape(TEST_GEOMS, 4))) > 0
