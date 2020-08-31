import pytest

from unittest.mock import patch
import os

def test_fake_creds(monkeypatch):
    from datacube_ows.ogc import ows_init_libs
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-1")
    monkeypatch.setenv("AWS_NO_SIGN_REQUEST", "false")
    with patch("datacube_ows.ogc.configure_s3_access") as s3a:
        s3a.return_value = None
        ows_init_libs()
        assert os.getenv("AWS_NO_SIGN_REQUEST") == "NO"
        monkeypatch.setenv("AWS_NO_SIGN_REQUEST", "indubitably")
        ows_init_libs()
        assert os.getenv("AWS_ACCESS_KEY_ID") == "fake"
