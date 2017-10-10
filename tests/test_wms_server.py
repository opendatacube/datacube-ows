from datacube_wms import wms

import pytest
from pytest_localserver.http import WSGIServer
from owslib.wms import WebMapService


@pytest.fixture
def wms_server(request):
    """
    Run the WMS server for the duration of these tests
    """
    server = WSGIServer(application=wms.app)
    server.start()
    request.addfinalizer(server.stop)
    return server


def test_wms_server(wms_server):
    # Use owslib to confirm that we have a somewhat compliant WMS service
    wms = WebMapService(url=wms_server.url, version="1.3.0")

    assert wms.identification.type == "WMS"

    # Ensure that we have at least some layers available
    # contents = list(wms.contents)
    # assert contents

