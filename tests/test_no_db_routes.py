"""Run with no DB to simulate connection failure
"""
import pytest
import os
import sys

src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if src_dir not in sys.path:
    sys.path.append(src_dir)


def test_db_connect_fail(flask_client):
    """Start with a database connection"""

    import os
    env = os.environ
    rv = flask_client.get('/ping')
    assert rv.status_code == 500

def test_wcs_fail(monkeypatch, flask_client):
    """WCS endpoint fails"""

    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.minimal_cfg.ows_cfg")
    rv = flask_client.get('/wcs')
    assert rv.status_code == 400

def test_wms_fail(monkeypatch, flask_client):
    """WMS endpoint fails"""

    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.minimal_cfg.ows_cfg")
    rv = flask_client.get('/wms')
    assert rv.status_code == 400

def test_wmts_fail(monkeypatch, flask_client):
    """WMTS endpoint fails"""

    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.minimal_cfg.ows_cfg")
    rv = flask_client.get('/wmts')
    assert rv.status_code == 400

def test_legend_fail(monkeypatch, flask_client):
    """Fail on legend"""

    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.minimal_cfg.ows_cfg")
    rv = flask_client.get("/legend/layer/style/legend.png")
    assert rv.status_code == 404

def test_index_fail(monkeypatch, flask_client):
    """Base index endpoint fails"""

    monkeypatch.setenv("DATACUBE_OWS_CFG", "tests.cfg.minimal_cfg.ows_cfg")
    rv = flask_client.get('/')
    assert rv.status_code == 200