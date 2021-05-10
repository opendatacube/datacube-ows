import datetime
from unittest.mock import MagicMock

import numpy as np
import pytest
import xarray
import xarray as xr

from tests.utils import coords, dim1_da, dummy_da


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
        "foo_nativeres": nb,
        "foo_nonativeres": nb,
        "foo_badnativecrs": nb,
        "foo_nativecrs": nb,
        "foo_nonativecrs": nb,
        "foo": nb,
        "bar": nb,
    }
    dc.list_measurements.return_value = lmo

    def product_by_name(s):
        if 'lookupfail' in s:
            return None
        mprod  = MagicMock()
        flag_def = {
            "moo": {"bits": 0},
            "floop": {"bits": 1},
            "blat": {"bits": 2},
            "pow": {"bits": 3},
            "zap": {"bits": 4},
            "dang": {"bits": 5},
        }
        mprod.lookup_measurements.return_value = {
            "band4": {
                "flags_definition": flag_def
            }
        }
        mprod.definition = {"storage": {}}
        if 'nonativecrs' in s:
            pass
        elif 'badnativecrs' in s:
            mprod.definition["storage"]["crs"] = "EPSG:9999"
        elif 'nativecrs' in s:
            mprod.definition["storage"]["crs"] = "EPSG:4326"
        else:
            pass
        if 'nonativeres' in s:
            pass
        elif 'nativeres' in s:
            mprod.definition["storage"]["resolution"] = {
                "latitude": 0.001,
                "longitude": 0.001,
            }
        else:
            pass
        return mprod
    dc.index.products.get_by_name = product_by_name
    return dc


@pytest.fixture
def minimal_global_cfg():
    global_cfg = MagicMock()
    global_cfg.keywords = {"global"}
    global_cfg.attribution.title = "Global Attribution"
    global_cfg.contact_org = None
    global_cfg.contact_position = None
    global_cfg.abstract = "Global Abstract"
    global_cfg.authorities = {
        "auth0": "http://test.url/auth0",
        "auth1": "http://test.url/auth1",
    }
    global_cfg.published_CRSs = {
        "EPSG:3857": {  # Web Mercator
            "geographic": False,
            "horizontal_coord": "x",
            "vertical_coord": "y",
            "vertical_coord_first": False,
            "gml_name": "http://www.opengis.net/def/crs/EPSG/0/3857",
            "alias_of": None,
        },
        "EPSG:4326": {  # WGS-84
            "geographic": True,
            "vertical_coord_first": True,
            "horizontal_coord": "longitude",
            "vertical_coord": "latitude",
            "gml_name": "http://www.opengis.net/def/crs/EPSG/0/4326",
            "alias_of": None,
        },
        "EPSG:3577": {
            "geographic": False,
            "horizontal_coord": "x",
            "vertical_coord": "y",
            "vertical_coord_first": False,
            "gml_name": "http://www.opengis.net/def/crs/EPSG/0/3577",
            "alias_of": None,
        },
        "TEST:CRS": {
            "geographic": False,
            "horizontal_coord": "horrible_zonts",
            "vertical_coord": "vertex_calories",
            "vertical_coord_first": False,
            "gml_name": "TEST/CRS",
            "alias_of": None,
        },
        "TEST:NATIVE_CRS": {
            "geographic": False,
            "horizontal_coord": "hortizonal_cults",
            "vertical_coord": "verbal_tics",
            "vertical_coord_first": False,
            "gml_name": "TEST/NATIVE_CRS",
            "alias_of": None,
        },
    }
    global_cfg.folder_index = {
        "existing_folder": MagicMock(),
    }
    return global_cfg


@pytest.fixture
def minimal_parent():
    parent = MagicMock()
    parent.abstract = "Parent Abstract"
    parent.keywords = {"global", "parent"}
    parent.attribution.title = "Parent Attribution"
    return parent


