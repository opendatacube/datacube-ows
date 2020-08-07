from datacube_ows.mv_index import MVSelectOpts

def test_all():
    stv = None

    assert MVSelectOpts.ALL.sel(stv) == [None]

class MockSTV:
    def __init__(self, id):
        self.id = id
        self.c = self

def test_ids_datasets():
    class MockSTV:
        def __init__(self, id):
            self.id = id
            self.c = self
    stv = MockSTV(72)
    assert MVSelectOpts.IDS.sel(stv) == [72]
    assert MVSelectOpts.DATASETS.sel(stv) == [72]

def test_extent():
    sel= MVSelectOpts.EXTENT.sel(None)
    assert len(sel) == 1
    assert str(sel[0]) == "ST_AsGeoJSON(ST_Union(spatial_extent))"

def test_count():
    from sqlalchemy import text
    stv = MockSTV(id=text("foo"))
    sel = MVSelectOpts.COUNT.sel(stv)
    assert len(sel) == 1
    assert str(sel[0]) == "count(foo)"