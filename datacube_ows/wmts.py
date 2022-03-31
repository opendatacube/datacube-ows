# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import absolute_import, division, print_function

import logging

from flask import render_template

from datacube_ows.data import feature_info, get_map
from datacube_ows.ogc_exceptions import WMSException, WMTSException
from datacube_ows.ogc_utils import cache_control_headers, get_service_base_url
from datacube_ows.ows_configuration import get_config
from datacube_ows.utils import log_call

_LOG = logging.getLogger(__name__)




# NB. No need to disambiguate method names shared with WMS because WMTS requires
# a "SERVICE" parameter with every request.

@log_call
def handle_wmts(nocase_args):
    operation = nocase_args.get("request", "").upper()
    # WMS operation Map
    if not operation:
        raise WMTSException("No operation specified", locator="Request parameter")
    elif operation == "GETCAPABILITIES":
        return get_capabilities(nocase_args)
    elif operation == "GETTILE":
        return get_tile(nocase_args)
    elif operation == "GETFEATUREINFO":
        return get_feature_info(nocase_args)
    else:
        raise WMTSException("Unrecognised operation: %s" % operation, WMTSException.OPERATION_NOT_SUPPORTED,
                           "Request parameter")


@log_call
def get_capabilities(args):
    # TODO: Handle updatesequence request parameter for cache consistency.
    # Note: Only WMS v1.0.0 exists at this stage, so no version negotiation is necessary
    # Extract layer metadata from Datacube.
    cfg = get_config()
    url = args.get('Host', args['url_root'])
    base_url = get_service_base_url(cfg.allowed_urls, url)
    section = args.get("section")
    if section:
        section = section.lower()
    show_service_id = False
    show_service_provider = False
    show_ops_metadata = False
    show_contents = False
    show_themes = False
    if section is None:
        show_service_id = True
        show_service_provider = True
        show_ops_metadata = True
        show_contents = True
        show_themes = True
    else:
        sections = section.split(",")
        for s in sections:
            if s == "all":
                show_service_id = True
                show_service_provider = True
                show_ops_metadata = True
                show_contents = True
                show_themes = True
            elif s == "serviceidentification":
                show_service_id = True
            elif s == "serviceprovider":
                show_service_provider = True
            elif s == "operationsmetadata":
                show_ops_metadata = True
            elif s == "contents":
                show_contents = True
            elif s == "themes":
                show_themes = True
            else:
                raise WMTSException("Invalid section: %s" % section,
                                WMTSException.INVALID_PARAMETER_VALUE,
                                locator="Section parameter")
    headers = cache_control_headers(cfg.wms_cap_cache_age)
    headers["Content-Type"] = "application/xml"
    return (
        render_template(
            "wmts_capabilities.xml",
            cfg=cfg,
            base_url=base_url,
            show_service_id=show_service_id,
            show_service_provider=show_service_provider,
            show_ops_metadata=show_ops_metadata,
            show_contents=show_contents,
            show_themes=show_themes),
        200,
        cfg.response_headers(headers)
    )


@log_call
def wmts_args_to_wms(args, cfg):
    layer = args.get("layer")
    style = args.get("style")
    format_ = args.get("format")
    time = args.get("time", "")
    tileMatrixSet = args.get("tilematrixset")
    tileMatrix = args.get("tilematrix")
    row = args.get("tilerow")
    col = args.get("tilecol")

    wms_args = {
        "version": "1.3.0",
        "service": "WMS",
        "request": "GetMap",
        "styles": style,
        "layers": layer,
        "time": time,
        "width": 256,
        "height": 256,
        "format": format_,
        "exceptions": "application/vnd.ogc.se_xml",
        "requestid": args["requestid"]
    }

    tms = cfg.tile_matrix_sets.get(tileMatrixSet)
    if not tms:
        for _tms in cfg.tile_matrix_sets.values():
            if tileMatrixSet == _tms.wkss:
                tms = _tms
                break

    if tms is None:
        raise WMTSException("Invalid Tile Matrix Set: " + tileMatrixSet)

    wms_args["crs"] = tms.crs_name
    crs_cfg = cfg.published_CRSs[tms.crs_name]
    try:
        tileMatrix = int(tileMatrix)
        if tileMatrix < 0 or tileMatrix >= len(tms.scale_set):
            raise WMTSException(f"Invalid Tile Matrix: {tileMatrix}")
    except ValueError:
        raise WMTSException(f"Invalid Tile Matrix: {tileMatrix}")
    try:
        row = int(row)
    except ValueError:
        raise WMTSException(f"Invalid Tile Row {row}")
    try:
        col = int(col)
    except ValueError:
        raise WMTSException(f"Invalid Tile Col: {col}")
    wms_args["bbox"] = "%f,%f,%f,%f" % tms.wms_bbox_coords(tileMatrix, row, col)

    # GetFeatureInfo only args
    if "i" in args:
        wms_args["i"] = args["i"]
        wms_args["j"] = args.get("j", "")
        wms_args["info_format"] = args.get("infoformat", "")


    if args.get("ows_stats"):
        wms_args["ows_stats"] = "y"

    return wms_args


@log_call
def get_tile(args):
    cfg = get_config()
    wms_args = wmts_args_to_wms(args, cfg)

    try:
        return get_map(wms_args)
    except WMSException as wmse:
        first_error = wmse.errors[0]
        e = WMTSException(first_error["msg"],
                            code=first_error["code"],
                            locator=first_error["locator"],
                            http_response=wmse.http_response)
        for error in wmse.errors[1:]:
            e.add_error(error["msg"], code=error["code"], locator=error["locator"])
        raise e


@log_call
def get_feature_info(args):
    cfg = get_config()
    wms_args = wmts_args_to_wms(args, cfg)
    wms_args["query_layers"] = wms_args["layers"]

    try:
        return feature_info(wms_args)
    except WMSException as wmse:
        first_error = wmse.errors[0]
        e = WMTSException(first_error["msg"],
                          code=first_error["code"],
                          locator=first_error["locator"],
                          http_response=wmse.http_response)
        for error in wmse.errors[1:]:
            e.add_error(error["msg"], code=error["code"], locator=error["locator"])
        raise e