@pytest.fixture
def minimal_layer_cfg():
    return {
        "title": "The Title",
        "abstract": "The Abstract",
        "name": "a_layer",
        "product_name": "foo",
        "image_processing": {
            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
        },
        "styling": {
            "default_style": "band1",
            "styles": [
                {
                    "name": "band1",
                    "title": "Single Band Test Style",
                    "abstract": "",
                    "components": {
                        "red": {"band1": 1.0},
                        "green": {"band1": 1.0},
                        "blue": {"band1": 1.0},
                    },
                    "scale_range": [0, 1024]
                }
            ]
        }
    }


@pytest.fixture
def minimal_multiprod_cfg():
    return {
        "title": "The Title",
        "abstract": "The Abstract",
        "name": "a_layer",
        "multi_product": True,
        "product_names": ["foo", "bar"],
        "image_processing": {
            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
        },
        "styling": {
            "default_style": "band1",
            "styles": [
                {
                    "name": "band1",
                    "title": "Single Band Test Style",
                    "abstract": "",
                    "components": {
                        "red": {"band1": 1.0},
                        "green": {"band1": 1.0},
                        "blue": {"band1": 1.0},
                    },
                    "scale_range": [0, 1024]
                }
            ]
        }
    }


@pytest.fixture
def mock_range():
    times = [datetime.datetime(2010, 1, 1), datetime.datetime(2010, 1, 2)]
    return {
        "lat": {
            "min": -0.1,
            "max": 0.1,
        },
        "lon": {
            "min": -0.1,
            "max": 0.1,
        },
        "times": times,
        "start_time": times[0],
        "end_time": times[-1],
        "time_set": set(times),
        "bboxes": {
            "EPSG:4326": {"top": 0.1, "bottom": -0.1, "left": -0.1, "right": 0.1, },
            "EPSG:3577": {"top": 0.1, "bottom": -0.1, "left": -0.1, "right": 0.1, },
            "EPSG:3857": {"top": 0.1, "bottom": -0.1, "left": -0.1, "right": 0.1, },
        }
    }


@pytest.fixture
def minimal_global_raw_cfg():
    return {
        "global": {
            "title": "Test Title",
            "info_url": "https://my.domain.com/about_us",
            "allowed_urls": [
                "http://localhost",
                "http://unsecure.domain.com/odc",
                "https://secure.domain.com/ows",
            ],
            "published_CRSs": {
                "EPSG:3857": {  # Web Mercator
                     "geographic": False,
                     "horizontal_coord": "x",
                     "vertical_coord": "y",
                },
                "EPSG:4326": {  # WGS-84
                    "geographic": True,
                    "vertical_coord_first": True
                },
            },
        },
        "layers": []
    }


@pytest.fixture
def wcs_global_cfg():
    return {
        "formats": {
            # Key is the format name, as used in DescribeCoverage XML
            "GeoTIFF": {
                "renderer": "datacube_ows.wcs_utils.get_tiff",
                # The MIME type of the image, as used in the Http Response.
                "mime": "image/geotiff",
                # The file extension to add to the filename.
                "extension": "tif",
                # Whether or not the file format supports multiple time slices.
                "multi-time": False
            },
            "netCDF": {
                "renderer": "datacube_ows.wcs_utils.get_netcdf",
                "mime": "application/x-netcdf",
                "extension": "nc",
                "multi-time": True,
            }
        },
        "native_format": "GeoTIFF",
    }


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
def dummy_raw_calc_data():
    dim_coords = [-2.0, -1.0, 0.0, -1.0, -2.0, -3.0]
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
    dim_coords = [-2.0, -1.0, 0.0, -1.0, -2.0, -3.0]
    return dim1_da("mask", [True] * len(dim_coords), dim_coords)


