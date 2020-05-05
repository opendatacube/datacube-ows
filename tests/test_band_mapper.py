import datetime

import datacube_ows.band_mapper as bm
from datacube_ows.band_mapper import StyleDef

from datacube_ows.ows_configuration import BandIndex, OWSProductLayer

from xarray import DataArray, Dataset, concat
from unittest.mock import patch

import pytest

import numpy as np

@pytest.fixture
def product_layer():
    product_layer = OWSProductLayer.__new__(OWSProductLayer)
    product_layer.name = "test_product"
    product_layer.pq_band = "test_band"
    product_layer.always_fetch_bands = ["red", "green", "blue"]
    product_layer.band_idx = BandIndex.__new__(BandIndex)
    product_layer.band_idx.band_cfg = {
        "red": [ "crimson", "foo", ],
        "green": [ ],
        "blue": [ "azure" ],
        "fake": []
    }
    product_layer.band_idx._idx = {
        "red": "red",
        "crimson": "red",
        "foo": "red",
        "green": "green",
        "blue": "blue",
        "azure": "red",
        "fake": "fake",
    }
    return product_layer


@pytest.fixture
def style_cfg_lin():
    cfg = {
        "name": "test_style",
        "title": "Test Style",
        "abstract": "This is a Test Style for Datacube WMS",
        "needed_bands": ["red", "green", "blue"],
        "scale_factor": 1.0,
        "scale_range": [1, 2],
        "components": {
            "red": {"red": 1.0},
            "green": {"green": 1.0},
            "blue": {"blue": 1.0}
        }
    }
    return cfg

@pytest.fixture
def style_cfg_map():
    cfg = {
        "name": "test_style",
        "title": "Test Style",
        "abstract": "This is a Test Style for Datacube WMS",
        "needed_bands": ["foo"],
        "value_map": {
            "foo": [
                {
                    "title": "Invalid",
                    "abstract": "An Invalid Value",
                    "flags": {
                        "bar": True,
                        "baz": False
                    },
                    "color": "#000000"
                },
                {
                    "title": "Valid",
                    "abstract": "A Valid Value",
                    "flags": {
                        "or": {
                            "x": True,
                            "y": True
                        }
                    },
                    "color": "#FFFFFF"
                }
            ]
        }
    }
    return cfg

@pytest.fixture
def product_layer_alpha_map():
    product_layer = OWSProductLayer.__new__(OWSProductLayer)
    product_layer.name = "test_product"
    product_layer.pq_band = "test_band"
    product_layer.always_fetch_bands = ["foo"]
    product_layer.band_idx = BandIndex.__new__(BandIndex)
    product_layer.band_idx.band_cfg = {
        "foo": ["foo"]
    }
    product_layer.band_idx._idx = {
        "foo": "foo"
    }
    return product_layer

@pytest.fixture
def style_cfg_map_alpha_1():
    cfg = {
        "name": "test_style",
        "title": "Test Style",
        "abstract": "This is a Test Style for Datacube WMS",
        "needed_bands": ["foo"],
        "value_map": {
            "foo": [
                {
                    "title": "Transparent",
                    "abstract": "A Transparent Value",
                    "flags": {
                        "bar": True,
                    },
                    "color": "#000000",
                    "alpha": 0.0
                }
            ]
        }
    }
    return cfg

@pytest.fixture
def style_cfg_map_alpha_2():
    cfg = {
        "name": "test_style",
        "title": "Test Style",
        "abstract": "This is a Test Style for Datacube WMS",
        "needed_bands": ["foo"],
        "value_map": {
            "foo": [
                {
                    "title": "Semi-Transparent",
                    "abstract": "A Semi-Transparent Value",
                    "flags": {
                        "bar": False,
                    },
                    "color": "#000000",
                    "alpha": 0.5
                }
            ]
        }
    }
    return cfg

@pytest.fixture
def style_cfg_map_alpha_3():
    cfg = {
        "name": "test_style",
        "title": "Test Style",
        "abstract": "This is a Test Style for Datacube WMS",
        "needed_bands": ["foo"],
        "value_map": {
            "foo": [
                {
                    "title": "Non-Transparent",
                    "abstract": "A Non-Transparent Value",
                    "flags": {
                        "bar": False,
                    },
                    "color": "#000000",
                }
            ]
        }
    }
    return cfg

@pytest.fixture
def style_cfg_ramp():
    cfg = {
        "name": "test_style",
        "title": "Test Style",
        "abstract": "This is a Test Style for Datacube WMS",
        "needed_bands": ["foo"],
        "index_function": {
            "function": "datacube_ows.band_utils.constant",
            "pass_product_cfg": True,
            "kwargs": {
                "const": "0.1"
            }
        },
        "color_ramp": [
            {"value": 0.0, "color": "#FFFFFF", "alpha": 0.0},
            {"value": 1.0, "color": "#000000", "alpha": 1.0}
        ]
    }
    return cfg

