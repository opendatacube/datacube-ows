import os
import pytest

from datacube_ows import ogc
from pytest_localserver.http import WSGIServer

from datacube_ows.ogc import app

@pytest.fixture
def flask_client():
    with app.test_client() as client:
        yield client


class generic_obj(object):
    pass

@pytest.fixture
def ows_server(request):
    """
    Run the WMS server for the duration of these tests
    """
    external_url = os.environ.get("SERVER_URL")
    if external_url:
        server = generic_obj()
        server.url = external_url
    else:
        server = WSGIServer(application=ogc.app)
        server.start()
        request.addfinalizer(server.stop)

    return server