@pytest.fixture
def dummy_col_map_data():
    dim_coords = [-2.0, -1.0, 0.0, -1.0, -2.0, -3.0]
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
def dummy_raw_ls_data():
    output = xr.Dataset({
        "red": dummy_da(5, "red", coords, dtype=np.int16),
        "green": dummy_da(7, "green", coords, dtype=np.int16),
        "blue": dummy_da(2, "blue", coords, dtype=np.int16),
        "nir": dummy_da(101, "nir", coords, dtype=np.int16),
        "swir1": dummy_da(1051, "swir1", coords, dtype=np.int16),
        "swir2": dummy_da(1051, "swir2", coords, dtype=np.int16),
    })
    return output


@pytest.fixture
def dummy_raw_wo_data():
    output = xr.Dataset({
        "water": dummy_da(0b101,
                        "red",
                        coords,
                        dtype=np.uint8,
                        attrs = {
                                "flags_definition": {
                                    "nodata": {
                                        "bits": 0,
                                        "description": "No data",
                                        "values": {
                                            '0': False,
                                            '1': True
                                        },
                                    },
                                    "noncontiguous": {
                                        "description": "At least one EO band is missing or saturated",
                                        "bits": 1,
                                        "values": {
                                            '0': False,
                                            '1': True
                                        },
                                    },
                                    "low_solar_angle": {
                                        "description": "Low solar incidence angle",
                                        "bits": 2,
                                        "values": {
                                            '0': False,
                                            '1': True
                                        },
                                    },
                                    "terrain_shadow": {
                                        "description": "Terrain shadow",
                                        "bits": 3,
                                        "values": {
                                            '0': False,
                                            '1': True
                                        },
                                    },
                                    "high_slope": {
                                        "description": "High slope",
                                        "bits": 4,
                                        "values": {
                                            '0': False,
                                            '1': True
                                        }
                                    },
                                    "cloud_shadow": {
                                        "description": "Cloud shadow",
                                        "bits": 5,
                                        "values": {
                                            '0': False,
                                            '1': True
                                        },
                                    },
                                    "cloud": {
                                        "description": "Cloudy",
                                        "bits": 6,
                                        "values": {
                                            '0': False,
                                            '1': True
                                        },
                                    },
                                    "water_observed": {
                                        "description": "Classified as water by the decision tree",
                                        "bits": 7,
                                        "values": {
                                            '0': False,
                                            '1': True
                                        },
                                    },
                                }
                            })
    })
    return output


@pytest.fixture
def dummy_raw_fc_data():
    output = xr.Dataset({
        "bs": dummy_da(546, "bs", coords, dtype=np.int16),
        "pv": dummy_da(723, "pv", coords, dtype=np.int16),
        "npv": dummy_da(209, "npv", coords, dtype=np.int16),
    })
    return output


@pytest.fixture
def dummy_raw_fc_plus_wo(dummy_raw_fc_data, dummy_raw_wo_data):
    return xarray.combine_by_coords(
            [dummy_raw_fc_data, dummy_raw_wo_data],
            join="exact")


