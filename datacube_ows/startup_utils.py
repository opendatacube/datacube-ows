# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import absolute_import, division, print_function

import logging
import os
import warnings

from botocore.credentials import RefreshableCredentials
from datacube.utils.aws import configure_s3_access
from flask import Flask, request
from flask_log_request_id import RequestID, RequestIDLogFilter
from rasterio.errors import NotGeoreferencedWarning

from datacube_ows.ows_configuration import get_config

__all__ = [
    'initialise_babel',
    'initialise_logger',
    'initialise_ignorable_warnings',
    'initialise_debugging',
    'initialise_sentry',
    'initialise_aws_credentials',
    'parse_config_file',
    'initialise_flask',
    'initialise_prometheus',
    'generate_locale_selector',
    'CredentialManager',
]

def initialise_logger(name=None):
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter('[%(asctime)s] [%(levelname)s] %(message)s'))
    handler.addFilter(RequestIDLogFilter())
    _LOG = logging.getLogger(name)
    _LOG.addHandler(handler)
    # If invoked using Gunicorn, link our root logger to the gunicorn logger
    # this will mean the root logs will be captured and managed by the gunicorn logger
    # allowing you to set the gunicorn log directories and levels for logs
    # produced by this application
    _LOG.setLevel(logging.getLogger('gunicorn.error').getEffectiveLevel())
    return _LOG


def initialise_ignorable_warnings():
    # Suppress annoying rasterio warning message every time we write to a non-georeferenced image format
    warnings.simplefilter("ignore", category=NotGeoreferencedWarning)


def initialise_debugging(log=None):
    # PYCHARM Debugging
    if os.environ.get("PYDEV_DEBUG"):
        import pydevd_pycharm
        pydevd_pycharm.settrace('172.17.0.1', port=12321, stdoutToServer=True, stderrToServer=True)
        if log:
            log.info("PyCharm Debugging enabled")

def before_send(event, hint):
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']
        if isinstance(exc_value, AttributeError) and "object has no attribute 'GEOSGeom_destroy'" in str(exc_value):
            return None
    return event

def initialise_sentry(log=None):
    if os.environ.get("SENTRY_DSN"):
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration
        SENTRY_ENV_TAG = os.environ.get("SENTRY_ENV_TAG") if os.environ.get("SENTRY_ENV_TAG") else "dev"
        sentry_sdk.init(
            dsn=os.environ["SENTRY_DSN"],
            environment=SENTRY_ENV_TAG,
            integrations = [FlaskIntegration()],
            before_send=before_send,
        )
        if log:
            log.info("Sentry initialised")

