# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import logging
import sys
import traceback
from logging import Logger

from flask import render_template, request

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
from datacube_ows.ows_configuration import get_config
from datacube_ows.protocol_versions import SupportedSvc, supported_versions
from datacube_ows.wcs1 import WCS_REQUESTS
from datacube_ows.wms import WMS_REQUESTS

_LOG: Logger = logging.getLogger(__name__)

# Protocol/Version lookup table
OWS_SUPPORTED: dict[str, SupportedSvc] = supported_versions()


# Flask Routes
# (Note that actual route declarations take place in startup_utils.py)
def ogc_impl():
    # pylint: disable=too-many-branches
    nocase_args = lower_get_args()
    nocase_args = capture_headers(request, nocase_args)
    service = nocase_args.get("service", "").upper()

    if service:
        return ogc_svc_impl(service.lower())

    # create dummy env if not exists
    try:
        # service argument is only required (in fact only defined) by OGC for
        # GetCapabilities requests.  As long as we are persisting with a single
        # routing end point for all services, we must derive the service from the request
        # parameter.
        # This is a quick hack to fix #64.  Service and operation routing could be
        # handled more elegantly.
        op = nocase_args.get("request", "").upper()
        if op in WMS_REQUESTS:
            return ogc_svc_impl("wms")
        if op in WCS_REQUESTS:
            return ogc_svc_impl("wcs")
        if op:
            # Should we return a WMS or WCS exception if there is no service specified?
            # Defaulting to WMS because that's what we already have.
            raise WMSException(
                "Invalid service and/or request",
                locator="Service and request parameters",
            )
        cfg = get_config()  # pylint: disable=redefined-outer-name
        url = nocase_args.get("Host", nocase_args["url_root"])
        base_url = get_service_base_url(cfg.allowed_urls, url)
        return (
            render_template(
                "index.html",
                cfg=cfg,
                supported=OWS_SUPPORTED,
                base_url=base_url,
                version=__version__,
            ),
            200,
            resp_headers({"Content-Type": "text/html"}),
        )
    except OGCException as e:
        _LOG.error("Handled Error: %s", repr(e.errors))
        return e.exception_response()
    except Exception as e:  # pylint: disable=broad-except
        _LOG.exception(e)
        tb = sys.exc_info()[2]
        ogc_e = WMSException(f"Unexpected server error: {e!s}", http_response=500)
        return ogc_e.exception_response(traceback=traceback.extract_tb(tb))


def ogc_svc_impl(svc):
    svc_support = OWS_SUPPORTED.get(svc)
    nocase_args = lower_get_args()
    nocase_args = capture_headers(request, nocase_args)
    service = nocase_args.get("service", svc).upper()

    # Is service activated in config?
    try:
        if not svc_support:
            raise WMSException(
                f"Invalid service: {svc}",
                valid_keys=[
                    service.service
                    for service in OWS_SUPPORTED.values()
                    if service.activated()
                ],
                code=WMSException.OPERATION_NOT_SUPPORTED,
                locator="service parameter",
            )
        if not svc_support.activated():
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
        return e.exception_response()

    try:
        return version_support.router(nocase_args)
    except OGCException as e:
        return e.exception_response()
    except Exception as e:  # pylint: disable=broad-except
        _LOG.exception(e)
        tb = sys.exc_info()[2]
        ogc_e = version_support.exception_class(
            f"Unexpected server error: {e!s}", http_response=500
        )
        return ogc_e.exception_response(traceback=traceback.extract_tb(tb))


def ogc_wms_impl():
    return ogc_svc_impl("wms")


def ogc_wmts_impl():
    return ogc_svc_impl("wmts")


def ogc_wcs_impl():
    return ogc_svc_impl("wcs")


def ping() -> tuple[str, int, dict[str, str]]:
    dbs_ok = {
        name: ows_index(dc).check_db_access(dc)
        for name, dc in get_config().all_dcs.items()
    }

    if all(dbs_ok.values()):
        return (
            render_template("ping.html", status="Up", statuses=dbs_ok),
            200,
            resp_headers({"Content-Type": "text/html"}),
        )
    if any(dbs_ok.values()):
        return (
            render_template("ping.html", status="Partially Up", statuses=dbs_ok),
            503,
            resp_headers({"Content-Type": "text/html"}),
        )
    return (
        render_template("ping.html", status="Down", statuses=dbs_ok),
        503,
        resp_headers({"Content-Type": "text/html"}),
    )


def legend(layer, style, dates=None):
    # pylint: disable=redefined-outer-name
    cfg = get_config()
    product = cfg.layer_index.get(layer)
    if not product:
        return "Unknown Layer", 404, resp_headers({"Content-Type": "text/plain"})
    if dates is None:
        args = lower_get_args()
        ndates = int(args.get("ndates", 0))
    else:
        ndates = len(dates)
    try:
        img = create_legend_for_style(product, style, ndates)
    except WMSException as e:
        return str(e), e.http_response, resp_headers({"Content-Type": "text/plain"})

    if not img:
        return "Unknown Style", 404, resp_headers({"Content-Type": "text/plain"})
    return img
