# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

"""Run with no DB to simulate connection failure
"""
import os
import sys
import pytest

src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.append(src_dir)


def reset_global_config():
    from datacube_ows.ows_configuration import OWSConfig
    OWSConfig._instance = None


@pytest.fixture
def no_db(monkeypatch):
    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.minimal_cfg.ows_cfg")
    reset_global_config()
    yield
    reset_global_config()


def test_db_connect_fail(no_db, flask_client):
    """Start with a database connection"""
    rv = flask_client.get('/ping')
    assert rv.status_code == 500


def test_wcs_fail(no_db, flask_client):
    """WCS endpoint fails"""
    rv = flask_client.get('/wcs')
    assert rv.status_code == 400


def test_wms_fail(no_db, flask_client):
    """WMS endpoint fails"""
    rv = flask_client.get('/wms')
    assert rv.status_code == 400


def test_wmts_fail(no_db, flask_client):
    """WMTS endpoint fails"""
    rv = flask_client.get('/wmts')
    assert rv.status_code == 400


def test_legend_fail(no_db, flask_client):
    """Fail on legend"""
    rv = flask_client.get("/legend/layer/style/legend.png")
    assert rv.status_code == 404


def test_index_fail(no_db, flask_client):
    """Base index endpoint fails"""
    # Should actually be 200 TODO
    rv = flask_client.get('/')
    assert rv.status_code == 500
