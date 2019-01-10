from __future__ import absolute_import, division, print_function

from flask import render_template

from datacube_wms.data import get_map, feature_info
from datacube_wms.ogc_utils import resp_headers, get_service_base_url

from datacube_wms.ogc_exceptions import WMSException

from datacube_wms.wms_layers import get_layers, get_service_cfg

from datacube_wms.legend_generator import legend_graphic
from datacube_wms.utils import log_call


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
        response = legend_graphic(nocase_args)
        if response is None:
            raise WMSException("Operation GetLegendGraphic not supported for this product and style",
                               WMSException.OPERATION_NOT_SUPPORTED,
                               "Request parameter")
        else:
            return response
    else:
        raise WMSException("Unrecognised operation: %s" % operation, WMSException.OPERATION_NOT_SUPPORTED,
                           "Request parameter")


@log_call
def get_capabilities(args):
    # TODO: Handle updatesequence request parameter for cache consistency.
    # Note: Only WMS v1.3.0 is fully supported at this stage, so no version negotiation is necessary
    # Extract layer metadata from Datacube.
    platforms = get_layers(refresh=True)
    service_cfg = get_service_cfg()
    url = args.get('Host', args['url_root'])
    base_url = get_service_base_url(service_cfg.allowed_urls, url)
    return (
        render_template(
            "wms_capabilities.xml",
            service=service_cfg,
            platforms=platforms,
            base_url=base_url),
        200,
        resp_headers(
            {"Content-Type": "application/xml", "Cache-Control": "no-cache,max-age=0"}
        )
    )
