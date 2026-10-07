# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import datetime
from typing import override
from unittest.mock import MagicMock

import numpy as np
import pytest
from affine import Affine
from odc.geo.geobox import GeoBox
from odc.geo.geom import polygon
from xarray import Dataset

import datacube_ows.data
import datacube_ows.feature_info
from datacube_ows.data import _write_empty, _write_polygon
from datacube_ows.feature_info import get_s3_browser_uris
from datacube_ows.loading import DataStacker, ProductBandQuery
from datacube_ows.ogc_exceptions import WMSException
from datacube_ows.ows_configuration import TimeRes
from tests.test_styles import product_layer  # noqa: F401


@pytest.fixture
def s3_url_datasets():
    class TestDataset:
        def __init__(self, uris) -> None:
            self.uris = uris

    datasets = []
    d1 = TestDataset(
        [
            "s3://test-bucket/hello_world/data.yaml",
            "s3://test-bucket/hello_world/data.yaml",
        ]
    )
    d2 = TestDataset(
        [
            "s3://test-bucket/hello.word/foo.bar/hello.test.yaml",
            "s3://test-bucket/hello.word/foo.bar/hello-test.yaml",
        ]
    )
    d3 = TestDataset(["s3://test-bucket/this.is/from.stac/hello.test.json"])

    datasets.append(d1)
    datasets.append(d2)
    datasets.append(d3)

    class DataSetMock:
        def __init__(self, datasets) -> None:
            self.datasets = datasets

            class InnerMock:
                def __init__(self, datasets) -> None:
                    self.datasets = datasets

                def item(self):
                    return self.datasets

            self.values = InnerMock(datasets)

    class PBQMock:
        def __init__(self, main) -> None:
            self.main = main

        @override
        def __hash__(self):
            return hash(self.main)

    return {
        PBQMock(True): [DataSetMock(datasets)],
        PBQMock(False): [DataSetMock(datasets)],
    }


def test_s3_browser_uris(s3_url_datasets) -> None:
    uris = get_s3_browser_uris(s3_url_datasets)

    assert (
        "http://test-bucket.s3-website-ap-southeast-2.amazonaws.com/?prefix=hello_world"
        in uris
    )
    assert (
        "http://test-bucket.s3-website-ap-southeast-2.amazonaws.com/?prefix=hello.word/foo.bar"
        in uris
    )
    assert (
        "http://test-bucket.s3-website-ap-southeast-2.amazonaws.com/?prefix=this.is/from.stac"
        in uris
    )


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
#             self.center_time = datetime.now(timezone.utc)
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


def test_make_derived_band_dict_nan() -> None:
    class FakeData:
        def __init__(self) -> None:
            self.nodata = np.nan

        def item(self):
            return np.nan

    class FakeDataset:
        def __getitem__(self, key):
            return FakeData()

    class FakeStyle:
        include_in_feature_info = True

        def __init__(self) -> None:
            self.needed_bands = ["test"]
            self.index_function = lambda x: FakeData()

    style_dict = {"fake": FakeStyle()}

    band_dict = datacube_ows.feature_info._make_derived_band_dict(
        FakeDataset(), style_dict
    )
    assert band_dict["fake"] == "n/a"


def test_make_derived_band_dict_not_nan() -> None:
    class FakeData:
        def __init__(self) -> None:
            self.nodata = -6666

        def item(self) -> float:
            return 10.10

    class FakeDataset:
        def __getitem__(self, key):
            return FakeData()

    class FakeStyle:
        include_in_feature_info = True

        def __init__(self) -> None:
            self.needed_bands = ["test"]
            self.index_function = lambda x: FakeData()

    style_dict = {"fake": FakeStyle()}

    band_dict = datacube_ows.feature_info._make_derived_band_dict(
        FakeDataset(), style_dict
    )
    assert band_dict["fake"] == 10.10


