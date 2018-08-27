# pylint: skip-file

import datacube
import pytest

from datacube_wms.data import feature_info
import flask
import json
import os

test_data = [
    ({
        "bbox": "12993071.8160274,-2504688.542848654,13149614.84995544,-2348145.5089206137",
        "srs": "EPSG:3857",
        "query_layers": "ls8_nbart_geomedian_annual",
        "version": "1.1.1",
        "x": "210",
        "y": "109",
        "time": "2015-01-01",
        "width": "256",
        "height": "256",
        "info_format": "application/json",
        "feature_count": "101"
    },
        {
        "type": "FeatureCollection",
        "features": [{
            "properties": {
                "lon": 117.87506103515621,
                "lat": -21.194655303138624,
                "time": "2015-01-01 00:00:00 UTC",
                "data_available_for_dates": [
                    "2015-01-01"
                ],
                "data_links": [
                    "s3://dea-test-store/geomedian-australia/v2.1.0/L8/x_-15/y_-24/2015/01/01/ls8_gm_nbart_-15_-24_20150101.yaml"
                ],
                "bands": {
                    "blue": 632,
                    "green": 1098,
                    "red": 1706,
                    "nir": 2618,
                    "swir1": 3353,
                    "swir2": 2685
                }
            }
        }]
    })
]


@pytest.mark.parametrize("test_args, expect", test_data)
def test_compose(cube, release_cube_dummy, mocker, test_args, expect):
    mocker.patch('datacube_wms.data.get_cube', cube)
    mocker.patch('datacube_wms.wms_layers.get_cube', cube)
    mocker.patch('datacube_wms.data.release_cube', release_cube_dummy)
    mocker.patch('datacube_wms.wms_layers.release_cube', release_cube_dummy)

    # stacker = DataStacker('s2b_nrt_granule', None, '2008-01-01')
    app = flask.Flask(
        "test",
        root_path=os.path.dirname(os.path.realpath(__file__) + "/../.."))
    with app.test_request_context('/?GetFeatureInfo'):
        result = json.loads(feature_info(test_args)[0])

        assert result["type"] == expect["type"]
        assert len(result["features"]) == 1
        feature = result["features"][0]
        expected_feature = expect["features"][0]
        properties = feature["properties"]
        expected_properties = expected_feature["properties"]
        bands = properties["bands"]
        expected_bands = expected_properties["bands"]
        assert properties["lon"] == expected_properties["lon"]
        assert properties["lat"] == expected_properties["lat"]
        assert properties["time"] == expected_properties["time"]
        assert bands["blue"] == expected_bands["blue"]
        assert bands["green"] == expected_bands["green"]
        assert bands["red"] == expected_bands["red"]
        assert bands["nir"] == expected_bands["nir"]
        assert bands["swir1"] == expected_bands["swir1"]
        assert bands["swir2"] == expected_bands["swir2"]
        assert properties["data_available_for_dates"][0] == expected_properties["data_available_for_dates"][0]
        assert properties["data_links"][0] == expected_properties["data_links"][0]
