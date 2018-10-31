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
            return band

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

    # # Test fuse funcing
    # sources = [ fakesource(1), fakesource(2) ]

    # def fake_read_file2(source, geobox, band, no_data, resampling):
    #     if source.get_bandnumber() == 1:
    #         return
    #     else:
    #         return
    #     return np.zeros(geobox.shape).astype("int16")