@pytest.fixture
def configs_for_landsat():
    def ndvi(data):
        # Calculate NDVI (-1.0 to 1.0)
        unscaled = (data["nir"] - data["red"]) / (data["nir"] + data["red"])
        # Scale to [-1.0 - 1.0] to [0 - 255]
        scaled = ((unscaled + 1.0) * 255 / 2).clip(0, 255)
        return scaled

    from datacube_ows.styles.api import scalable

    @scalable
    def scaled_ndvi(data):
        # Calculate NDVI (-1.0 to 1.0)
        return (data["nir"] - data["red"]) / (data["nir"] + data["red"])

    return [
        {
            "components": {
                "red": {"red": 1.0},
                "green": {"green": 1.0},
                "blue": {"blue": 1.0},
            },
            "scale_range": (50, 3000),
        },
        {
            "components": {
                "red": {"swir1": 1.0},
                "green": {"nir": 1.0},
                "blue": {"green": 1.0},
            },
            "scale_range": (50, 3000),
        },
        {
            "components": {
                "red": {"red": 1.0},
                "green": {"red": 1.0},
                "blue": {"red": 1.0},
            },
            "scale_range": (50, 3000),
        },
        {
            "components": {
                "red": {
                    "red": 0.333,
                    "green": 0.333,
                    "blue": 0.333,
                },
                "green": {"nir": 1.0},
                "blue": {
                    "swir1": 0.5,
                    "swir2": 0.5,
                },
            },
            "scale_range": (50, 3000),
        },
        {
            "components": {
                "red": {"red": 1.0},
                "green": {},
                "blue": {},
            },
            "scale_range": (50, 3000),
        },
        {
            "components": {
                "red": {"red": 1.0},
                "green": {"green": 1.0},
                "blue": {"blue": 1.0},
            },
            "scale_range": (10, 800),
        },
        {
            "components": {
                "red": {"red": 1.0},
                "green": {"green": 1.0},
                "blue": {"blue": 1.0},
            },
            "scale_range": (1000, 8000),
        },
        {
            "components": {
                "red": {"red": 1.0},
                "green": {"green": 1.0},
                "blue": {"blue": 1.0},
            },
            "scale_range": (1000, 3000),
        },
        {
            "components": {
                "red": {
                    "swir1": 1.0,
                    "scale_range": (1500, 3700),
                },
                "green": {
                    "nir": 1.0,
                    "scale_range": (1600, 3200),
                },
                "blue": {"green": 1.0},
            },
            "scale_range": (200, 1900),
        },
        {
            "components": {
                "red": {"red": 1.0},
                "green": ndvi,
                "blue": {"blue": 1.0},
            },
            "scale_range": (50, 3000),
        },
        {
            "components": {
                "red": {"red": 1.0},
                "green": {
                    "function": scaled_ndvi,
                    "kwargs": {
                        "scale_from": (0.0, 1.0),
                        "scale_to": (0, 255)
                    }
                },
                "blue": {"blue": 1.0},
            },
            "scale_range": (50, 3000),
        },
        {
            "components": {
                "red": {"red": 1.0},
                "green": {
                    "function": "datacube_ows.band_utils.norm_diff",
                    "kwargs": {
                        "band1": "nir",
                        "band2": "red",
                        "scale_from": (0.0, 1.0),
                        "scale_to": (0, 255)
                    }
                },
                "blue": {
                    "function": "datacube_ows.band_utils.norm_diff",
                    "kwargs": {
                        "band1": "green",
                        "band2": "nir",
                        "scale_from": (0.0, 1.0),
                        "scale_to": (0, 255)
                    }
                },
            },
            "scale_range": (50, 3000),
        },
        {
            "index_function": {
                "function": "datacube_ows.band_utils.norm_diff",
                "mapped_bands": True,
                "kwargs": {"band1": "nir", "band2": "red"},
            },
            "mpl_ramp": "RdYlGn",
            "range": [-1.0, 1.0]
        },
        {
            "index_function": {
                "function": "datacube_ows.band_utils.norm_diff",
                "kwargs": {"band1": "nir", "band2": "red"},
            },
            "mpl_ramp": "ocean_r",
            "range": [0.0, 1.0]
        },
        {
            "index_function": {
                "function": "datacube_ows.band_utils.norm_diff",
                "kwargs": {"band1": "nir", "band2": "red"},
            },
            "color_ramp": [
                {"value": -1.0, "color": "#0000FF"},
                {"value": -0.2, "color": "#005050", },
                {"value": -0.1, "color": "#505050", },
                {"value": -0.01, "color": "#303030", },
                {"value": 0.0, "color": "black", },
                {"value": 0.01, "color": "#303000", },
                {"value": 0.5, "color": "#707030", },
                {"value": 1.0, "color": "#FF9090", },
            ]
        },
        {
            "index_function": {
                "function": "datacube_ows.band_utils.norm_diff",
                "kwargs": {"band1": "nir", "band2": "red"},
            },
            "color_ramp": [
                {
                    "value": -1.0,
                    "color": "#000000",
                    "alpha": 0.0,
                },
                {
                    "value": 0.0,
                    "color": "#000000",
                    "alpha": 0.0,
                },
                {
                    "value": 0.1,
                    "color": "#000030",
                    "alpha": 1.0,
                },
                {
                    "value": 0.3,
                    "color": "#703070",
                },
                {
                    "value": 0.6,
                    "color": "#e0e070",
                },
                {
                    "value": 1.0,
                    "color": "#90FF90",
                }
            ]
        },
        {
            "components": {
                "red": {"red": 1.0},
                "green": {"green": 1.0},
                "blue": {"blue": 1.0},
                "alpha": {
                    "function": "datacube_ows.band_utils.norm_diff",
                    "kwargs": {
                        "band1": "nir",
                        "band2": "red",
                        "scale_from": (0.0, 0.5),
                        "scale_to": (0, 255)
                    }
                },
            },
            "scale_range": (50, 3000),
        },
    ]


