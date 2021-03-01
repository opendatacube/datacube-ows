import datetime
import pytest

import xarray as xr
import numpy as np

from datacube_ows.styles import ows_style_standalone


def dummy_da(val, name, coords, attrs=None, dtype=np.float64):
    if attrs is None:
        attrs={}
    dims = [n for n, a in coords]
    data = np.ndarray([len(a) for n, a in coords], dtype=dtype)
    coords = dict(coords)
    data.fill(val)
    output = xr.DataArray(
        data,
        coords=coords,
        dims=dims,
        attrs=attrs,
        name=name,
    )
    return output

coords = [
    ('x', [
        0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0,
        10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0,
    ]),
    ('y', [-5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0]),
    ('time', [np.datetime64(datetime.date.today())])
]

@pytest.fixture
def dummy_raw_data():
    output = xr.Dataset({
        "ir": dummy_da(3, "ir", coords),
        "red": dummy_da(5, "red", coords),
        "green": dummy_da(7, "green", coords),
        "blue": dummy_da(2, "blue", coords),
        "uv": dummy_da(-1, "uv", coords),
    })
    return output

@pytest.fixture
def null_mask():
    return dummy_da(True, "mask", coords, dtype=np.bool)

@pytest.fixture
def simple_rgb_style_cfg():
    return {
        "name": "test_style",
        "title": "Test Style",
        "abstract": "This is a Test Style for Datacube WMS",
        "needed_bands": ["red", "green", "blue"],
        "scale_factor": 1.0,
        "components": {
            "red": {"red": 1.0},
            "green": {"green": 1.0},
            "blue": {"blue": 1.0}
        }
    }


def test_rgb_style_instantiation(dummy_raw_data, null_mask, simple_rgb_style_cfg):
    style = ows_style_standalone(simple_rgb_style_cfg)
    style.make_ready(None)
    mask = style.to_mask(dummy_raw_data, null_mask)
    result = style.transform_data(dummy_raw_data, mask)
    for channel in ("red", "green", "blue"):
        assert channel in result.data_vars.keys()