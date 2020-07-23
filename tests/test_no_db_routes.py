"""Run with no DB to simulate connection failure
"""

def test_db_connect_fail(flask_client):
    """Start with a database connection"""

    import os
    env = os.environ
    rv = flask_client.get('/ping')
    assert rv.status_code == 500

def test_wcs_fail(flask_client):
    """WCS endpoint fails"""

    rv = flask_client.get('/wcs')
    assert rv.status_code == 400

def test_wms_fail(flask_client):
    """WMS endpoint fails"""

    rv = flask_client.get('/wms')
    assert rv.status_code == 400

def test_wmts_fail(flask_client):
    """WMTS endpoint fails"""

    rv = flask_client.get('/wmts')
    assert rv.status_code == 400

def test_legend_fail(flask_client):
    """Fail on legend"""

    rv = flask_client.get("/legend/layer/style/legend.png")
    assert rv.status_code == 404

def test_index_fail(flask_client):
    """Base index endpoint fails"""

    rv = flask_client.get('/')
    assert rv.status_code == 200