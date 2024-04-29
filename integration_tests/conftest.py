# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0


import os

pytest_plugins = ["helpers_namespace"]
import pytest
from click.testing import CliRunner
from pytest_localserver.http import WSGIServer

from datacube.cfg import ODCConfig
from datacube_ows import ogc
from datacube_ows.ogc import app


@pytest.fixture
def flask_client():
    with app.test_client() as client:
        yield client


class generic_obj(object):
    pass


@pytest.fixture(scope="session")
def ows_server(request):
    """
    Run the OWS server for the duration of these tests
    """
    external_url = os.environ.get("SERVER_URL")
    if external_url:
        server = generic_obj()
        server.url = external_url
    else:
        server = WSGIServer(port="5000", application=ogc.app)
        server.start()
        request.addfinalizer(server.stop)

    return server


@pytest.fixture
def runner():
    return CliRunner()


@pytest.helpers.register
def enclosed_bbox(bbox):
    lon_min, lat_min, lon_max, lat_max = bbox
    lon_range = lon_max - lon_min
    lat_range = lat_max - lat_min

    return (
        lon_min + 0.45 * lon_range,
        lat_min + 0.45 * lat_range,
        lon_max - 0.45 * lon_range,
        lat_max - 0.45 * lat_range,
    )


@pytest.helpers.register
def disjoint_bbox(bbox):
    lon_min, lat_min, lon_max, lat_max = bbox
    lon_range = lon_max - lon_min
    lat_range = lat_max - lat_min

    return (
        lon_min - 0.4 * lon_range,
        lat_min - 0.4 * lat_range,
        lon_min - 0.2 * lon_range,
        lat_min - 0.2 * lat_range,
    )

@pytest.helpers.register
def representative_bbox(bbox):
    lon_min, lat_min, lon_max, lat_max = bbox
    lon_range = lon_max - lon_min
    lat_range = lat_max - lat_min

    return (
        lon_min + 0.40 * lon_range,
        lat_min + 0.45 * lat_range,
        lon_min + 0.41 * lon_range,
        lat_min + 0.46 * lat_range,
    )


@pytest.fixture
def product_name():
    return "s2_l2a"


@pytest.fixture
def role_name():
    odc_env = ODCConfig.get_environment()
    return odc_env.db_username


@pytest.fixture
def multiproduct_name():
    return "s2_ard_granule_nbar_t"
