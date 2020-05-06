import datacube_ows.data

from datacube_ows.data import get_s3_browser_uris

import pytest

from unittest.mock import patch, MagicMock
from tests.test_band_mapper import product_layer
from datetime import datetime

import numpy as np

@pytest.fixture
def s3_url_datasets():
    class TestDataset:
        def __init__(self, uris):
            self.uris = uris

    datasets = list()
    d1 = TestDataset([
            "s3://test-bucket/hello_world/data.yaml",
            "s3://test-bucket/hello_world/data.yaml"
        ])
    d2 = TestDataset([
            "s3://test-bucket/hello.word/foo.bar/hello.test.yaml",
            "s3://test-bucket/hello.word/foo.bar/hello-test.yaml"
        ])

    datasets.append(d1)
    datasets.append(d2)

    class DataSetMock:
        def __init__(self, datasets):
            self.datasets = datasets

            class InnerMock:
                def __init__(self, datasets):
                    self.datasets = datasets
                def item(self):
                    return self.datasets
            self.values = InnerMock(datasets)

    return [DataSetMock(datasets)]

def test_s3_browser_uris(s3_url_datasets):
    uris = get_s3_browser_uris(s3_url_datasets)

    assert "http://test-bucket.s3-website-ap-southeast-2.amazonaws.com/?prefix=hello_world" in uris
    assert "http://test-bucket.s3-website-ap-southeast-2.amazonaws.com/?prefix=hello.word/foo.bar" in uris

# TODO: read_data is now a method of the DataStacker class. This test needs a rewrite.
# @patch('xarray.Dataset')
# def test_read_data(dataset):
#
#     class fake_coords:
#         def __init__(self):
#             self.values = 1
#             self.units = "m"
#
#     class fakegeobox:
#         def __init__(self):
#             self.dimensions = ["hello"]
#             self.crs = "EPSG:3577"
#             self.coordinates = {
#                 "hello": fake_coords()
#             }
#
#     class fake_measurement:
#         def __init__(self, name, nodata, dtype):
#             self.name = name
#             self.nodata = nodata
#             self.dtype = dtype
#
#         def dataarray_attrs(self):
#             return None
#
#         def __getitem__(self, item):
#             return getattr(self, item)
#
#     class fake_dataset:
#         def __init__(self):
#             self.center_time = datetime.utcnow()
#             self.id = 1
#             self.metadata = dict()
#
#     datasets = [ fake_dataset() ]
#     measurements = [ fake_measurement("test", -1, "int16") ]
#     geobox = fakegeobox()
#     with patch('datacube.Datacube.load_data') as load_data, patch('datacube.api.query.solar_day') as solar_day:
#         datacube_wms.data.read_data(datasets, measurements, geobox)
#         assert load_data.called
#         assert solar_day.called

def test_make_derived_band_dict_nan():
    class fake_data:
        def __init__(self):
            self.nodata = np.nan
        def item(self):
            return np.nan

    class fake_dataset:
        def __getitem__(self, key):
            return fake_data()

    class fake_style:
        include_in_feature_info = True
        def __init__(self):
            self.needed_bands = ["test"]
            self.index_function = lambda x: fake_data()

    style_dict = {
        "fake": fake_style()
    }

    band_dict = datacube_ows.data._make_derived_band_dict(fake_dataset(), style_dict)
    assert band_dict["fake"] == "n/a"

def test_make_derived_band_dict_not_nan():
    class fake_data:
        def __init__(self):
            self.nodata = -6666
        def item(self):
            return 10.10

    class fake_dataset:
        def __getitem__(self, key):
            return fake_data()

    class fake_style:
        include_in_feature_info = True
        def __init__(self):
            self.needed_bands = ["test"]
            self.index_function = lambda x: fake_data()

    style_dict = {
        "fake": fake_style()
    }

    band_dict = datacube_ows.data._make_derived_band_dict(fake_dataset(), style_dict)
    assert band_dict["fake"] == 10.10

def test_make_band_dict_nan(product_layer):
    class fake_data:
        def __init__(self):
            self.nodata = np.nan
        def item(self):
            return np.nan

    class fake_dataset:
        def __getitem__(self, key):
            return fake_data()

    bands = ["fake"]

    band_dict = datacube_ows.data._make_band_dict(product_layer, fake_dataset(), bands)
    assert band_dict["fake"] == "n/a"

def test_make_band_dict_float(product_layer):
    import yaml
    flags_yaml = """
    flags_definition:
        category:
          bits: [0,1,2,3,4,5,6,7]
          description: Mask image as provided by JAXA - Ocean and water, lay over, shadowing, land.
          values:
            0: no_data
            50: water
            100: lay_over
            150: shadowing
            255: land
    """
    class int_data:
        def __init__(self):
            self.nodata = np.nan
            self.attrs = yaml.load(flags_yaml, yaml.Loader)
        def item(self):
            return 100

    class int_dataset:
        def __getitem__(self, key):
            return int_data()

    class float_data:
        def __init__(self):
            self.nodata = np.nan
            self.attrs = yaml.load(flags_yaml, yaml.Loader)
        def item(self):
            return 100.0

    class float_dataset:
        def __getitem__(self, key):
            return float_data()

    bands = ["fake"]

    band_dict = datacube_ows.data._make_band_dict(product_layer, int_dataset(), bands)
    assert isinstance(band_dict["fake"], list) 
    assert band_dict["fake"] == ['Mask image as provided by JAXA - Ocean and water, lay over, shadowing, land.']

    band_dict = datacube_ows.data._make_band_dict(product_layer, float_dataset(), bands)
    assert isinstance(band_dict["fake"], list) 
    assert band_dict["fake"] == ['Mask image as provided by JAXA - Ocean and water, lay over, shadowing, land.']