def test_correct_style_hybrid(product_layer, style_cfg_lin):
    style_cfg_lin["component_ratio"] = 1.0
    style_cfg_lin["range"] = [1, 2]
    style_cfg_lin["index_function"] = {
        "function": "datacube_ows.band_utils.constant",
        "pass_product_cfg": True,
        "kwargs": {
            "const": "0.1"
        }
    }
    style_def = StyleDef(product_layer, style_cfg_lin)

    assert isinstance(style_def, bm.HybridStyleDef)

def test_correct_style_linear(product_layer, style_cfg_lin):
    style_def = StyleDef(product_layer, style_cfg_lin)

    assert isinstance(style_def, bm.LinearStyleDef  )

def test_correct_style_map(product_layer, style_cfg_map):
    style_def = StyleDef(product_layer, style_cfg_map)

    assert isinstance(style_def, bm.RGBAMappedStyleDef)

def test_alpha_style_map(
    product_layer_alpha_map,
    style_cfg_map_alpha_1,
    style_cfg_map_alpha_2,
    style_cfg_map_alpha_3):

    def fake_make_mask(data, **kwargs):
        return data


    band = np.array([True, True, True])
    timarray = [np.datetime64(datetime.date.today())]
    times = DataArray(timarray, coords=[timarray], dims=["time"], name="time")
    da = DataArray(band, name='foo')
    dst = Dataset(data_vars={'foo': da})
    ds = concat([dst], times)

    with patch('datacube_ows.band_mapper.make_mask', new_callable=lambda: fake_make_mask) as fmm:
        style_def = StyleDef(product_layer_alpha_map, style_cfg_map_alpha_1)
        
        result = style_def.transform_data(ds, None, None)
        alpha_channel = result["alpha"].values
        assert (alpha_channel == 0).all()

        style_def = StyleDef(product_layer_alpha_map, style_cfg_map_alpha_2)

        result = style_def.transform_data(ds, None, None)
        alpha_channel = result["alpha"].values
        assert (alpha_channel == 127).all()

        style_def = StyleDef(product_layer_alpha_map, style_cfg_map_alpha_3)

        result = style_def.transform_data(ds, None, None)
        alpha_channel = result["alpha"].values
        assert (alpha_channel == 255).all()


def test_correct_style_ramp(product_layer, style_cfg_ramp):
    style_def = StyleDef(product_layer, style_cfg_ramp)

    assert isinstance(style_def, bm.RgbaColorRampDef)

def test_dynamic_range_compression_scale_range(product_layer, style_cfg_lin):
    style_cfg_lin["scale_range"] = [-3000, 3000]

    style_def = StyleDef(product_layer, style_cfg_lin)

    assert style_def.scale_min == -3000
    assert style_def.scale_max == 3000

    band = np.zeros(3)
    band[0] = -3000
    band[1] = 0
    band[2] = 3000

    compressed = style_def.compress_band("red", band)

    assert compressed[0] == 0
    assert compressed[1] == 255 / 2
    assert compressed[2] == 255

def test_dynamic_range_compression_scale_range_clip(product_layer, style_cfg_lin):
    style_cfg_lin["scale_range"] = [-3000, 3000]

    style_def = StyleDef(product_layer, style_cfg_lin)

    assert style_def.scale_min == -3000
    assert style_def.scale_max == 3000

    band = np.zeros(3)
    band[0] = -3001
    band[1] = 0
    band[2] = 3001

    compressed = style_def.compress_band("red", band)

    assert compressed[0] == 0
    assert compressed[1] == 255 / 2
    assert compressed[2] == 255

def test_dynamic_range_compression_scale_factor(product_layer, style_cfg_lin):
    del style_cfg_lin["scale_range"]
    style_cfg_lin["scale_factor"] = 2.5

    style_def = StyleDef(product_layer, style_cfg_lin)

    assert style_def.scale_min == 0.0
    assert style_def.scale_max == 637.5

    band = np.zeros(3)
    band[0] = -3000
    band[1] = 0
    band[2] = 3000

@pytest.fixture
def product_layer_mask_map():
    product_layer = OWSProductLayer.__new__(OWSProductLayer)
    product_layer.name = "test_product"
    product_layer.pq_band = None
    product_layer.always_fetch_bands = ["foo"]
    product_layer.band_idx = BandIndex.__new__(BandIndex)
    product_layer.band_idx.band_cfg = {
        "foo": ["foo"]
    }
    product_layer.band_idx._idx = {
        "foo": "foo"
    }
    return product_layer