class CredentialManager:
    _instance = None

    def __new__(cls, log=None):
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log=None):
        # Startup initialisation of libraries controlled by environment variables
        self.use_aws = False
        self.unsigned = False
        self.requester_pays = False
        self.credentials = None
        self.log = log

        if log:
            log.debug("Initialising CredentialManager")

        # Boto3/AWS
        if os.environ.get("AWS_DEFAULT_REGION") or os.environ.get("AWS_REGION"):
            if "AWS_NO_SIGN_REQUEST" in os.environ:
                env_nosign = os.environ["AWS_NO_SIGN_REQUEST"]
                if env_nosign.lower() in ("y", "t", "yes", "true", "1"):
                    unsigned = True
                    # Workaround for rasterio bug
                    os.environ["AWS_NO_SIGN_REQUEST"] = "yes"
                    os.environ["AWS_ACCESS_KEY_ID"] = "fake"
                    os.environ["AWS_SECRET_ACCESS_KEY"] = "fake"
                else:
                    unsigned = False
                    # delete env variable
                    del os.environ["AWS_NO_SIGN_REQUEST"]
            else:
                unsigned = False
                if log:
                    log.warning("AWS_NO_SIGN_REQUEST is not set. " +
                                "The default behaviour has recently changed to False (i.e. signed requests) " +
                                "Please explicitly set $AWS_NO_SIGN_REQUEST to 'no' for unsigned requests.")
            env_requester_pays = os.environ.get("AWS_REQUEST_PAYER", "")
            requester_pays = False
            if env_requester_pays.lower() == "requester":
                requester_pays = True
            self.use_aws = True
            if log:
                if unsigned:
                    log.info("S3 access configured with unsigned requests")
                else:
                    log.info("S3 access configured with signed requests")
            self.unsigned = unsigned
            self.requester_pays = requester_pays
            self.renew_creds()

            if "AWS_S3_ENDPOINT" in os.environ and os.environ["AWS_S3_ENDPOINT"] == "":
                del os.environ["AWS_S3_ENDPOINT"]
        elif log:
            log.warning(
                "Environment variable $AWS_DEFAULT_REGION not set.  (This warning can be ignored if all data is stored locally.)")

    def _check_cred(self):
        if self.credentials and isinstance(self.credentials, RefreshableCredentials):
            if self.credentials.refresh_needed():
                self.renew_creds()
            elif self.log:
                # pylint: disable=protected-access
                self.log.info("Credentials look OK: %s seconds remaining", str(self.credentials._seconds_remaining()))
        elif self.log:
            self.log.debug("Credentials of type %s - NOT RENEWING", self.credentials.__class__.__name__)

    @classmethod
    def check_cred(cls):
        # pylint: disable=protected-access
        cls._instance._check_cred()

    def renew_creds(self):
        if self.use_aws:
            if self.log:
                self.log.info("Establishing/renewing credentials")
            self.credentials = configure_s3_access(aws_unsigned=self.unsigned,
                                                            requester_pays=self.requester_pays)
            if self.log:
                if isinstance(self.credentials, RefreshableCredentials):
                    # pylint: disable=protected-access
                    self.log.debug("%s seconds remaining", str(self.credentials._seconds_remaining()))


def initialise_aws_credentials(log=None):
    # pylint: disable=protected-access
    if CredentialManager._instance is None:
        cm = CredentialManager(log)


def parse_config_file(log=None):
    # Cache a parsed config file object
    # (unless deferring to first request)
    cfg = None
    if not os.environ.get("DEFER_CFG_PARSE"):
        cfg = get_config()
    return cfg


def initialise_flask(name):
    app = Flask(name.split('.')[0])
    RequestID(app)
    return app

def pass_through(undecorated):
    def decorator(*args, **kwargs):
        return undecorated(*args, **kwargs)
    decorator.__name__ = undecorated.__name__
    return decorator

class FakeMetrics:
    def do_not_track(self):
        return pass_through
    def counter(self, *args, **kwargs):
        return pass_through
    def histogram(self, *args, **kwargs):
        return pass_through
    def gauge(self, *args, **kwargs):
        return pass_through
    def summary(self, *args, **kwargs):
        return pass_through

def initialise_prometheus(app, log=None):
    # Prometheus
    if os.environ.get("prometheus_multiproc_dir", False):
        from prometheus_flask_exporter.multiprocess import \
            GunicornInternalPrometheusMetrics
        metrics = GunicornInternalPrometheusMetrics(app)
        if log:
            log.info("Prometheus metrics enabled")
        return metrics
    return FakeMetrics()

def request_extractor():
    qreq = request.args.get('request')
    return qreq

def generate_locale_selector(locales):
    def selector_template():
        return request.accept_languages.best_match(locales)
    return selector_template

def initialise_babel(cfg, app):
    if cfg and cfg.internationalised:
        from flask_babel import Babel
        app.config["BABEL_TRANSLATION_DIRECTORIES"] = cfg.translations_dir
        babel = Babel(app,
                      default_locale=cfg.locales[0],
                      default_domain=cfg.message_domain,
                      configure_jinja=False
                      )
        babel.localeselector(generate_locale_selector(cfg.locales))
        return babel
    else:
        return None
