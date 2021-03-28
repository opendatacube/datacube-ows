import pytest

import xarray as xr

from datacube_ows.styles.api import StandaloneStyle, apply_ows_style, apply_ows_style_cfg, generate_ows_legend_style, generate_ows_legend_style_cfg, xarray_image_as_png, create_geobox
from tests.utils import dim1_da


def test_indirect_imports():
    assert xarray_image_as_png is not None
    assert create_geobox is not None


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

@pytest.fixture
def simple_rgb_perband_scaling_style_cfg():
    return {
        "name": "test_style",
        "title": "Test Style",
        "abstract": "This is a Test Style for Datacube WMS",
        "needed_bands": ["red", "green", "blue"],
        "components": {
            "red": {"red": 1.0, "scale_range": [0,200]},
            "green": {"green": 1.0, "scale_range": [0,500]},
            "blue": {"blue": 1.0}
        },
        "scale_range": [0,350]
    }


def test_component_style(dummy_raw_data, null_mask, simple_rgb_style_cfg):
    style = StandaloneStyle(simple_rgb_style_cfg)
    mask = style.to_mask(dummy_raw_data, null_mask)
    result = style.transform_data(dummy_raw_data, mask)
    for channel in ("red", "green", "blue"):
        assert channel in result.data_vars.keys()
    assert result["red"].values[0][0] == 5
    assert result["green"].values[0][0] == 7
    assert result["blue"].values[0][0] == 2


def test_perband_component_style(dummy_raw_data, null_mask, simple_rgb_perband_scaling_style_cfg):
    style = StandaloneStyle(simple_rgb_perband_scaling_style_cfg)
    mask = style.to_mask(dummy_raw_data, null_mask)
    result = style.transform_data(dummy_raw_data, mask)
    for channel in ("red", "green", "blue"):
        assert channel in result.data_vars.keys()


@pytest.fixture
def simple_ramp_style_cfg():
    return {
        "name": "test_style",
        "title": "Test Style",
        "abstract": "This is a Test Style for Datacube WMS",
        "index_function": {
            "function": "datacube_ows.band_utils.norm_diff",
            "mapped_bands": True,
            "kwargs": {
                "band1": "ir",
                "band2": "red"
            }
        },
        "needed_bands": ["red", "ir"],
        "color_ramp": [
            {
                "value": -0.00000001,
                "color": "#000000",
                "alpha": 0.0
            },
            {
                "value": 0.0,
                "color": "#000000",
                "alpha": 1.0
            },
            {"value": 0.2, "color": "#FF00FF"},
            {"value": 0.4, "color": "#00FF00"},
            {"value": 0.5, "color": "#FFFF00"},
            {"value": 0.6, "color": "#0000FF"},
            {"value": 0.8, "color": "#00FFFF"},
            {"value": 1.0, "color": "#FFFFFF"}
        ],
    }

@pytest.fixture
def dummy_raw_calc_data():
    dim_coords = [ -2.0, -1.0, 0.0, -1.0, -2.0, -3.0]
    output = xr.Dataset({
        "ir": dim1_da("ir", [800, 100, 1000, 600, 200, 1000], dim_coords),
        "red": dim1_da("red", [200, 500, 0, 200, 200, 700], dim_coords),
        "green": dim1_da("green", [100, 500, 0, 400, 300, 200], dim_coords),
        "blue": dim1_da("blue", [200, 500, 1000, 600, 100, 700], dim_coords),
        "uv": dim1_da("uv", [400, 600, 900, 200, 400, 100], dim_coords),
        "pq": dim1_da("pq", [0b000, 0b001, 0b010, 0b011, 0b100, 0b111], dim_coords,
                      attrs={
                                "flags_definition": {
                                    "splodgy": {
                                        "bits": 2,
                                        "values": {
                                            '0': "Splodgeless",
                                            '1': "Splodgy",
                                        },
                                        "description": "All splodgy looking"
                                    },
                                    "ugly": {
                                        "bits": 1,
                                        "values": {
                                            '0': False,
                                            '1': True
                                        },
                                        "description": "Real, real ugly",
                                    },
                                    "impossible": {
                                        "bits": 0,
                                        "values": {
                                            '0': False,
                                            '1': "Woah!"
                                        },
                                        "description": "Won't happen. Can't happen. Might happen.",
                                    },
                                }
                            })
    })
    return output

def dim1_null_mask(coords):
    return dim1_da("mask", [True] * len(coords), coords)

@pytest.fixture
def raw_calc_null_mask():
    dim_coords = [ -2.0, -1.0, 0.0, -1.0, -2.0, -3.0]
    return dim1_da("mask", [True] * len(dim_coords), dim_coords)

