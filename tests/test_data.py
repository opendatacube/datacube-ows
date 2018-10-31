import datacube_wms.data as odcdata

from datacube_wms.data import get_s3_browser_uris

import pytest

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

