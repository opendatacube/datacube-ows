# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import logging
import traceback

from flask import render_template, request
from sqlalchemy.exc import OperationalError

from datacube_ows import __version__
from datacube_ows.http_utils import (
    capture_headers,
    get_service_base_url,
    lower_get_args,
    resp_headers,
)
from datacube_ows.index.api import ows_index
from datacube_ows.legend_generator import create_legend_for_style
from datacube_ows.ogc_exceptions import OGCException, WMSException
from datacube_ows.protocol_versions import supported_versions
from datacube_ows.wcs1 import WCS_REQUESTS
from datacube_ows.wms import WMS_REQUESTS

TYPE_CHECKING = False
if TYPE_CHECKING:
    from logging import Logger

    from datacube_ows.ows_configuration import OWSConfig
    from datacube_ows.protocol_versions import FlaskResponse, SupportedSvc

_LOG: Logger = logging.getLogger(__name__)

# Protocol/Version lookup table
OWS_SUPPORTED: dict[str, SupportedSvc] = supported_versions()


# Flask Routes
# (Note that actual route declarations take place in startup_utils.py)
def ogc_impl(cfg: OWSConfig):
    # pylint: disable=too-many-branches
    nocase_args = capture_headers(request, lower_get_args())
    service = nocase_args.get("service", "").upper()  # type: ignore[union-attr]
    if service:
        return ogc_svc_impl(cfg, service.lower())

    # create dummy env if not exists
    try:
        # service argument is only required (in fact only defined) by OGC for
        # GetCapabilities requests.  As long as we are persisting with a single
        # routing end point for all services, we must derive the service from the request
        # parameter.
        # This is a quick hack to fix #64.  Service and operation routing could be
        # handled more elegantly.
        op = nocase_args.get("request", "").upper()  # type: ignore[union-attr]
        if op in WMS_REQUESTS:
            return ogc_svc_impl(cfg, "wms")
        if op in WCS_REQUESTS:
            return ogc_svc_impl(cfg, "wcs")
        if op:
            # Should we return a WMS or WCS exception if there is no service specified?
            # Defaulting to WMS because that's what we already have.
            raise WMSException(
                "Invalid service and/or request",
                locator="Service and request parameters",
            )
        url = nocase_args.get("Host", nocase_args["url_root"])
        base_url = get_service_base_url(cfg.allowed_urls, url)  # type: ignore[arg-type]
        return (
            render_template(
                "index.html",
                cfg=cfg,
                supported=OWS_SUPPORTED,
                base_url=base_url,
                version=__version__,
            ),
            200,
            resp_headers(cfg, {"Content-Type": "text/html"}),
        )
    except OGCException as e:
        _LOG.error("Handled Error: %s", repr(e.errors))
        return e.exception_response(cfg)
    except Exception as e:  # pylint: disable=broad-except
        _LOG.exception(e)
        ogc_e = WMSException(f"Unexpected server error: {e!s}", http_response=500)
        return ogc_e.exception_response(cfg, traceback=traceback.format_exception(e))


def ogc_svc_impl(cfg: OWSConfig, svc) -> FlaskResponse:
    svc_support = OWS_SUPPORTED.get(svc)
    nocase_args = capture_headers(request, lower_get_args())
    service = nocase_args.get("service", svc).upper()

    # Is service activated in config?
    try:
        if not svc_support:
            raise WMSException(
                f"Invalid service: {svc}",
                valid_keys=[
                    service.service
                    for service in OWS_SUPPORTED.values()
                    if service.activated(cfg)
                ],
                code=WMSException.OPERATION_NOT_SUPPORTED,
                locator="service parameter",
            )
        if not svc_support.activated(cfg):
            raise svc_support.default_exception_class(
                "Invalid service and/or request",
                locator="Service and request parameters",
            )

        # Does service match path (if supplied)
        if service != svc_support.service_upper:
            raise svc_support.default_exception_class(
                "Invalid service", locator="Service parameter"
            )

        version = nocase_args.get("version")
        version_support = svc_support.negotiated_version(version)
    except OGCException as e:
        return e.exception_response(cfg)

    try:
        # FIXME: fix type of nocase_args in protocol_versions.py.
        return version_support.router(cfg, nocase_args)  # type: ignore[arg-type]
    except OGCException as e:
        return e.exception_response(cfg)
    except OperationalError as e:
        # Expected types of failures in this branch. Log the error to console and give
        # the user a generic 500 response.
        _LOG.error(e)
        return version_support.exception_class(
            "Internal server error.", http_response=500
        ).exception_response(cfg)
    except Exception as e:  # pylint: disable=broad-except
        _LOG.error(f"Arguments for unexpected error: {nocase_args}")
        _LOG.exception(e)
        ogc_e = version_support.exception_class(
            f"Unexpected server error: {e!s}", http_response=500
        )
        return ogc_e.exception_response(cfg, traceback=traceback.format_exception(e))


def ogc_wms_impl(cfg: OWSConfig):
    return ogc_svc_impl(cfg, "wms")


def ogc_wmts_impl(cfg: OWSConfig):
    return ogc_svc_impl(cfg, "wmts")


def ogc_wcs_impl(cfg: OWSConfig):
    return ogc_svc_impl(cfg, "wcs")


def ping(cfg: OWSConfig) -> tuple[str, int, dict[str, str]]:
    dbs_ok = {
        name: ows_index(dc).check_db_access(dc) for name, dc in cfg.all_dcs.items()
    }

    if all(dbs_ok.values()):
        return (
            render_template("ping.html", status="Up", statuses=dbs_ok),
            200,
            resp_headers(cfg, {"Content-Type": "text/html"}),
        )
    if any(dbs_ok.values()):
        return (
            render_template("ping.html", status="Partially Up", statuses=dbs_ok),
            503,
            resp_headers(cfg, {"Content-Type": "text/html"}),
        )
    return (
        render_template("ping.html", status="Down", statuses=dbs_ok),
        503,
        resp_headers(cfg, {"Content-Type": "text/html"}),
    )


def legend(
    cfg: OWSConfig, layer, style, dates=None
) -> tuple[str | bytes, int, dict[str, str]]:
    product = cfg.layer_index.get(layer)
    if not product:
        return "Unknown Layer", 404, resp_headers(cfg, {"Content-Type": "text/plain"})
    ndates = int(lower_get_args().get("ndates", 0)) if dates is None else len(dates)  # type: ignore[arg-type]
    try:
        img = create_legend_for_style(cfg, product, style, ndates)
    except WMSException as e:
        return (
            str(e),
            e.http_response,
            resp_headers(cfg, {"Content-Type": "text/plain"}),
        )

    if not img:
        return "Unknown Style", 404, resp_headers(cfg, {"Content-Type": "text/plain"})
    return img
