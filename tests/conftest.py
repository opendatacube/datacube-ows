import pytest

import os
os.environ["DEFER_CFG_PARSE"] = "yes"

from datacube_ows.ogc import app


@pytest.fixture
def flask_client():
    with app.test_client() as client:
        yield client