def test_make_band_dict_nan(product_layer) -> None:  # noqa: F811
    class FakeData:
        def __init__(self) -> None:
            self.nodata = np.nan
            self.attrs = {}

        def item(self):
            return np.nan

    class FakeDataset:
        def __init__(self) -> None:
            self.data_vars = {"fake": "fake_band"}

        def __getitem__(self, key):
            return FakeData()

    band_dict = datacube_ows.feature_info._make_band_dict(product_layer, FakeDataset())
    assert band_dict["fake"] == "n/a"


def test_make_band_dict_float(product_layer) -> None:  # noqa: F811
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

    class IntData:
        def __init__(self) -> None:
            self.nodata = np.nan
            self.attrs = yaml.load(flags_yaml, yaml.Loader)

        def item(self) -> int:
            return 100

    class IntDataset:
        def __init__(self) -> None:
            self.data_vars = {"fake": "fake_band"}

        def __getitem__(self, key):
            return IntData()

    class FloatData(IntData):
        @override
        def item(self) -> float:
            return 100.0

    class FloatDataset(IntDataset):
        @override
        def __getitem__(self, key):
            return FloatData()

    band_dict = datacube_ows.feature_info._make_band_dict(product_layer, IntDataset())
    assert isinstance(band_dict["fake"], dict)
    assert band_dict["fake"] == {
        "Mask image as provided by JAXA - Ocean and water, lay over, shadowing, land.": "lay_over"
    }

    band_dict = datacube_ows.feature_info._make_band_dict(product_layer, FloatDataset())
    assert isinstance(band_dict["fake"], dict)
    assert band_dict["fake"] == {
        "Mask image as provided by JAXA - Ocean and water, lay over, shadowing, land.": "lay_over"
    }


def test_pbq_ctor_simple(product_layer) -> None:  # noqa: F811
    pbq = ProductBandQuery.simple_layer_query(product_layer, {"red", "green"})
    assert str(pbq) in (
        "Query bands {'red', 'green'} from products [FakeODCProduct(test_odc_product)]",
        "Query bands {'green', 'red'} from products [FakeODCProduct(test_odc_product)]",
    )
    pbq = ProductBandQuery.simple_layer_query(
        product_layer, {"red", "green"}, resource_limited=True
    )
    assert str(pbq) in (
        "Query bands {'red', 'green'} from products [FakeODCProduct(test_odc_summary_product)]",
        "Query bands {'green', 'red'} from products [FakeODCProduct(test_odc_summary_product)]",
    )


def test_pbq_ctor_full(product_layer) -> None:  # noqa: F811
    pbqs = ProductBandQuery.full_layer_queries(product_layer)
    assert len(pbqs) == 2
    assert "red" in str(pbqs[0])
    assert "green" in str(pbqs[0])
    assert "blue" in str(pbqs[0])
    assert "fake" in str(pbqs[0])
    assert "Query bands {" in str(pbqs[0])
    assert "} from products [FakeODCProduct(test_odc_product)]" in str(pbqs[0])
    assert str(pbqs[1]) in (
        "Query bands {'wongle', 'pq'} from products [FakeODCProduct(test_masking_product)]",
        "Query bands {'pq', 'wongle'} from products [FakeODCProduct(test_masking_product)]",
    )


