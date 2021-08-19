# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import os
from unittest.mock import MagicMock, patch

import flask
import pytest


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
        monkeypatch.setenv("AWS_NO_SIGN_REQUEST", "yes")
        initialise_aws_credentials()
        assert os.getenv("AWS_ACCESS_KEY_ID") == "fake"

def test_s3_endpoint_default(monkeypatch):
    from datacube_ows.startup_utils import initialise_aws_credentials
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-west-1")
    monkeypatch.setenv("AWS_S3_ENDPOINT", "")
    initialise_aws_credentials()
    assert "AWS_S3_ENDPOINT" not in os.environ

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
    from datacube_ows.startup_utils import (  # noqa: F401
        initialise_prometheus, initialise_prometheus_register)


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


def test_generate_locale_sel():
    app = flask.Flask("test_generate_locale_selector")
    from datacube_ows.startup_utils import generate_locale_selector
    with app.test_request_context(headers={"Accept-Language": "sw, fr;q=0.7, de;q=0.2"}):
        selector = generate_locale_selector(["en", "de", "sw"])
        assert selector() == "sw"


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
    bab = initialise_babel(babel_cfg, flask_app)
    assert bab is not None
    assert bab.default_locale.language == "en"


def test_init_babel_off(babel_cfg, flask_app):
    from datacube_ows.startup_utils import initialise_babel
    babel_cfg.internationalised = False
    bab = initialise_babel(babel_cfg, flask_app)
    assert bab is None