@pytest.fixture
def configs_for_wofs():
    return [
        {
            "name": "observations",
            "title": "Observations",
            "abstract": "Observations",
            "value_map": {
                "water": [
                    {
                        "title": "Water",
                        "abstract": "",
                        "flags": {"water_observed": True},
                        "color": "Aqua",
                    },
                    {
                        "title": "Cloud",
                        "abstract": "",
                        "flags": {"cloud": True},
                        "color": "Beige",
                    },
                    {
                        "title": "Terrain",
                        "abstract": "",
                        # Flag rules can contain an "or" - they match if either of the conditions hold.
                        "flags": {"or": {"terrain_shadow": True, "high_slope": True}},
                        "color": "SlateGray",
                    },
                    {
                        "title": "Cloud Shadow and High Slope",
                        "abstract": "",
                        # Flag rules can contain an "and" - they match if all of the conditions hold.
                        "flags": {"and": {"cloud_shadow": True, "high_slope": True}},
                        "color": "DarkKhaki",
                    },
                    {
                        "title": "Dry",
                        "abstract": "",
                        "flags": {"water_observed": False},
                        "color": "Brown",
                    },
                ]
            }
        },
        {
            "name": "observations",
            "title": "Observations",
            "abstract": "Observations",
            "value_map": {
                "water": [
                    # Cloudy Slopes rule needs to come before the Cloud
                    # and High Slopes rules.
                    {
                        "title": "Cloudy Slopes",
                        "abstract": "",
                        "flags": {"and": {"cloud": True, "high_slope": True}},
                        "color": "BurlyWood",
                    },
                    # Only matches non-cloudy high-slopes.
                    {
                        "title": "High Slopes",
                        "abstract": "",
                        "flags": {"high_slope": True},
                        "color": "Brown",
                    },
                    {
                        "title": "Cloud",
                        "abstract": "",
                        "flags": {"cloud": True},
                        "color": "Beige",
                    },
                    {
                        "title": "Cloud Shadow",
                        "abstract": "",
                        "flags": {"cloud_shadow": True},
                        "color": "SlateGray",
                    },
                    {
                        "title": "Water",
                        "abstract": "",
                        "flags": {"water_observed": True},
                        "color": "Aqua",
                    },
                    {
                        "title": "Dry",
                        "abstract": "",
                        "flags": {"water_observed": False},
                        "color": "SaddleBrown",
                    },
                ]
            }
        },
        {
            "value_map": {
                "water": [
                    {
                        # Make noncontiguous data transparent
                        "title": "",
                        "abstract": "",
                        "flags": {
                            "or": {
                                "noncontiguous": True,
                                "nodata": True,
                            },
                        },
                        "alpha": 0.0,
                        "color": "#ffffff",
                    },
                    {
                        "title": "Cloudy Steep Terrain",
                        "abstract": "",
                        "flags": {
                            "and": {
                                "high_slope": True,
                                "cloud": True
                            }
                        },
                        "color": "#f2dcb4",
                    },
                    {
                        "title": "Cloudy Water",
                        "abstract": "",
                        "flags": {
                            "and": {
                                "water_observed": True,
                                "cloud": True
                            }
                        },
                        "color": "#bad4f2",
                    },
                    {
                        "title": "Shaded Water",
                        "abstract": "",
                        "flags": {
                            "and": {
                                "water_observed": True,
                                "cloud_shadow": True
                            }
                        },
                        "color": "#335277",
                    },
                    {
                        "title": "Cloud",
                        "abstract": "",
                        "flags": {"cloud": True},
                        "color": "#c2c1c0",
                    },
                    {
                        "title": "Cloud Shadow",
                        "abstract": "",
                        "flags": {"cloud_shadow": True},
                        "color": "#4b4b37",
                    },
                    {
                        "title": "Terrain Shadow or Low Sun Angle",
                        "abstract": "",
                        "flags": {
                            "or": {
                                "terrain_shadow": True,
                                "low_solar_angle": True
                            },
                        },
                        "color": "#2f2922",
                    },
                    {
                        "title": "Steep Terrain",
                        "abstract": "",
                        "flags": {"high_slope": True},
                        "color": "#776857",
                    },
                    {
                        "title": "Water",
                        "abstract": "",
                        "flags": {
                            "water_observed": True,
                        },
                        "color": "#4f81bd",
                    },
                    {
                        "title": "Dry",
                        "abstract": "",
                        "flags": {"water_observed": False},
                        "color": "#96966e",
                    },
                ]
            },
        },
    ]


