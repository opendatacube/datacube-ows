# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import logging
import os
import warnings
from collections.abc import Callable
from logging import Logger
from time import monotonic
from typing import Any, TypeVar

from botocore.credentials import RefreshableCredentials
from datacube.utils.aws import configure_s3_access
from flask import Flask, g, request
from rasterio.errors import NotGeoreferencedWarning

from datacube_ows.ows_configuration import OWSConfig, get_config

__all__ = [
    "initialise_babel",
    "initialise_logger",
    "initialise_ignorable_warnings",
    "initialise_debugging",
    "initialise_sentry",
    "initialise_aws_credentials",
    "parse_config_file",
    "initialise_flask",
    "initialise_prometheus",
    "CredentialManager",
    "create_app",
]


def initialise_logger(name: str | None = None) -> Logger:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    log = logging.getLogger(name)
    log.addHandler(handler)
    # If invoked using Gunicorn, link our root logger to the gunicorn logger
    # this will mean the root logs will be captured and managed by the gunicorn logger
    # allowing you to set the gunicorn log directories and levels for logs
    # produced by this application
    log.setLevel(logging.getLogger("gunicorn.error").getEffectiveLevel())
    return log


def initialise_ignorable_warnings() -> None:
    # Suppress annoying rasterio warning message every time we write to a non-georeferenced image format
    warnings.simplefilter("ignore", category=NotGeoreferencedWarning)


def initialise_debugging(log: Logger | None = None) -> None:
    # PYCHARM Debugging
    dbg = os.environ.get("PYDEV_DEBUG")
    if dbg and dbg.lower() not in ("no", "false", "f", "n"):
        import pydevd_pycharm

        pydevd_pycharm.settrace(
            "172.17.0.1", port=12321, stdout_to_server=True, stderr_to_server=True
        )
        if log:
            log.info("PyCharm Debugging enabled")


SentryEvent = TypeVar("SentryEvent")


def before_send(event: SentryEvent, hint: dict[str, Any]) -> SentryEvent | None:
    if "exc_info" in hint:
        _, exc_value, _ = hint["exc_info"]
        if isinstance(
            exc_value, AttributeError
        ) and "object has no attribute 'GEOSGeom_destroy'" in str(exc_value):
            return None
    return event


def initialise_sentry(log: Logger | None = None) -> None:
    if os.environ.get("SENTRY_DSN"):
        import sentry_sdk
        from sentry_sdk.integrations.flask import FlaskIntegration

        SENTRY_ENV_TAG = (
            os.environ.get("SENTRY_ENV_TAG")
            if os.environ.get("SENTRY_ENV_TAG")
            else "dev"
        )
        sentry_sdk.init(
            dsn=os.environ["SENTRY_DSN"],
            environment=SENTRY_ENV_TAG,
            integrations=[FlaskIntegration()],
            before_send=before_send,
        )
        if log:
            log.info("Sentry initialised")


class CredentialManager:
    _instance = None

    def __new__(cls, log: Logger | None = None) -> "CredentialManager":
        if not cls._instance:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, log: Logger | None = None) -> None:
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
                    log.warning(
                        "AWS_NO_SIGN_REQUEST is not set. "
                        + "The default behaviour has recently changed to False (i.e. signed requests) "
                        + "Please explicitly set $AWS_NO_SIGN_REQUEST to 'no' for unsigned requests."
                    )
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
                "Environment variable $AWS_DEFAULT_REGION not set.  (This warning can be ignored if all data is stored locally.)"
            )

    def _check_cred(self) -> None:
        if self.credentials and isinstance(self.credentials, RefreshableCredentials):
            if self.credentials.refresh_needed():
                self.renew_creds()
            elif self.log:
                # pylint: disable=protected-access
                self.log.info(
                    "Credentials look OK: %s seconds remaining",
                    str(self.credentials._seconds_remaining()),
                )
        elif self.log:
            self.log.debug(
                "Credentials of type %s - NOT RENEWING",
                self.credentials.__class__.__name__,
            )

    @classmethod
    def check_cred(cls) -> None:
        # pylint: disable=protected-access
        assert cls._instance is not None
        cls._instance._check_cred()

    def renew_creds(self) -> None:
        if self.use_aws:
            if self.log:
                self.log.info("Establishing/renewing credentials")
            self.credentials = configure_s3_access(
                aws_unsigned=self.unsigned, requester_pays=self.requester_pays
            )
            if self.log and isinstance(self.credentials, RefreshableCredentials):
                # pylint: disable=protected-access
                self.log.debug(
                    "%s seconds remaining", str(self.credentials._seconds_remaining())
                )


def initialise_aws_credentials(log: Logger | None = None) -> None:
    # pylint: disable=protected-access
    if CredentialManager._instance is None:
        _ = CredentialManager(log)


def parse_config_file(log: Logger | None = None) -> OWSConfig | None:
    # Cache a parsed config file object
    # (unless deferring to first request)
    cfg = None
    if not os.environ.get("DEFER_CFG_PARSE"):
        cfg = get_config()
    return cfg


def initialise_flask(name: str) -> Flask:
    app_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return Flask(
        name.split(".")[0], template_folder=os.path.join(app_path, "templates")
    )


def pass_through(undecorated: Callable) -> Callable:
    def decorator(*args, **kwargs):
        return undecorated(*args, **kwargs)

    decorator.__name__ = undecorated.__name__
    return decorator


