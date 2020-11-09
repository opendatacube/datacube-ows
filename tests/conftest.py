from unittest.mock import MagicMock

import pytest

@pytest.fixture
def flask_client(monkeypatch):
    monkeypatch.setenv("DEFER_CFG_PARSE", "yes")
    from datacube_ows.ogc import app
    with app.test_client() as client:
        yield client


@pytest.fixture
def minimal_dc():
    dc = MagicMock()
    nb = MagicMock()
    nb.index = ['band1', 'band2', 'band3', 'band4']
    nb.__getitem__.return_value = {
        "band1": -999,
        "band2": -999,
        "band3": float("nan"),
        "band4": "nan",
    }
    lmo = MagicMock()
    lmo.loc = {
        "foo": nb,
        "bar": nb,
    }
    dc.list_measurements.return_value = lmo

    def product_by_name(s):
        if 'lookupfail' in s:
            return None
        else:
            return MagicMock()
    dc.index.products.get_by_name = product_by_name
    return dc