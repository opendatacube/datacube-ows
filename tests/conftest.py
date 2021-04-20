import datetime
from unittest.mock import MagicMock

import numpy as np
import pytest
import xarray as xr

from tests.utils import dummy_da, coords, dim1_da


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
    global_cfg.attribution = "Global Attribution"
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
    return global_cfg


@pytest.fixture
def minimal_parent():
    parent = MagicMock()
    parent.abstract = "Parent Abstract"
    parent.keywords = {"global", "parent"}
    parent.attribution = "Parent Attribution"
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