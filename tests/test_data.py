import datacube_wms.data

from datacube_wms.data import get_s3_browser_uris

import pytest

from unittest.mock import patch, MagicMock

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
    return datasets

def test_s3_browser_uris(s3_url_datasets):
    uris = get_s3_browser_uris(s3_url_datasets)

    assert "http://test-bucket.s3-website-ap-southeast-2.amazonaws.com/?prefix=hello_world" in uris
    assert "http://test-bucket.s3-website-ap-southeast-2.amazonaws.com/?prefix=hello.word/foo.bar" in uris

from datacube_wms.data import _make_destination

def test_make_destination():
    dest = _make_destination((256, 256), -1, "int16")

    assert dest.shape == (256, 256)
    assert (dest == -1).all()
    assert dest.dtype == np.dtype("int16")

def test_get_measurement():

    class fakegeobox:
        def __init__(self, shape):
            self.shape = shape

    class fakesource:
        def __init__(self, band=1):
            self.band = band
        def get_bandnumber(self):
            return self.band

    def fake_delayed(some_callable):
        return some_callable

    def fake_as_delayed():
        class fakeda:
            def from_delayed(self, destination, shape, dtype):
                return destination
        return fakeda()

    def fake_read_file(source, geobox, band, no_data, resampling):
        return np.zeros(geobox.shape).astype("int16")

    gb = fakegeobox((256, 256))
    sources = [ fakesource() ]

    # test basic
    with patch('datacube_wms.data._read_file', new_callable=lambda: fake_read_file) as rf, patch('datacube_wms.data.da', new_callable=fake_as_delayed) as da, patch('datacube_wms.data.delayed', new_callable=lambda: fake_delayed) as delayed:
        result = datacube_wms.data._get_measurement(sources, gb, None, -1, "int16", fuse_func=None)

    assert (result == 0).all()
    assert result.shape == (256, 256)

    # Test fuse funcing
    sources = [ fakesource(1), fakesource(2) ]
    gb = fakegeobox((16,16))

    def fake_read_file2(source, geobox, band, no_data, resampling):
        if source.get_bandnumber() == 1:
            return np.full((16,16), np.nan)
        else:
            return np.full((16,16), 1., "float64")

    with patch('datacube_wms.data._read_file', new_callable=lambda: fake_read_file2) as rf, patch('datacube_wms.data.da', new_callable=fake_as_delayed) as da, patch('datacube_wms.data.delayed', new_callable=lambda: fake_delayed) as delayed:
        result = datacube_wms.data._get_measurement(sources, gb, None, np.nan, "float64", fuse_func=None)

    assert (result == 1.).all()
    assert result.shape == (16,16)

    # Test custom fuse func
    sources = [ fakesource(1), fakesource(2) ]

    def fake_read_file3(source, geobox, band, no_data, resampling):
        if source.get_bandnumber() == 1:
            return np.full((16,16), 56)
        else:
            return np.full((16,16), 20)

    def fake_fuse(dest, src):
        where_src_56 = (src == 56)
        np.copyto(dest, src, where=where_src_56)

    with patch('datacube_wms.data._read_file', new_callable=lambda: fake_read_file3) as rf, patch('datacube_wms.data.da', new_callable=fake_as_delayed) as da, patch('datacube_wms.data.delayed', new_callable=lambda: fake_delayed) as delayed:
        result = datacube_wms.data._get_measurement(sources, gb, None, -1, "int16", fuse_func=None)

    assert (result == 56).all()
    assert result.shape == (16,16)

@patch('datacube_wms.data.new_datasource')
@patch('xarray.Dataset')
def test_read_data(dataset, new_datasource):

    class fake_coords:
        def __init__(self):
            self.values = 1
            self.units = "m"

    class fakegeobox:
        def __init__(self):
            self.dimensions = ["hello"]
            self.crs = "EPSG:3577"
            self.coordinates = {
                "hello": fake_coords()
            }

    class fake_measurement:
        def __init__(self, name, nodata, dtype):
            self.name = name
            self.nodata = nodata
            self.dtype = dtype

        def dataarray_attrs(self):
            return None

        def __getitem__(self, item):
            return getattr(self, item)

    class fake_dataset:
        def __init__(self):
            self.id = 1

    class fake_datasource:
        def __init__(self):
            self._dataset = fake_dataset()

    # Test overviews / no overviews

    datasets = [ fake_dataset() ]
    measurements = [ fake_measurement("test", -1, "int16") ]
    geobox = fakegeobox()
    with patch('datacube.Datacube.load_data') as load_data, patch('datacube_wms.data._get_measurement') as get_measurement:
        datacube_wms.data.read_data(datasets, measurements, geobox, use_overviews=False)

        assert load_data.called
        assert not get_measurement.called

    with patch('datacube.Datacube.load_data') as load_data, patch('datacube_wms.data._get_measurement') as get_measurement:
        datacube_wms.data.read_data(datasets, measurements, geobox, use_overviews=True)

        assert not load_data.called
        assert get_measurement.called

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
        def __init__(self):
            self.needed_bands = ["test"]
            self.index_function = lambda x: fake_data()

    style_dict = {
        "fake": fake_style()
    }

    band_dict = datacube_wms.data._make_derived_band_dict(fake_dataset(), style_dict)
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
        def __init__(self):
            self.needed_bands = ["test"]
            self.index_function = lambda x: fake_data()

    style_dict = {
        "fake": fake_style()
    }

    band_dict = datacube_wms.data._make_derived_band_dict(fake_dataset(), style_dict)
    assert band_dict["fake"] == 10.10

def test_make_band_dict_nan():
    class fake_data:
        def __init__(self):
            self.nodata = np.nan
        def item(self):
            return np.nan

    class fake_dataset:
        def __getitem__(self, key):
            return fake_data()

    bands = ["fake"]

    band_dict = datacube_wms.data._make_band_dict(fake_dataset(), bands)
    assert band_dict["fake"] == "n/a"


