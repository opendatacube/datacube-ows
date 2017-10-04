
from datacube_wms import wms_wsgi

import pytest
from pytest_localserver.http import WSGIServer
from owslib.wms import WebMapService


@pytest.fixture
def wms_server(request):
    """
    Run the WMS server for the duration of these tests
    """
    server = WSGIServer(application=wms_wsgi.application)
    server.start()
    request.addfinalizer(server.stop)
    return server


def test_wms_server(wms_server):
    # Use owslib to confirm that we have a somewhat compliant WMS service
    wms = WebMapService(url=wms_server.url)

    assert wms.identification.type == "OGC:WMS"

    # Ensure that we have at least some layers available
    contents = list(wms.contents)
    assert contents
