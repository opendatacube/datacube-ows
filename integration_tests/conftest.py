import os
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
