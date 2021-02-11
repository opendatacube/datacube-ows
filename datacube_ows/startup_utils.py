from __future__ import absolute_import, division, print_function
import warnings
import sentry_sdk
from rasterio.errors import NotGeoreferencedWarning
from sentry_sdk.integrations.flask import FlaskIntegration
from prometheus_flask_exporter.multiprocess import GunicornInternalPrometheusMetrics

from flask import Flask, request
from flask_log_request_id import RequestID, RequestIDLogFilter
import os

from datacube.utils.aws import configure_s3_access
from datacube_ows.ows_configuration import get_config

import logging

__all__ = [
    'initialise_logger',
    'initialise_ignorable_warnings',
    'initialise_debugging',
    'initialise_sentry',
    'initialise_aws_credentials',
    'parse_config_file',
    'initialise_flask',
    'initialise_prometheus',
    'initialise_prometheus_register',
]

def initialise_logger(name=None):
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] %(name)s [%(request_id)s] [%(levelname)s] %(message)s"))
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

def initialise_sentry(log=None):
    if os.environ.get("SENTRY_KEY") and os.environ.get("SENTRY_PROJECT"):
        sentry_sdk.init(
            dsn="https://%s@sentry.io/%s" % (os.environ["SENTRY_KEY"], os.environ["SENTRY_PROJECT"]),
            integrations = [FlaskIntegration()]
        )
        if log:
            log.info("Sentry initialised")

def initialise_aws_credentials(log=None):
    # Startup initialisation of libraries controlled by environment variables
    #
    # Move to a function to facilitate unit testing.
    # Should be done in a more flexible pluggable way.

    # Boto3/AWS
    if os.environ.get("AWS_DEFAULT_REGION"):
        env_nosign = os.environ.get("AWS_NO_SIGN_REQUEST", "yes")
        unsigned = bool(env_nosign)
        if not unsigned or env_nosign.lower() in ("n", "f", "no", "false", "0"):
            unsigned = False
            # delete env variable
            del os.environ["AWS_NO_SIGN_REQUEST"]
        else:
            # Workaround for rasterio bug
            os.environ["AWS_ACCESS_KEY_ID"] = "fake"
            os.environ["AWS_SECRET_ACCESS_KEY"] = "fake"
        env_requester_pays = os.environ.get("AWS_REQUEST_PAYER", "")
        requester_pays = False
        if env_requester_pays.lower() == "requester":
            requester_pays = True
        if log:
            if unsigned:
                log.info("S3 access configured with unsigned requests")
            else:
                log.info("S3 access configured with signed requests")
        credentials = configure_s3_access(aws_unsigned=unsigned, requester_pays=requester_pays)
    elif log:
        log.warning("Environment variable $AWS_DEFAULT_REGION not set.  (This warning can be ignored if all data is stored locally.)")

def parse_config_file(log=None):
    # Cache a parsed config file object
    # (unless deferring to first request)
    if not os.environ.get("DEFER_CFG_PARSE"):
        get_config()

def initialise_flask(name):
    app = Flask(name.split('.')[0])
    RequestID(app)
    return app

def initialise_prometheus(app, log=None):
    # Prometheus
    if os.environ.get("prometheus_multiproc_dir", False):
        metrics = GunicornInternalPrometheusMetrics(app)
        if log:
            log.info("Prometheus metrics enabled")
        return metrics
    return None

def initialise_prometheus_register(metrics):
    # Register routes with Prometheus - call after all routes set up.
    if os.environ.get("prometheus_multiproc_dir", False):
        metrics.register_default(
            metrics.summary(
                'flask_ows_request_full_url', 'Request summary by request url',
                labels={
                    'query_request': lambda: request.args.get('request'),
                    'query_service': lambda: request.args.get('service'),
                    'query_layers': lambda: request.args.get('layers'),
                    'query_url': lambda: request.full_path
                }
            )
        )
