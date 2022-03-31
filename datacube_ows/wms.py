# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import absolute_import, division, print_function

from flask import render_template

from datacube_ows.data import feature_info, get_map
from datacube_ows.legend_generator import legend_graphic
from datacube_ows.ogc_exceptions import WMSException
from datacube_ows.ogc_utils import cache_control_headers, get_service_base_url
from datacube_ows.ows_configuration import get_config
from datacube_ows.utils import log_call

WMS_REQUESTS = ("GETMAP", "GETFEATUREINFO", "GETLEGENDGRAPHIC")


@log_call
def handle_wms(nocase_args):
    operation = nocase_args.get("request", "").upper()
    # WMS operation Map
    if not operation:
        raise WMSException("No operation specified", locator="Request parameter")
    elif operation == "GETCAPABILITIES":
        return get_capabilities(nocase_args)
    elif operation == "GETMAP":
        return get_map(nocase_args)
    elif operation == "GETFEATUREINFO":
        return feature_info(nocase_args)
    elif operation == "GETLEGENDGRAPHIC":
        return legend_graphic(nocase_args)
    else:
        raise WMSException("Unrecognised operation: %s" % operation, WMSException.OPERATION_NOT_SUPPORTED,
                           "Request parameter")


@log_call
def get_capabilities(args):
    # TODO: Handle updatesequence request parameter for cache consistency.
    # Note: Only WMS v1.3.0 is fully supported at this stage, so no version negotiation is necessary
    # Extract layer metadata from Datacube.
    cfg = get_config()
    url = args.get('Host', args['url_root'])
    base_url = get_service_base_url(cfg.allowed_urls, url)
    headers = cache_control_headers(cfg.wms_cap_cache_age)
    headers["Content-Type"] = "application/xml"
    return (
        render_template(
            "wms_capabilities.xml",
            cfg=cfg,
            base_url=base_url),
        200,
        cfg.response_headers(headers)
    )