def test_user_date_sorter() -> None:
    layer = MagicMock()
    layer.time_resolution.is_subday.return_value = False
    minx, maxx = 140, 141
    miny, maxy = -35, -34
    crs = "EPSG:4326"
    geom = polygon(
        [(minx, maxy), (minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)], crs
    )

    odc_dates = [
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


def test_create_nodata(dummy_raw_calc_data) -> None:
    ds = DataStacker.__new__(DataStacker)
    data_in = dummy_raw_calc_data
    prod = MagicMock()
    prod.measurements = {"flagband": MagicMock()}
    prod.measurements["flagband"].nodata = 1
    pbq = ProductBandQuery([prod], ["flagband"], False)
    data_out = ds.create_nodata_filled_flag_bands(data_in, pbq)
    assert data_out["flagband"][0] == 1
    assert data_out["flagband"][5] == 1
    with pytest.raises(WMSException) as e:
        data_out = ds.create_nodata_filled_flag_bands(Dataset(), pbq)
    assert "Cannot add default flag data as there is no non-flag data available" in str(
        e.value
    )


@pytest.fixture
def simple_geobox() -> GeoBox:
    affine_transform = Affine(0.1, 0.0, 140.0, 0.0, -0.1, -34.0)
    return GeoBox((10, 10), affine_transform, "EPSG:4326")


@pytest.fixture
def sorter_geom():
    minx, maxx = 140, 141
    miny, maxy = -35, -34
    crs = "EPSG:4326"
    return polygon(
        [(minx, maxy), (minx, miny), (maxx, miny), (maxx, maxy), (minx, maxy)], crs
    )


def test_write_empty(simple_geobox) -> None:
    result = _write_empty(simple_geobox)
    assert isinstance(result, bytes)
    assert len(result) > 0
    # PNG magic bytes
    assert result[:4] == b"\x89PNG"


def test_write_polygon_within(simple_geobox) -> None:
    # A polygon that fully contains the geobox extent
    big_polygon = polygon(
        [(138, -33), (138, -36), (143, -36), (143, -33), (138, -33)], "EPSG:4326"
    )
    layer_mock = MagicMock()
    zoom_fill = [100, 80, 60, 40]
    result = _write_polygon(simple_geobox, big_polygon, zoom_fill, layer_mock)
    assert isinstance(result, bytes)
    assert len(result) > 0
    assert result[:4] == b"\x89PNG"


def test_write_polygon_partial(simple_geobox) -> None:
    # A polygon that only partially overlaps with the geobox extent
    partial_polygon = polygon(
        [(140.3, -34.7), (140.3, -34.3), (140.7, -34.3), (140.7, -34.7), (140.3, -34.7)],
        "EPSG:4326",
    )
    layer_mock = MagicMock()
    zoom_fill = [100, 80, 60, 40]
    result = _write_polygon(simple_geobox, partial_polygon, zoom_fill, layer_mock)
    assert isinstance(result, bytes)
    assert len(result) > 0
    assert result[:4] == b"\x89PNG"


def test_user_date_sorter_summary(sorter_geom) -> None:
    layer = MagicMock()
    layer.time_resolution = TimeRes.SUMMARY

    odc_dates = [
        np.datetime64(datetime.datetime(2019, 1, 1, 12, 0, 0), "ns"),
        np.datetime64(datetime.datetime(2020, 1, 1, 12, 0, 0), "ns"),
    ]

    user_dates = [
        datetime.date(2020, 1, 1),
        datetime.date(2019, 1, 1),
    ]

    sorter = datacube_ows.data.user_date_sorter(layer, odc_dates, sorter_geom, user_dates)
    assert sorter.values[0] == 1
    assert sorter.values[1] == 0


def test_user_date_sorter_subday(sorter_geom) -> None:
    layer = MagicMock()
    layer.time_resolution = TimeRes.SUBDAY

    odc_dates = [
        np.datetime64(datetime.datetime(2019, 6, 15, 8, 0, 0), "ns"),
        np.datetime64(datetime.datetime(2019, 6, 16, 8, 0, 0), "ns"),
    ]

    # user_dates[0] is in the window of odc_dates[1], user_dates[1] is in the window of odc_dates[0]
    user_dates = [
        datetime.datetime(2019, 6, 16, 9, 0, 0),
        datetime.datetime(2019, 6, 15, 9, 0, 0),
    ]

    sorter = datacube_ows.data.user_date_sorter(layer, odc_dates, sorter_geom, user_dates)
    assert sorter.values[0] == 1
    assert sorter.values[1] == 0

