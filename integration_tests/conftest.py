# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import os

import pytest
from click.testing import CliRunner
from datacube.cfg import ODCConfig
from pytest_localserver.http import WSGIServer

from datacube_ows.startup_utils import create_app

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Generator

    from flask import Flask


@pytest.fixture(scope="session")
def flask_app() -> Generator[Flask]:
    app = create_app()
    yield app


@pytest.fixture
def flask_client(flask_app) -> Generator[WSGIServer]:
    with flask_app.test_client() as client:
        yield client


class generic_obj:
    def __init__(self, url: str) -> None:
        self.url = url


@pytest.fixture(scope="session")
def ows_server(request, flask_app) -> WSGIServer:
    """
    Run the OWS server for the duration of these tests
    """
    external_url = os.environ.get("SERVER_URL")
    if external_url:
        server = generic_obj(external_url)
    else:
        server = WSGIServer(port="5000", application=flask_app)
        server.start()
        request.addfinalizer(server.stop)

    return server


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def layer_name() -> str:
    return "s2_l2a"


@pytest.fixture
def postgis_layer_name() -> str:
    return "s2_l2a_postgis"


@pytest.fixture
def write_role_name() -> str:
    odc_env = ODCConfig.get_environment()
    return odc_env.db_username


@pytest.fixture
def read_role_name(write_role_name: str) -> str:
    if read_role_name := os.environ.get("SERVER_DB_USERNAME"):
        return read_role_name
    return write_role_name


@pytest.fixture
def multiproduct_name() -> str:
    return "s2_ard_granule_nbar_t"
