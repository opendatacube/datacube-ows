from datacube_ows.styles.base import StyleDefBase
import numpy as np
import pandas as pd
import xarray as xr

def test_multidate_handler():
    # TODO: Consolidate these into a fixture
    class fake_data:
        def __init__(self):
            self.nodata = np.nan
        def item(self):
            return np.nan

    class fake_dataset:
        def __getitem__(self, key):
            return fake_data()

    class fake_mdh_style:
        include_in_feature_info = True
        def __init__(self):
            self.product = "test"
            self.needed_bands = ["test"]
            self.index_function = lambda x: fake_data()

    data = np.random.randint(0, 255, size=(4, 3), dtype=np.uint8)
    locs = ["IA", "IL", "IN"]
    times = pd.date_range("2000-01-01", periods=4)
    fake_mask = xr.DataArray(data, coords=[times, locs], dims=["time", "space"])

    fake_cfg = {
        "allowed_count_range" : [0, 10],
        "aggregator_function" : "datacube_ows.band_utils.multi_date_delta"
    }

    mdh = StyleDefBase.MultiDateHandler(fake_mdh_style(), fake_cfg)
    assert mdh is not None
    assert not mdh.legend(None)
    assert mdh.collapse_mask(fake_mask) is not None