def test_ramp_style(dummy_raw_calc_data, raw_calc_null_mask, simple_ramp_style_cfg):
    style = StandaloneStyle(simple_ramp_style_cfg)
    result = apply_ows_style(style, dummy_raw_calc_data, valid_data_mask=raw_calc_null_mask)
    for channel in ("red", "green", "blue", "alpha"):
        assert channel in result.data_vars.keys()
    # point 0 800, 200 (idx=0.6)maps to blue
    assert result["alpha"].values[0] == 255
    assert result["red"].values[0] == 0
    assert result["green"].values[0] == 0
    assert result["blue"].values[0] == 255
    # point 1 100, 500 (idx<0)maps to transparent
    assert result["alpha"].values[1] == 0
    # point 2 1000,0 (idx=1.0) maps to white
    assert result["alpha"].values[2] == 255
    assert result["red"].values[2] == 255
    assert result["green"].values[2] == 255
    assert result["blue"].values[2] == 255
    # point 3 600,200 (idx=0.5) maps to yellow
    assert result["alpha"].values[3] == 255
    assert result["red"].values[3] == 255
    assert result["green"].values[3] >= 254 # Why isn't it 255?
    assert result["blue"].values[3] == 0
    # point 4 200,200 (idx=0.0) maps to black
    assert result["alpha"].values[4] == 255
    assert result["red"].values[4] == 0
    assert result["green"].values[4] == 0
    assert result["blue"].values[4] == 0
    # point 5 1000,700 (idx=0.176) maps to between black and magenta
    assert result["alpha"].values[5] == 255
    assert result["green"].values[5] == 0
    assert abs(result["red"].values[5] - result["blue"].values[5]) <=1 # Why not exactly equal?
    assert result["red"].values[5] > 0
    assert result["red"].values[5] < 255


def test_ramp_legend(simple_ramp_style_cfg):
    style = StandaloneStyle(simple_ramp_style_cfg)
    img = generate_ows_legend_style(style, 1)
    assert img.mode == "RGBA"
    assert img.size == (400, 125)


@pytest.fixture
def rgb_style_with_masking_cfg():
    return {
        "name": "test_style",
        "title": "Test Style",
        "abstract": "This is a Test Style for Datacube WMS",
        "needed_bands": ["red", "green", "blue"],
        "scale_range": (0.0, 1000.0),
        "components": {
            "red": {"red": 1.0},
            "green": {"green": 1.0},
            "blue": {"blue": 1.0}
        },
        "pq_masks": [
            {
                "band": "pq",
                "flags": {
                    'splodgy': "Splodgeless",
                },
            },
            {
                "band": "pq",
                "flags": {
                    "ugly": True,
                    "impossible": "Woah!"
                },
                "invert": True
            },
        ]
    }

def test_component_style_with_masking(dummy_raw_calc_data, raw_calc_null_mask, rgb_style_with_masking_cfg):
    result = apply_ows_style_cfg(rgb_style_with_masking_cfg, dummy_raw_calc_data, raw_calc_null_mask)
    for channel in ("red", "green", "blue", "alpha"):
        assert channel in result.data_vars.keys()
    alphas = result["alpha"].values
    assert alphas[0] == 255
    assert alphas[1] == 255
    assert alphas[2] == 255
    assert alphas[3] == 0
    assert alphas[4] == 0
    assert alphas[5] == 0


@pytest.fixture
def dummy_col_map_data():
    dim_coords = [ -2.0, -1.0, 0.0, -1.0, -2.0, -3.0]
    output = xr.Dataset({
        "pq": dim1_da("pq", [0b01000, 0b11001, 0b01010, 0b10011, 0b00100, 0b10111], dim_coords,
                      attrs={
                          "flags_definition": {
                              "joviality": {
                                  "bits": 3,
                                  "values": {
                                      '0': "Melancholic",
                                      '1': "Joyous",
                                  },
                                  "description": "All splodgy looking"
                              },
                              "flavour": {
                                  "bits": 3,
                                  "values": {
                                      '0': "Bland",
                                      '1': "Tasty",
                                  },
                                  "description": "All splodgy looking"
                              },
                              "splodgy": {
                                  "bits": 2,
                                  "values": {
                                      '0': "Splodgeless",
                                      '1': "Splodgy",
                                  },
                                  "description": "All splodgy looking"
                              },
                              "ugly": {
                                  "bits": 1,
                                  "values": {
                                      '0': False,
                                      '1': True
                                  },
                                  "description": "Real, real ugly",
                              },
                              "impossible": {
                                  "bits": 0,
                                  "values": {
                                      '0': False,
                                      '1': "Woah!"
                                  },
                                  "description": "Won't happen. Can't happen. Might happen.",
                              },
                          }
                      })
    })
    return output


