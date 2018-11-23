from __future__ import absolute_import, division, print_function

from flask import render_template

from datacube_wms.data import get_map, feature_info
from datacube_wms.ogc_utils import resp_headers, get_service_base_url

from datacube_wms.ogc_exceptions import WMTSException

from datacube_wms.wms_layers import get_layers, get_service_cfg

from datacube_wms.legend_generator import legend_graphic

# TODO: method names that overlap with WMS.
WMTS_REQUESTS = ("GETTILE", "GETFEATUREINFO", "GETLEGENDGRAPHIC")


def handle_wmts(nocase_args):
    operation = nocase_args.get("request", "").upper()
    # WMS operation Map
    if not operation:
        raise WMTSException("No operation specified", locator="Request parameter")
    elif operation == "GETCAPABILITIES":
        return get_capabilities(nocase_args)
    else:
        raise WMTSException("Unrecognised operation: %s" % operation, WMTSException.OPERATION_NOT_SUPPORTED,
                           "Request parameter")


def get_capabilities(args):
    # TODO: Handle updatesequence request parameter for cache consistency.
    # Note: Only WMS v1.0.0 exists at this stage, so no version negotiation is necessary
    # Extract layer metadata from Datacube.
    platforms = get_layers(refresh=True)
    service_cfg = get_service_cfg()
    url = args.get('Host', args['url_root'])
    base_url = get_service_base_url(service_cfg.allowed_urls, url)
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
            service=service_cfg,
            platforms=platforms,
            base_url=base_url,
            show_service_id = show_service_id,
            show_service_provider = show_service_provider,
            show_ops_metadata = show_ops_metadata,
            show_contents = show_contents,
            show_themes = show_themes),
        200,
        resp_headers(
            {"Content-Type": "application/xml", "Cache-Control": "no-cache,max-age=0"}
        )
    )
