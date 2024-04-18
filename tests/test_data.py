# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import datetime
from unittest.mock import MagicMock

import numpy as np
import pytest
from odc.geo.geom import polygon
from xarray import Dataset

import datacube_ows.data
from datacube_ows.data import ProductBandQuery, get_s3_browser_uris
from datacube_ows.ogc_exceptions import WMSException
from tests.test_styles import product_layer  # noqa: F401


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

    class PBQMock:
        def __init__(self, main):
            self.main = main

        def __hash__(self):
            return hash(self.main)

    return {
        PBQMock(True): [DataSetMock(datasets)],
        PBQMock(False): [DataSetMock(datasets)],
    }


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


def test_make_band_dict_nan(product_layer): # noqa: F811
    class fake_data:
        def __init__(self):
            self.nodata = np.nan
            self.attrs = {}

        def item(self):
            return np.nan

    class fake_dataset:
        def __init__(self):
            self.data_vars = {
                "fake": "fake_band"
            }

        def __getitem__(self, key):
            return fake_data()

    bands = ["fake"]

    band_dict = datacube_ows.data._make_band_dict(product_layer, fake_dataset())
    assert band_dict["fake"] == "n/a"


def test_make_band_dict_float(product_layer): # noqa: F811
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
        def __init__(self):
            self.data_vars = {
                "fake": "fake_band"
            }

        def __getitem__(self, key):
            return int_data()

    class float_data(int_data):
        def item(self):
            return 100.0

    class float_dataset(int_dataset):
        def __getitem__(self, key):
            return float_data()

    bands = ["fake"]

    band_dict = datacube_ows.data._make_band_dict(product_layer, int_dataset())
    assert isinstance(band_dict["fake"], dict)
    assert band_dict["fake"] == {
        "Mask image as provided by JAXA - Ocean and water, lay over, shadowing, land.": 'lay_over'
    }

    band_dict = datacube_ows.data._make_band_dict(product_layer, float_dataset())
    assert isinstance(band_dict["fake"], dict)
    assert band_dict["fake"] == {
        "Mask image as provided by JAXA - Ocean and water, lay over, shadowing, land.": 'lay_over'
    }


def test_pbq_ctor_simple(product_layer): # noqa: F811
    pbq = ProductBandQuery.simple_layer_query(product_layer, set(["red", "green"]))
    assert str(pbq) in (
        "Query bands {'red', 'green'} from products [FakeODCProduct(test_odc_product)]",
        "Query bands {'green', 'red'} from products [FakeODCProduct(test_odc_product)]"
    )
    pbq = ProductBandQuery.simple_layer_query(product_layer, set(["red", "green"]), resource_limited=True)
    assert str(pbq) in (
        "Query bands {'red', 'green'} from products [FakeODCProduct(test_odc_summary_product)]",
        "Query bands {'green', 'red'} from products [FakeODCProduct(test_odc_summary_product)]"
    )


def test_pbq_ctor_full(product_layer): # noqa: F811
    pbqs = ProductBandQuery.full_layer_queries(product_layer)
    assert len(pbqs) == 2
    assert "red" in str(pbqs[0])
    assert "green" in str(pbqs[0])
    assert "blue" in str(pbqs[0])
    assert "fake" in str(pbqs[0])
    assert "Query bands {" in str(pbqs[0])
    assert "} from products [FakeODCProduct(test_odc_product)]"  in str(pbqs[0])
    assert str(pbqs[1]) in (
        "Query bands ('wongle', 'pq') from products [FakeODCProduct(test_masking_product)]",
        "Query bands ('pq', 'wongle') from products [FakeODCProduct(test_masking_product)]",
    )


def test_user_date_sorter():
    layer = MagicMock()
    layer.time_resolution.is_subday.return_value = False
    minx, maxx = 140, 141
    miny, maxy = -35, -34
    crs = "EPSG:4326"
    geom = polygon([(minx, maxy), (minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)], crs)

    odc_dates =  [
        np.datetime64(datetime.datetime(2018, 12, 31, 20, 0, 0), "ns"),
        np.datetime64(datetime.datetime(2019, 12, 31, 20, 0, 0), "ns"),
        np.datetime64(datetime.datetime(2020, 12, 31, 20, 0, 0), "ns"),
     ]

    user_dates = [
        datetime.date(2021, 1, 1),
        datetime.date(2019, 1, 1),
        datetime.date(2020, 1, 1),
    ]

    sorter = datacube_ows.data.user_date_sorter(layer, odc_dates, geom, user_dates)
    assert sorter.values[0] == 1
    assert sorter.values[1] == 2
    assert sorter.values[2] == 0


def test_create_nodata(dummy_raw_calc_data):
    from datacube_ows.data import DataStacker
    ds = DataStacker.__new__(DataStacker)
    data_in = dummy_raw_calc_data
    prod = MagicMock()
    prod.measurements = {
        "flagband": MagicMock()
    }
    prod.measurements["flagband"].nodata = 1
    pbq = ProductBandQuery(
                    [prod],
                    ["flagband"],
                    False)
    data_out = ds.create_nodata_filled_flag_bands(data_in, pbq)
    assert data_out["flagband"][0] == 1
    assert data_out["flagband"][5] == 1
    with pytest.raises(WMSException) as e:
        data_out = ds.create_nodata_filled_flag_bands(Dataset(), pbq)
    assert "Cannot add default flag data as there is no non-flag data available" in str(e.value)
