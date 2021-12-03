# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import datetime
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from xarray import DataArray, Dataset, concat

import datacube_ows.styles
from datacube_ows.config_utils import OWSEntryNotFound
from datacube_ows.ogc_utils import ConfigException
from datacube_ows.ows_configuration import BandIndex, OWSProductLayer


@pytest.fixture
def product_layer():
    class FakeODCProduct:
        def __init__(self, name):
            self.name = name
            self.id = 7

        def __str__(self):
            return self.name

        def __repr__(self):
            return f"FakeODCProduct({self.name})"

    class FakeProductBand:
        bands = set(["pq", "wongle"])
        products = [FakeODCProduct("test_masking_product")]
        manual_merge = False
        ignore_time = False
        fuse_func = None

        def products_match(self, name):
            return False
    product_layer = OWSProductLayer.__new__(OWSProductLayer)
    product_layer._unready_attributes = []
    product_layer.global_cfg = MagicMock()
    product_layer.name = "test_product"
    product_layer.object_label = "layer.test_product"
    product_layer.pq_band = "test_band"
    product_layer.product_names = ["test_odc_product"]
    product_layer.products = [FakeODCProduct('test_odc_product')]
    product_layer.low_res_product_names = ["test_odc_summary_product"]
    product_layer.low_res_products = [FakeODCProduct('test_odc_summary_product')]
    product_layer.always_fetch_bands = ["red", "green", "blue"]
    product_layer.band_idx = BandIndex.__new__(BandIndex)
    product_layer.band_idx._unready_attributes = []
    product_layer.band_idx.product = product_layer
    product_layer.band_idx.band_cfg = {
        "red": ["crimson", "foo", ],
        "green": [],
        "blue": ["azure", "bar"],
        "fake": []
    }
    product_layer.band_idx._idx = {
        "red": "red",
        "crimson": "red",
        "foo": "red",
        "bar": "blue",
        "green": "green",
        "blue": "blue",
        "azure": "red",
        "fake": "fake",
    }
    product_layer.global_cfg.product_index = {
        "test_product": product_layer
    }
    product_layer.data_manual_merge = False
    product_layer.fuse_func = None
    product_layer.allflag_productbands = [FakeProductBand()]
    product_layer.style_index = {}
    product_layer.band_idx._metadata_registry = {
        "layer.test_product.bands.red": "crimson",
        "layer.test_product.bands.green": "green",
        "layer.test_product.bands.blue": "azure",
        "layer.test_product.bands.fake": "fake",
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
        "components": {
            "red": {"red": 1.0},
            "green": {"green": 1.0},
            "blue": {"blue": 1.0}
        }
    }
    return cfg


@pytest.fixture
def style_cfg_lin_clone():
    cfg = {
        "inherits": {
            "style": "test_style",
        },
        "name": "test_style_2",
        "title": "Test Style 2",
        "scale_factor": None,
        "scale_range": [0, 12000],
    }
    return cfg


