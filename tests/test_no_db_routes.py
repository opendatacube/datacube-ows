# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
"""Run with no DB to simulate connection failure
"""
import os
import sys

src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.append(src_dir)


def no_db(monkeypatch):
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.minimal_cfg.ows_cfg")
    monkeypatch.setenv("DB_USERNAME", "fakeuser")
    monkeypatch.setenv("DB_PASSWORD", "password")
    monkeypatch.setenv("DB_HOSTNAME", "localhost")
    from datacube_ows.ows_configuration import get_config
    cfg = get_config(refresh=True)


def test_db_connect_fail(monkeypatch, flask_client):
    """Start with a database connection"""

    no_db(monkeypatch)
    rv = flask_client.get('/ping')
    assert rv.status_code == 500


def test_wcs_fail(monkeypatch, flask_client):
    """WCS endpoint fails"""

    no_db(monkeypatch)
    rv = flask_client.get('/wcs')
    assert rv.status_code == 400


def test_wms_fail(monkeypatch, flask_client):
    """WMS endpoint fails"""

    no_db(monkeypatch)
    rv = flask_client.get('/wms')
    assert rv.status_code == 400


def test_wmts_fail(monkeypatch, flask_client):
    """WMTS endpoint fails"""

    no_db(monkeypatch)
    rv = flask_client.get('/wmts')
    assert rv.status_code == 400


def test_legend_fail(monkeypatch, flask_client):
    """Fail on legend"""

    no_db(monkeypatch)
    rv = flask_client.get("/legend/layer/style/legend.png")
    assert rv.status_code == 404


def test_index_fail(monkeypatch, flask_client):
    """Base index endpoint fails"""
    # Should actually be 200 TODO
    no_db(monkeypatch)
    rv = flask_client.get('/')
    assert rv.status_code == 500
