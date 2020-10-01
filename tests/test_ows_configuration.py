from datacube_ows.ows_configuration import BandIndex
from unittest.mock import patch, MagicMock
import pytest


def test_band_index():
    dc = MagicMock()
    prod = MagicMock()
    prod.name = "prod_name"
    nb = MagicMock()
    nb.index = ['band1', 'band2', 'band3', 'band4']
    nb.get.return_val = {
        "band1": -999,
        "band2": -999,
        "band3": -999,
        "band4": -999,
    }
    dc.list_measurements().loc = {
        "prod_name": nb
    }

    foo =dc.list_measurements().loc["prod_name"]

    cfg = {
        "band1": [],
        "band2": ["alias1"],
        "band3": ["alias2", "alias3"],
        "band4": ["band4", "alias4"],
    }

    bidx = BandIndex(prod, cfg, dc)