class FakeMetrics:
    def do_not_track(self) -> Callable:
        return pass_through

    def counter(self, *args, **kwargs) -> Callable:
        return pass_through

    def histogram(self, *args, **kwargs) -> Callable:
        return pass_through

    def gauge(self, *args, **kwargs) -> Callable:
        return pass_through

    def summary(self, *args, **kwargs) -> Callable:
        return pass_through


def initialise_prometheus(app: Flask, log: Logger | None = None):
    # Prometheus
    if os.environ.get("PROMETHEUS_MULTIPROC_DIR", False):
        from prometheus_flask_exporter.multiprocess import (
            GunicornInternalPrometheusMetrics,
        )

        metrics = GunicornInternalPrometheusMetrics(app, group_by="endpoint")
        if log:
            log.info("Prometheus metrics enabled")
        return metrics
    return FakeMetrics()


def proxy_fix(app: Flask, log: Logger | None = None):
    # Proxy Fix, to respect X-Forwarded-For headers
    if os.environ.get("PROXY_FIX", False):
        from werkzeug.middleware.proxy_fix import ProxyFix

        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_port=1)  # type: ignore[method-assign]
        if log is not None:
            log.info("ProxyFix was enabled")
    return app


def request_extractor() -> str | None:
    return request.args.get("request")


def initialise_babel(cfg, app: Flask) -> object | None:
    if cfg and cfg.internationalised:
        from flask_babel import Babel

        app.config["BABEL_TRANSLATION_DIRECTORIES"] = cfg.translations_dir

        def get_locale() -> str | None:
            return request.accept_languages.best_match(
                cfg.locales, default=cfg.locales[0]
            )

        return Babel(
            app,
            locale_selector=get_locale,
            default_domain=cfg.message_domain,
            configure_jinja=False,
        )
    return None


def create_app() -> Flask:
    log = initialise_logger()
    cfg = parse_config_file(log)
    initialise_ignorable_warnings()
    initialise_debugging(log)
    initialise_sentry(log)
    initialise_aws_credentials(log)
    app = initialise_flask(__name__)
    initialise_babel(cfg, app)
    metrics = initialise_prometheus(app, log)
    ows_ogc_metric = metrics.histogram(
        "ows_ogc",
        "Summary by OGC request protocol, version, operation, layer, and HTTP Status",
        labels={
            "query_request": lambda: request.args.get("request", "NONE").upper(),
            "query_service": lambda: request.args.get("service", "NONE").upper(),
            "query_version": lambda: request.args.get("version"),
            "query_layer": lambda: (
                request.args.get("query_layers")  # WMS GetFeatureInfo
                or request.args.get("layers")  # WMS
                or request.args.get("layer")  # WMTS
                or request.args.get("coverage")  # WCS 1.x
                or request.args.get("coverageid")  # WCS 2.x
            ),
            "status": lambda r: r.status_code,
        },
    )
    proxy_fix(app, log)

    # Declare routes
    from datacube_ows.ogc import (
        legend,
        ogc_impl,
        ogc_wcs_impl,
        ogc_wms_impl,
        ogc_wmts_impl,
        ping,
    )

    @app.route("/")
    @ows_ogc_metric
    def main_route():
        return ogc_impl()

    @app.route("/wms")
    @ows_ogc_metric
    def wms_route():
        return ogc_wms_impl()

    @app.route("/wmts")
    @ows_ogc_metric
    def wmts_route():
        return ogc_wmts_impl()

    @app.route("/wcs")
    @ows_ogc_metric
    def wcs_route():
        return ogc_wcs_impl()

    @app.route("/ping")
    @metrics.summary(
        "ows_heartbeat_pings", "Ping durations", labels={"status": lambda r: r.status}
    )
    def ping_route():
        return ping()

    @app.route("/legend/<string:layer>/<string:style>/legend.png")
    @metrics.histogram(
        "ows_legends",
        "Legend query durations",
        labels={
            "layer": lambda: request.path.split("/")[2],
            "style": lambda: request.path.split("/")[3],
            "status": lambda r: r.status,
        },
    )
    def legend_route(layer, style):
        return legend(layer, style)

    # Configure Flask Middleware
    @app.before_request
    def start_timer() -> None:
        # pylint: disable=assigning-non-slot
        g.ogc_start_time = monotonic()

    @app.after_request
    def log_time_and_request_response(response):
        time_taken = int((monotonic() - g.ogc_start_time) * 1000)
        # request.environ.get('HTTP_X_REAL_IP') captures requester ip on a local docker container via gunicorn
        if request.environ.get("HTTP_X_REAL_IP"):
            ip = request.environ.get("HTTP_X_REAL_IP")
        # request.environ.get('HTTP_X_FORWARDED_FOR') captures request IP forwarded by ingress/loadbalancer
        elif request.environ.get("HTTP_X_FORWARDED_FOR"):
            ip = request.environ.get("HTTP_X_FORWARDED_FOR")
        # request.environ.get('REMOTE_ADDR') is standard internal IP address
        elif request.environ.get("REMOTE_ADDR"):
            ip = request.environ.get("REMOTE_ADDR")
        else:
            ip = "Not found"
        log.info(
            "ip: %s request: %s returned status: %d and took: %d ms",
            ip,
            request.url,
            response.status_code,
            time_taken,
        )
        return response

    return app
