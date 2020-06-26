import pytest
from click.testing import CliRunner

from datacube_ows.ogc import app

@pytest.fixture
def flask_client():
    with app.test_client() as client:
        yield client

@pytest.fixture
def runner():
    return CliRunner()