@pytest.fixture
def style_cfg_nonlin():
    cfg = {
        "name": "test_style",
        "title": "Test Style",
        "abstract": "This is a Test Style for Datacube WMS",
        "needed_bands": ["red", "green", "blue"],
        "scale_factor": 1.0,
        "components": {
            "red": {"red": 1.0},
            "green": {
                "function": "datacube_ows.band_utils.norm_diff",
                "kwargs": {
                    "band1": "red",
                    "band2": "green",
                }
            },
            "blue": {"blue": 1.0}
        },
        "additional_bands": [],
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
    product_layer.global_cfg = None
    product_layer.name = "test_product"
    product_layer.pq_band = "test_band"
    product_layer.product_names = ["test_odc_product"]
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


def test_valuemap_ctor():
    style = MagicMock()
    style.name = "style_name"
    style.product.name = "layer_name"

    vm = datacube_ows.styles.colormap.ValueMapRule(style, "band3", {
        "title": "",
        "abstract": "Abstract abstractions",
        "values": [1, 2],
        "color": "#FFFFFF"
    })
    assert vm.label == "Abstract abstractions"
    with pytest.raises(ConfigException) as e:
        vm = datacube_ows.styles.colormap.ValueMapRule(style, "band3", {
            "title": "",
            "abstract": "Abstract abstractions",
            "flags": {
                "and": {
                    "flag": "val",
                },
                "or": {
                    "other_flag": "other_val"
                }
            },
            "color": "#FFFFFF"
        })
    assert "combines 'and' and 'or' rules" in str(e.value)
    assert "style_name" in str(e.value)
    assert "layer_name" in str(e.value)
    with pytest.raises(ConfigException) as e:
        vm = datacube_ows.styles.colormap.ValueMapRule(style, "band3", {
            "title": "",
            "abstract": "Abstract abstractions",
            "flags": {
                "and": {
                    "flag": "val",
                },
            },
            "values": [1, 2, 3],
            "color": "#FFFFFF"
        })
    assert "has both a 'flags' and a 'values' section - choose one" in str(e.value)
    assert "style_name" in str(e.value)
    assert "layer_name" in str(e.value)
    with pytest.raises(ConfigException) as e:
        vm = datacube_ows.styles.colormap.ValueMapRule(style, "band3", {
            "title": "",
            "abstract": "Abstract abstractions",
            "color": "#FFFFFF"
        })
    assert "must have a non-empty 'flags' or 'values' section" in str(e.value)
    assert "style_name" in str(e.value)
    assert "layer_name" in str(e.value)


@pytest.fixture
def style_cfg_ramp():
    cfg = {
        "name": "test_style",
        "title": "Test Style",
        "abstract": "This is a Test Style for Datacube WMS",
        "needed_bands": ["foo"],
        "index_function": {
            "function": "datacube_ows.band_utils.single_band",
            "mapped_bands": False,
            "kwargs": {
                "band": "foo"
            }
        },
        "color_ramp": [
            {"value": 0.0, "color": "#FFFFFF", "alpha": 0.0},
            {"value": 1.0, "color": "#000000", "alpha": 1.0}
        ]
    }
    return cfg


@pytest.fixture
def style_cfg_ramp_clone(style_cfg_ramp):
    cfg = {
        "inherits": style_cfg_ramp,
        "name": "test_style2",
        "title": "Test Style 2",
        "needed_bands": ["bar"],
    }
    return cfg


@pytest.fixture
def style_cfg_ramp_mapped():
    cfg = {
        "name": "test_style",
        "title": "Test Style",
        "abstract": "This is a Test Style for Datacube WMS",
        "needed_bands": ["foo"],
        "index_function": {
            "function": "datacube_ows.band_utils.single_band",
            "mapped_bands": True,
            "kwargs": {
                "band": "bar"
            }
        },
        "band_map": {"bar": "foo"},
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
        "mapped_bands": True,
        "kwargs": {
            "const": "0.1"
        }
    }
    style_def = datacube_ows.styles.StyleDef(product_layer, style_cfg_lin)

    assert isinstance(style_def, datacube_ows.styles.hybrid.HybridStyleDef)


def test_correct_style_nonlin_hybrid(product_layer, style_cfg_nonlin):
    style_cfg_nonlin["component_ratio"] = 1.0
    style_cfg_nonlin["range"] = [1, 2]
    style_cfg_nonlin["index_function"] = {
        "function": "datacube_ows.band_utils.constant",
        "mapped_bands": True,
        "kwargs": {
            "const": "0.1"
        }
    }
    style_def = datacube_ows.styles.StyleDef(product_layer, style_cfg_nonlin)
    assert isinstance(style_def, datacube_ows.styles.hybrid.HybridStyleDef)


def test_invalid_component_ratio(product_layer, style_cfg_nonlin):
    style_cfg_nonlin["component_ratio"] = 2.0
    style_cfg_nonlin["range"] = [1, 2]
    style_cfg_nonlin["index_function"] = {
        "function": "datacube_ows.band_utils.constant",
        "mapped_bands": True,
        "kwargs": {
            "const": "0.1"
        }
    }
    with pytest.raises(ConfigException) as e:
        style_def = datacube_ows.styles.StyleDef(product_layer, style_cfg_nonlin)
    assert "Component ratio must be a floating point number between 0 and 1" in str(e.value)


def test_correct_style_linear(product_layer, style_cfg_lin, style_cfg_lin_clone):
    style_def = datacube_ows.styles.StyleDef(product_layer, style_cfg_lin)
    product_layer.style_index[style_def.name] = style_def
    assert isinstance(style_def, datacube_ows.styles.component.ComponentStyleDef)


def test_unresolvable_style(product_layer):
    with pytest.raises(ConfigException) as e:
        style_def = datacube_ows.styles.StyleDef(product_layer, {
            "foo": "This is not real",
            "name": "gotaname",
            "abstract": "gotabstract",
            "splunge": "doodly-doo"
        })
    assert "could not determine style type" in str(e.value)


def test_style_inheritance(product_layer, style_cfg_lin, style_cfg_lin_clone):
    style_def = datacube_ows.styles.StyleDef(product_layer, style_cfg_lin)
    product_layer.style_index[style_def.name] = style_def
    style_def_clone = datacube_ows.styles.StyleDef(product_layer, style_cfg_lin_clone)
    assert isinstance(style_def_clone, datacube_ows.styles.component.ComponentStyleDef)
    assert isinstance(style_def, datacube_ows.styles.component.ComponentStyleDef)


def test_inherit_exceptions(product_layer, style_cfg_lin, style_cfg_lin_clone):
    style_def = datacube_ows.styles.StyleDef(product_layer, style_cfg_lin)
    product_layer.style_index[style_def.name] = style_def
    style_cfg_lin_clone["inherits"]["layer"] = "fake_layer"
    try:
        style_def_clone = datacube_ows.styles.StyleDef(product_layer, style_cfg_lin_clone)
        assert "Expected exception not thrown" == False
    except OWSEntryNotFound:
        pass
    try:
        style = datacube_ows.styles.StyleDef.lookup_impl(product_layer.global_cfg,
                                                         keyvals={
                                                             "style": "test_style",
                                                             "layer": "fake-layer"
                                                         })
        assert style == "Expected exception not thrown"
    except OWSEntryNotFound:
        pass
    try:
        style = datacube_ows.styles.StyleDef.lookup_impl(product_layer.global_cfg,
                                                 keyvals={
                                                     "style": "fake_style",
                                                     "layer": "test_product"
                                                 },
                                                subs={"layer": {"test_product": product_layer}})
        assert style == "Expected exception not thrown"
    except OWSEntryNotFound:
        pass


def test_style_exceptions(product_layer, style_cfg_map: dict):
    style_no_name = dict(style_cfg_map)
    style_no_name.pop('name', None)
    with pytest.raises(KeyError) as excinfo:
        style_def = datacube_ows.styles.StyleDef(product_layer, style_no_name)


def test_correct_style_map(product_layer, style_cfg_map):
    style_def = datacube_ows.styles.StyleDef(product_layer, style_cfg_map)

    assert isinstance(style_def, datacube_ows.styles.colormap.ColorMapStyleDef)


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
    da = DataArray(band, name='foo',
                         attrs = {
                            "flags_definition": {
                                "foo": {"bits": 0},
                                "floop": {"bits": 1},
                         }
    })
    dst = Dataset(data_vars={'foo': da})
    ds = concat([dst], times)
    npmap = np.array([True, True, True])
    damap = DataArray(npmap)

    with patch('datacube_ows.config_utils.make_mask', new_callable=lambda: fake_make_mask) as fmm:
        style_def = datacube_ows.styles.StyleDef(product_layer_alpha_map, style_cfg_map_alpha_1)
        
        result = style_def.transform_data(ds, damap)
        alpha_channel = result["alpha"].values
        assert (alpha_channel == 0).all()

        style_def = datacube_ows.styles.StyleDef(product_layer_alpha_map, style_cfg_map_alpha_2)

        result = style_def.transform_data(ds, None)
        alpha_channel = result["alpha"].values
        assert (alpha_channel == 128).all()

        style_def = datacube_ows.styles.StyleDef(product_layer_alpha_map, style_cfg_map_alpha_3)

        result = style_def.transform_data(ds, damap)
        alpha_channel = result["alpha"].values
        assert (alpha_channel == 255).all()


def test_correct_style_ramp(product_layer, style_cfg_ramp):
    style_def = datacube_ows.styles.StyleDef(product_layer, style_cfg_ramp)

    assert isinstance(style_def, datacube_ows.styles.ramp.ColorRampDef)


def test_inherited_style_ramp(product_layer, style_cfg_ramp_clone):
    style_def = datacube_ows.styles.StyleDef(product_layer, style_cfg_ramp_clone)

    assert isinstance(style_def, datacube_ows.styles.ramp.ColorRampDef)


def test_bandmapped_style_ramp(product_layer, style_cfg_ramp_mapped):
    style_def = datacube_ows.styles.StyleDef(product_layer, style_cfg_ramp_mapped)

    assert isinstance(style_def, datacube_ows.styles.ramp.ColorRampDef)
    assert style_def.local_band("bar") == "red"


def test_dynamic_range_compression_scale_range(product_layer, style_cfg_lin):
    style_cfg_lin["scale_range"] = [-3000, 3000]

    style_def = datacube_ows.styles.StyleDef(product_layer, style_cfg_lin)

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

    style_def = datacube_ows.styles.StyleDef(product_layer, style_cfg_lin)

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
    style_cfg_lin["scale_factor"] = 2.5

    style_def = datacube_ows.styles.StyleDef(product_layer, style_cfg_lin)

    assert style_def.scale_min == 0.0
    assert style_def.scale_max == 637.5

    band = np.zeros(3)
    band[0] = -3000
    band[1] = 0
    band[2] = 3000


@pytest.fixture
def product_layer_mask_map():
    product_layer = OWSProductLayer.__new__(OWSProductLayer)
    product_layer.global_cfg = None
    product_layer.name = "test_product"
    product_layer.pq_band = None
    product_layer.product_names = ["test_odc_product"]
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
                    "title": "Transparent",
                    "abstract": "A Transparent Value",
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
                    "title": "Impossible",
                    "abstract": "Will already have matched a previous rule",
                    "flags": {
                        "bar": 1,
                    },
                    "color": "#54d56f",
                }
            ]
        }
    }
    return cfg


