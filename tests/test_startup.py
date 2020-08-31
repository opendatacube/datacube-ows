import pytest
import os

def test_fake_creds(monkeypatch):
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-1")
    monkeypatch.setenv("AWS_NO_SIGN_REQUEST", "false")
    from datacube_ows.ogc import ows_init_libs
    try:
        ows_init_libs()
    except ValueError:
        pass
    assert os.getenv("AWS_NO_SIGN_REQUEST") == "NO"
    monkeypatch.setenv("AWS_NO_SIGN_REQUEST", "indubitably")
    ows_init_libs()
    assert os.getenv("AWS_ACCESS_KEY_ID") == "fake"
