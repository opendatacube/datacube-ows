# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import os
import sys
from unittest.mock import MagicMock, patch

import flask
import pytest


def test_fake_creds(monkeypatch):
    from datacube_ows.startup_utils import (CredentialManager,
                                            initialise_aws_credentials)
    CredentialManager._instance = None
    log = MagicMock()
    monkeypatch.setenv("AWS_DEFAULT_REGION", "")
    initialise_aws_credentials(log=log)
    CredentialManager._instance = None
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-1")
    monkeypatch.setenv("AWS_NO_SIGN_REQUEST", "false")
    monkeypatch.setenv("AWS_REQUEST_PAYER", "requester")
    with patch("datacube_ows.startup_utils.configure_s3_access") as s3a:
        s3a.return_value = None
        initialise_aws_credentials(log=log)
        assert os.getenv("AWS_NO_SIGN_REQUEST") is None
        CredentialManager._instance = None
        monkeypatch.setenv("AWS_NO_SIGN_REQUEST", "yes")
        initialise_aws_credentials()
        assert os.getenv("AWS_ACCESS_KEY_ID") == "fake"


def test_renewable_creds(monkeypatch):
    from datacube_ows.startup_utils import (CredentialManager,
                                            RefreshableCredentials,
                                            initialise_aws_credentials)
    CredentialManager._instance = None
    log = MagicMock()
    monkeypatch.setenv("AWS_DEFAULT_REGION", "")
    initialise_aws_credentials(log=log)
    CredentialManager._instance = None
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-1")
    monkeypatch.setenv("AWS_NO_SIGN_REQUEST", "false")
    monkeypatch.setenv("AWS_REQUEST_PAYER", "requester")
    with patch("datacube_ows.startup_utils.configure_s3_access") as s3a:
        mock_creds = MagicMock(spec=RefreshableCredentials)
        s3a.return_value = mock_creds
        initialise_aws_credentials(log=log)
        CredentialManager.check_cred()
        mock_creds.refresh_needed.return_value = True
        CredentialManager.check_cred()


def test_s3_endpoint_default(monkeypatch):
    from datacube_ows.startup_utils import (CredentialManager,
                                            initialise_aws_credentials)
    CredentialManager._instance = None
    log = MagicMock()
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-1")
    monkeypatch.setenv("AWS_S3_ENDPOINT", "")
    initialise_aws_credentials(log=log)
    assert "AWS_S3_ENDPOINT" not in os.environ

def test_initialise_logger():
    from datacube_ows.startup_utils import initialise_logger
    log = initialise_logger("tim.the.testlogger")
    assert log is not None
    log.info("Test")


def test_initialise_ign_warn():
    from datacube_ows.startup_utils import initialise_ignorable_warnings
    initialise_ignorable_warnings()


def test_initialise_nodebugging(monkeypatch):
    monkeypatch.setenv("PYDEV_DEBUG", "")
    from datacube_ows.startup_utils import initialise_debugging
    initialise_debugging()


def test_initialise_explicit_nodebugging(monkeypatch):
    monkeypatch.setenv("PYDEV_DEBUG", "no")
    from datacube_ows.startup_utils import initialise_debugging
    initialise_debugging()


def test_initialise_debugging(monkeypatch):
    monkeypatch.setenv("PYDEV_DEBUG", "YES")
    from datacube_ows.startup_utils import initialise_debugging
    fake_mod = MagicMock()
    with patch.dict("sys.modules", pydevd_pycharm=fake_mod) as set_trc:
        initialise_debugging()
        fake_mod.settrace.assert_called()


def test_initialise_sentry(monkeypatch):
    monkeypatch.setenv("SENTRY_DSN", "")
    from datacube_ows.startup_utils import initialise_sentry
    initialise_sentry()
    monkeypatch.setenv("SENTRY_DSN", "https://key@sentry.local/projid")
    log = MagicMock()
    try:
        initialise_sentry(log)
    except Exception:
        pass


def test_prometheus_inactive(monkeypatch):
    monkeypatch.setenv("prometheus_multiproc_dir", "")
    from datacube_ows.startup_utils import initialise_prometheus
    initialise_prometheus(None)


def test_supported_version():
    from datacube_ows.protocol_versions import SupportedSvcVersion
    ver = SupportedSvcVersion("wts", "1.2.3", "a", "b")
    assert ver.service == "wts"
    assert ver.service_upper == "WTS"
    assert ver.version == "1.2.3"
    assert ver.version_parts == [1, 2, 3]
    assert ver.router == "a"
    assert ver.exception_class == "b"
    from datacube_ows.protocol_versions import supported_versions
    supported = supported_versions()
    assert supported["wms"].versions[0].service == "wms"


@pytest.fixture
def babel_cfg():
    cfg = MagicMock()
    cfg.internationalised = True
    cfg.locales = ["en", "de"]
    cfg.translations_dir = f"{os.path.dirname(__file__)}/translations"
    cfg.message_domain = "ows_cfg"
    return cfg

@pytest.fixture
def flask_app():
    app = flask.Flask("test_flask_app")
    return app

def test_init_babel_on(babel_cfg, flask_app):
    from datacube_ows.startup_utils import initialise_babel
    with flask_app.app_context():
        bab = initialise_babel(babel_cfg, flask_app)
        assert bab is not None
        assert bab.default_locale.language == "en"


def test_init_babel_off(babel_cfg, flask_app):
    from datacube_ows.startup_utils import initialise_babel
    babel_cfg.internationalised = False
    bab = initialise_babel(babel_cfg, flask_app)
    assert bab is None


def test_sentry_before_send():
    from datacube_ows.startup_utils import before_send

    class LGEOS380():
        def __init__(self, a=5):
            self.a = a

    try:
        string = LGEOS380().GEOSGeom_destroy()
    except Exception:
        hint = {'exc_info': sys.exc_info()}
        assert 'exc_info' in hint
        assert before_send("event", hint) is None