@pytest.fixture
def style_cfg_map_mask():
    cfg = {
        "name": "test_style",
        "title": "Test Style",
        "abstract": "This is a Test Style for Datacube WMS",
        "needed_bands": ["foo"],
        "value_map": {
            "foo": [
                {
                    "title": "Non-Transparent",
                    "abstract": "A Non-Transparent Value",
                    "flags": {
                        "bar": 1,
                    },
                    "color": "#111111",
                    "mask": True
                },
                {
                    "title": "Non-Transparent",
                    "abstract": "A Non-Transparent Value",
                    "flags": {
                        "bar": 2,
                    },
                    "color": "#FFFFFF",
                },
                {
                    "title": "Non-Transparent",
                    "abstract": "A Non-Transparent Value",
                    "flags": {
                        "bar": 1,
                    },
                    "color": "#111111",
                }
            ]
        }
    }
    return cfg

def test_RBGAMapped_Masking(product_layer_mask_map, style_cfg_map_mask):
    def fake_make_mask(data, **kwargs):
        val = kwargs["bar"]
        return data == val


    band = np.array([0, 0, 1, 1, 2, 2])
    timarray = [np.datetime64(datetime.date.today())]
    times = DataArray(timarray, coords=[timarray], dims=["time"], name="time")
    da = DataArray(band, name='foo')
    dst = Dataset(data_vars={'foo': da})
    ds = concat([dst], times)

    with patch('datacube_ows.band_mapper.make_mask', new_callable=lambda: fake_make_mask) as fmm:
        style_def = StyleDef(product_layer_mask_map, style_cfg_map_mask)
        data = style_def.transform_data(ds, None, None)
        r = data["red"]
        g = data["green"]
        b = data["blue"]
        a = data["alpha"]

        assert (r[2:3:1] == 0)
        assert (g[2:3:1] == 0)
        assert (b[2:3:1] == 0)
        assert (a[2:3:1] == 0)
        assert (r[4:5:1] == 255)
        assert (g[4:5:1] == 255)
        assert (b[4:5:1] == 255)
        assert (a[4:5:1] == 255)


def test_reint():
    from datacube_ows.band_mapper import RGBAMappedStyleDef

    band = np.array([0., 0., 1., 1., 2., 2.])
    da = DataArray(band, name='foo')

    assert (band.dtype.kind == "f")
    data = RGBAMappedStyleDef.reint(band)
    assert (data.dtype.kind == "i")

    assert (da.dtype.kind == "f")
    data = RGBAMappedStyleDef.reint(da)
    assert (data.dtype.kind == "i")

    data = RGBAMappedStyleDef.reint(data)
    assert (data.dtype.kind == "i")

def test_createcolordata():
    from datacube_ows.band_mapper import RGBAMappedStyleDef
    from colour import Color

    band = np.array([0, 0, 1, 1, 2, 2])
    da = DataArray(band, name='foo')
    rgb = Color("#FFFFFF")

    data = RGBAMappedStyleDef.create_colordata(da, rgb, 1.0, (band >= 0))
    assert (data == 1.0).all()

def test_createcolordata_alpha():
    from datacube_ows.band_mapper import RGBAMappedStyleDef
    from colour import Color

    band = np.array([0, 0, 1, 1, 2, 2])
    da = DataArray(band, name='foo')
    rgb = Color("#FFFFFF")

    data = RGBAMappedStyleDef.create_colordata(da, rgb, 0.0, (band >= 0))
    assert (data["alpha"] == 0).all()

def test_createcolordata_mask():
    from datacube_ows.band_mapper import RGBAMappedStyleDef
    from colour import Color

    band = np.array([0, 0, 1, 1, 2, 2])
    da = DataArray(band, name='foo')
    rgb = Color("#FFFFFF")

    data = RGBAMappedStyleDef.create_colordata(da, rgb, 0.0, (band > 0))
    assert (np.isnan(data["red"][0:1:1])).all()
    assert (np.isfinite(data["red"][2:5:1])).all()

def test_createcolordata_remask():
    from datacube_ows.band_mapper import RGBAMappedStyleDef
    from colour import Color

    band = np.array([0, 0, 1, 1, np.nan, np.nan])
    da = DataArray(band, name='foo')
    rgb = Color("#FFFFFF")

    data = RGBAMappedStyleDef.create_colordata(da, rgb, 0.0, np.array([True, True, True, True, True, True]))
    assert (np.isfinite(data["red"][0:3:1])).all()
    assert (np.isnan(data["red"][4:5:1])).all()
    
    



