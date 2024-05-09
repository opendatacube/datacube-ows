# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

"""Run with no DB to simulate connection failure
"""
import os
import sys

src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.append(src_dir)


def reset_global_config():
    from datacube_ows.ows_configuration import OWSConfig
    OWSConfig._instance = None


def no_db(monkeypatch):
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.minimal_cfg.ows_cfg")
    reset_global_config()


def test_db_connect_fail(monkeypatch, flask_client):
    """Start with a database connection"""

    no_db(monkeypatch)
    rv = flask_client.get('/ping')
    assert rv.status_code == 500
    reset_global_config()


def test_wcs_fail(monkeypatch, flask_client):
    """WCS endpoint fails"""

    no_db(monkeypatch)
    rv = flask_client.get('/wcs')
    assert rv.status_code == 400
    reset_global_config()


def test_wms_fail(monkeypatch, flask_client):
    """WMS endpoint fails"""

    no_db(monkeypatch)
    rv = flask_client.get('/wms')
    assert rv.status_code == 400
    reset_global_config()


def test_wmts_fail(monkeypatch, flask_client):
    """WMTS endpoint fails"""

    no_db(monkeypatch)
    rv = flask_client.get('/wmts')
    assert rv.status_code == 400
    reset_global_config()


def test_legend_fail(monkeypatch, flask_client):
    """Fail on legend"""

    no_db(monkeypatch)
    rv = flask_client.get("/legend/layer/style/legend.png")
    assert rv.status_code == 404
    reset_global_config()


def test_index_fail(monkeypatch, flask_client):
    """Base index endpoint fails"""
    # Should actually be 200 TODO
    no_db(monkeypatch)
    rv = flask_client.get('/')
    assert rv.status_code == 500
    reset_global_config()
