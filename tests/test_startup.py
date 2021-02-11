import pytest

from unittest.mock import patch
import os


def test_fake_creds(monkeypatch):
    from datacube_ows.startup_utils import initialise_aws_credentials
    monkeypatch.setenv("AWS_DEFAULT_REGION", "")
    initialise_aws_credentials()
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-1")
    monkeypatch.setenv("AWS_NO_SIGN_REQUEST", "false")
    with patch("datacube_ows.startup_utils.configure_s3_access") as s3a:
        s3a.return_value = None
        initialise_aws_credentials()
        assert os.getenv("AWS_NO_SIGN_REQUEST") is None
        monkeypatch.setenv("AWS_NO_SIGN_REQUEST", "indubitably")
        initialise_aws_credentials()
        assert os.getenv("AWS_ACCESS_KEY_ID") == "fake"

def test_initialise_logger():
    from datacube_ows.startup_utils import initialise_logger
    log = initialise_logger("tim.the.testlogger")
    assert log is not None
    log.info("Test")

def test_initialise_ign_warn():
    from datacube_ows.startup_utils import initialise_ignorable_warnings
    initialise_ignorable_warnings()

def test_initialise_debugging(monkeypatch):
    monkeypatch.setenv("PYDEV_DEBUG", "")
    from datacube_ows.startup_utils import initialise_debugging
    initialise_debugging()

def test_initialise_sentry(monkeypatch):
    monkeypatch.setenv("SENTRY_KEY", "")
    monkeypatch.setenv("SENTRY_PROJECT", "")
    from datacube_ows.startup_utils import initialise_sentry
    initialise_sentry()
    monkeypatch.setenv("SENTRY_KEY", "dummy_key")
    monkeypatch.setenv("SENTRY_PROJECT", "dummy_project")
    try:
        initialise_sentry()
    except Exception:
        pass

def test_prometheus_inactive(monkeypatch):
    monkeypatch.setenv("prometheus_multiproc_dir", "")
    from datacube_ows.startup_utils import initialise_prometheus_register, initialise_prometheus

def test_supported_version():
    from datacube_ows.protocol_versions import SupportedSvcVersion
    ver = SupportedSvcVersion("wts", "1.2.3", "a", "b")
    assert ver.service == "wts"
    assert ver.service_upper == "WTS"
    assert ver.version == "1.2.3"
    assert ver.version_parts == ["1", "2", "3"]
    assert ver.router == "a"
    assert ver.exception_class == "b"
    from datacube_ows.protocol_versions import supported_versions
    supported = supported_versions()
    assert supported["wms"].versions[0].service == "wms"