def test_RGBAMapped_Masking(product_layer_mask_map, style_cfg_map_mask):
    def fake_make_mask(data, **kwargs):
        val = kwargs["bar"]
        return data == val


    dim = np.array([0, 1, 2, 3, 4, 5])
    band = np.array([0, 0, 1, 1, 2, 2])
    timarray = [np.datetime64(datetime.date.today())]
    times = DataArray(timarray, coords=[timarray], dims=["time"], name="time")
    da = DataArray(band, name='foo', coords={"dim": dim}, dims=["dim"])
    dst = Dataset(data_vars={'foo': da})
    ds = concat([dst], times)

    npmap = np.array([True, True, True, True, True, True])
    damap = DataArray(npmap, coords={"dim": dim}, dims=["dim"])

    with patch('datacube_ows.config_utils.make_mask', new_callable=lambda: fake_make_mask) as fmm:
        style_def = datacube_ows.styles.StyleDef(product_layer_mask_map, style_cfg_map_mask)
        data = style_def.transform_data(ds, damap)
        r = data["red"]
        g = data["green"]
        b = data["blue"]
        a = data["alpha"]

        assert (r.values[2] == 17)
        assert (g.values[2] == 17)
        assert (b.values[2] == 17)
        assert (a.values[2] == 0)
        assert (r.values[4] == 255)
        assert (g.values[4] == 255)
        assert (b.values[4] == 255)
        assert (a.values[4] == 255)


