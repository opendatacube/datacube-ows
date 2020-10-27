from __future__ import absolute_import, division, print_function

from flask import render_template

from datacube.utils import geometry
from datacube_ows.data import get_map, feature_info
from datacube_ows.ogc_utils import get_service_base_url

from datacube_ows.ogc_exceptions import WMSException, WMTSException

from datacube_ows.ows_configuration import get_config

from datacube_ows.utils import log_call
import logging
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
    return (
        render_template(
            "wmts_capabilities.xml",
            cfg=cfg,
            base_url=base_url,
            show_service_id = show_service_id,
            show_service_provider = show_service_provider,
            show_ops_metadata = show_ops_metadata,
            show_contents = show_contents,
            show_themes = show_themes),
        200,
        cfg.response_headers(
            {"Content-Type": "application/xml", "Cache-Control": "max-age=10"}
        )
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
        "crs": "EPSG:3857",
        "requestid": args["requestid"]
    }

    tms = None
    for _tms in cfg.supported_tile_matrix_sets:
        if tileMatrixSet == _tms.identifier or tileMatrixSet == _tms.wkss:
            tms = _tms
            break

    if tms is None:
        raise WMTSException("Invalid Tile Matrix Set: " + tileMatrixSet)

    if cfg.published_CRSs[tms.crs_name]["vertical_coord_first"]:
        _LOG.warning("Potential Coordinate ordering issue")
    try:
        tileMatrix = int(tileMatrix)
        if tileMatrix < 0 or tileMatrix >= len(tms.scale_set):
            raise WMTSException("Invalid Tile Matrix: " + tileMatrix)
    except ValueError:
        raise WMTSException("Invalid Tile Matrix: " + tileMatrix)
    try:
        row = int(row)
    except ValueError:
        raise WMTSException("Invalid Tile Row: " + row)
    try:
        col = int(col)
    except ValueError:
        raise WMTSException("Invalid Tile Col: " + col)

    matrix_origin = tms.top_left
    scale_denominator = tms.scale_set[tileMatrix]
    pixel_span = [ scale_denominator * 0.00028 * u for u in tms.unit_coefficients]
    tile_span = [ pixel_span[i] * tms.tile_size[i] for i in range(2)]

    left  = matrix_origin[0] + col * tile_span[0]
    right = left + tile_span[0]
    upper = matrix_origin[1] - row * tile_span[1]
    lower = upper - tile_span[1]

    wms_args["bbox"] = "%f,%f,%f,%f" % (
        left, lower, right, upper
    )

    # GetFeatureInfo only args
    if "i" in args:
        wms_args["i"] = args["i"]
        wms_args["j"] = args.get("j", "")
        wms_args["info_format"] = args.get("infoformat", "")

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
    wms_args = wmts_args_to_wms(args)
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


