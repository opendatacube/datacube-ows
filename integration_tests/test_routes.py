# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

"""Run with DB to simulate actual function
"""


def test_db_connect_success(flask_client) -> None:
    """Start with a database connection"""

    rv = flask_client.get("/ping")
    assert rv.status_code == 200


def test_wcs_base(flask_client) -> None:
    """WCS endpoint base"""

    rv = flask_client.get("/wcs")
    assert rv.status_code == 400


def test_wms_base(flask_client) -> None:
    """WMS endpoint base"""

    rv = flask_client.get("/wms")
    assert rv.status_code == 400


def test_wmts_base(flask_client) -> None:
    """WMTS endpoint base"""

    rv = flask_client.get("/wmts")
    assert rv.status_code == 400


def test_legend_default(flask_client) -> None:
    """No-param on legend"""

    rv = flask_client.get("/legend/layer/style/legend.png")
    assert rv.status_code == 404


def test_index(flask_client) -> None:
    """Base index endpoint"""

    rv = flask_client.get("/")
    assert rv.status_code == 200