def test_reint():
    from datacube_ows.styles.colormap import ColorMapStyleDef

    band = np.array([0., 0., 1., 1., 2., 2.])
    da = DataArray(band, name='foo')

    assert (band.dtype.kind == "f")
    data = ColorMapStyleDef.reint(band)
    assert (data.dtype.kind == "i")

    assert (da.dtype.kind == "f")
    data = ColorMapStyleDef.reint(da)
    assert (data.dtype.kind == "i")

    data = ColorMapStyleDef.reint(data)
    assert (data.dtype.kind == "i")


def test_createcolordata():
    from colour import Color

    from datacube_ows.styles.colormap import ColorMapStyleDef

    band = np.array([0, 0, 1, 1, 2, 2])
    da = DataArray(band, name='foo')
    rgb = Color("#FFFFFF")

    data = ColorMapStyleDef.create_colordata(da, rgb, 1.0, (band >= 0))
    assert (data == 1.0).all()


def test_createcolordata_alpha():
    from colour import Color

    from datacube_ows.styles.colormap import ColorMapStyleDef

    band = np.array([0, 0, 1, 1, 2, 2])
    da = DataArray(band, name='foo')
    rgb = Color("#FFFFFF")

    data = ColorMapStyleDef.create_colordata(da, rgb, 0.0, (band >= 0))
    assert (data["alpha"] == 0).all()