@pytest.fixture
def configs_for_combined_fc_wofs():
    return [
        {
            "components": {
                "red": {"bs": 1.0},
                "green": {"pv": 1.0},
                "blue": {"npv": 1.0}},
            "scale_range": [0.0, 100.0],
        },
        {
            "components": {
                "red": {"bs": 1.0},
                "green": {"pv": 1.0},
                "blue": {"npv": 1.0}
            },
            "scale_range": [0.0, 100.0],
            "pq_masks": [
                {
                    "band": "water",
                    "flags": {
                        "nodata": False,
                        "noncontiguous": False,
                        "terrain_shadow": False,
                        "low_solar_angle": False,
                        "high_slope": False,
                        "cloud_shadow": False,
                        "cloud": False,
                        "water_observed": False,
                    }
                }
            ]
        },
        {
            "components": {
                "red": {"bs": 1.0},
                "green": {"pv": 1.0},
                "blue": {"npv": 1.0}
            },
            "scale_range": [0.0, 100.0],
            "pq_masks": [
                {
                    "band": "water",
                    "enum": 1,
                }
            ]
        },
        {
            "components": {
                "red": {"bs": 1.0},
                "green": {"pv": 1.0},
                "blue": {"npv": 1.0}
            },
            "scale_range": [0.0, 100.0],
            "pq_masks": [
                {
                    "band": "water",
                    "enum": 1,
                    "invert": True,
                }
            ]
        },
        {
            "components": {
                "red": {"bs": 1.0},
                "green": {"pv": 1.0},
                "blue": {"npv": 1.0}
            },
            "scale_range": [0.0, 100.0],
            "pq_masks": [
                {
                    # Mask out nodata pixels.
                    "band": "water",
                    "enum": 1,
                    "invert": True,
                },
                {
                    # Mask out pixels with low_solar_angle, high_slope
                    #      or cloud shadow.
                    "band": "water",
                    "flags": {
                        "low_solar_angle": False,
                        "high_slope": False,
                        "cloud_shadow": False,
                    }
                },
                {
                    # Mask out pixels with cloud AND no water observed
                    "band": "water",
                    "flags": {
                        "cloud": True,
                        "water_observed": False,
                    },
                    "invert": True,
                },
            ]
        }
    ]

