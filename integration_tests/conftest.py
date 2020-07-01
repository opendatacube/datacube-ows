import os
pytest_plugins = ['helpers_namespace']
import pytest
from click.testing import CliRunner

from datacube_ows import ogc
from pytest_localserver.http import WSGIServer

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
        server = WSGIServer(port='5000', application=ogc.app)
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
        lon_min + 0.2 * lon_range,
        lat_min + 0.2 * lat_range,
        lon_max - 0.2 * lon_range,
        lat_max - 0.2 * lat_range
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
        lat_min - 0.2 * lat_range
    )