def test_createcolordata_mask():
    from colour import Color

    from datacube_ows.styles.colormap import ColorMapStyleDef

    band = np.array([0, 0, 1, 1, 2, 2])
    da = DataArray(band, name='foo')
    rgb = Color("#FFFFFF")

    data = ColorMapStyleDef.create_colordata(da, rgb, 0.0, (band > 0))
    assert (np.isnan(data["red"][0:1:1])).all()
    assert (np.isfinite(data["red"][2:5:1])).all()


def test_createcolordata_remask():
    from colour import Color

    from datacube_ows.styles.colormap import ColorMapStyleDef

    band = np.array([0, 0, 1, 1, np.nan, np.nan])
    da = DataArray(band, name='foo')
    rgb = Color("#FFFFFF")

    data = ColorMapStyleDef.create_colordata(da, rgb, 0.0, np.array([True, True, True, True, True, True]))
    assert (np.isfinite(data["red"][0:3:1])).all()
    assert (np.isnan(data["red"][4:5:1])).all()


def test_scale_ramp():
    from datacube_ows.styles.ramp import scale_unscaled_ramp

    input = [
        {"value": 0.0, "color": "red", "alpha": 0.5},
        {"value": 0.5, "color": "green"},
        {"value": 1.0, "color": "blue"},
    ]
    output = scale_unscaled_ramp(-100.0, 100.0, input)
    assert output[0]["color"] == "red"
    assert output[0]["alpha"] == 0.5
    assert output[0]["value"] == -100.0
    assert output[1]["color"] == "green"
    assert output[1]["alpha"] == 1.0
    assert output[1]["value"] == 0.0
    assert output[2]["color"] == "blue"
    assert output[2]["alpha"] == 1.0
    assert output[2]["value"] == 100.0


def test_bad_mpl_ramp():
    from datacube_ows.styles.ramp import read_mpl_ramp

    with pytest.raises(ConfigException) as e:
        ramp = read_mpl_ramp("definitely_not_a_real_matplotlib_ramp_name")
    assert "Invalid Matplotlib name: " in str(e.value)