@pytest.fixture
def simple_colormap_style_cfg():
    return {
        "name": "test_style",
        "title": "Test Style",
        "abstract": "This is a Test Style for Datacube WMS",
        "value_map": {
            "pq": [
                {
                    "title": "Impossibly Tasty",
                    "abstract": "Tasty AND Impossible",
                    "flags": {
                        "and": {
                            "flavour": "Tasty",
                            "impossible": "Woah!"
                        },
                    },
                    "color": "#FF0000"
                },
                {
                    "title": "Possibly Tasty",
                    "abstract": "Tasty and Possible",
                    "flags": {
                        "impossible": "Woah!"
                    },
                    "color": "#00FF00"
                },
                {
                    "title": "Ugly/Splodgy",
                    "abstract": "Ugly or splodgy",
                    "flags": {
                        "or": {
                            "ugly": True,
                            "splodgy": "Splodgy"
                        }
                    },
                    "color": "#0000FF"
                },
            ]
        }
    }

def test_colormap_style(dummy_col_map_data, raw_calc_null_mask, simple_colormap_style_cfg):
    result = apply_ows_style_cfg(simple_colormap_style_cfg, dummy_col_map_data, raw_calc_null_mask)
    for channel in ("red", "green", "blue", "alpha"):
        assert channel in result.data_vars.keys()
    # point 0 fall through - transparent
    assert result["alpha"].values[0] == 0
    # point 1 tasty & impossible: red
    assert result["alpha"].values[1] == 255
    assert result["red"].values[1] == 255
    assert result["green"].values[1] == 0
    assert result["blue"].values[1] == 0
    # point 2 splodgy or ugly: blue
    assert result["alpha"].values[2] == 255
    assert result["red"].values[2] == 0
    assert result["green"].values[2] == 0
    assert result["blue"].values[2] == 255
    # point 3 bland & impossible: green
    assert result["alpha"].values[3] == 255
    assert result["red"].values[3] == 0
    assert result["green"].values[3] == 255
    assert result["blue"].values[3] == 0
    # point 4 splodgy or ugly: blue
    assert result["alpha"].values[4] == 255
    assert result["red"].values[4] == 0
    assert result["green"].values[4] == 0
    assert result["blue"].values[4] == 255
    # point 5 bland & impossible: green
    assert result["alpha"].values[5] == 255
    assert result["red"].values[5] == 0
    assert result["green"].values[5] == 255
    assert result["blue"].values[5] == 0


@pytest.fixture
def enum_colormap_style_cfg():
    return {
        "name": "test_style",
        "title": "Test Style",
        "abstract": "This is a Test Style for Datacube WMS",
        "value_map": {
            "pq": [
                {
                    "title": "Blah",
                    "values": [8, 25],
                    "color": "#FF0000"
                },
                {
                    "title": "Rock and Roll",
                    "values": [4, 19, 25],
                    "color": "#00FF00"
                },
                {
                    "title": "",
                    "values": [23],
                    "color": "#0000FF"
                },
            ]
        }
    }


def test_enum_colormap_style(dummy_col_map_data, raw_calc_null_mask, enum_colormap_style_cfg):
    result = apply_ows_style_cfg(enum_colormap_style_cfg, dummy_col_map_data, raw_calc_null_mask)
    for channel in ("red", "green", "blue", "alpha"):
        assert channel in result.data_vars.keys()
    # point 0 (8) Blah - red
    assert result["alpha"].values[0] == 255
    assert result["red"].values[1] == 255
    assert result["green"].values[1] == 0
    assert result["blue"].values[1] == 0
    # point 1 (25) Blah - red
    assert result["alpha"].values[1] == 255
    assert result["red"].values[1] == 255
    assert result["green"].values[1] == 0
    assert result["blue"].values[1] == 0
    # point 2 (10) - fall through, transparent
    assert result["alpha"].values[2] == 0
    # point 3 (19) - rnr green
    assert result["alpha"].values[3] == 255
    assert result["red"].values[3] == 0
    assert result["green"].values[3] == 255
    assert result["blue"].values[3] == 0
    # point 4 (4): rnr green
    assert result["alpha"].values[4] == 255
    assert result["red"].values[4] == 0
    assert result["green"].values[4] == 255
    assert result["blue"].values[4] == 0
    # point 5 (23): blue
    assert result["alpha"].values[5] == 255
    assert result["red"].values[5] == 0
    assert result["green"].values[5] == 0
    assert result["blue"].values[5] == 255


def test_ramp_legend(simple_colormap_style_cfg):
    img = generate_ows_legend_style_cfg(simple_colormap_style_cfg, 1)

    assert img.mode == "RGBA"
    assert img.size == (300, 125)


def test_api_none_mask(dummy_col_map_data, raw_calc_null_mask, simple_colormap_style_cfg):
    null_mask = apply_ows_style_cfg(simple_colormap_style_cfg, dummy_col_map_data, raw_calc_null_mask)
    none_mask = apply_ows_style_cfg(simple_colormap_style_cfg, dummy_col_map_data)
    for i in range(6):
        for c in ("red", "green", "blue", "alpha"):
            assert null_mask[c].values[i] == none_mask[c].values[i]

