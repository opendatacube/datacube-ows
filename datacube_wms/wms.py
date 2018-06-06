from __future__ import absolute_import, division, print_function

from flask import render_template

from datacube_wms.data import get_map, feature_info
from datacube_wms.ogc_utils import resp_headers

from datacube_wms.ogc_exceptions import WMSException


try:
    from datacube_wms.wms_cfg_local import service_cfg
except:
        from datacube_wms.wms_cfg import service_cfg
from datacube_wms.wms_layers import get_layers


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
    else:
        raise WMSException("Unrecognised operation: %s" % operation, WMSException.OPERATION_NOT_SUPPORTED,
                           "Request parameter")


def get_capabilities(args):
    # TODO: Handle updatesequence request parameter for cache consistency.
    # Note: Only WMS v1.3.0 is fully supported at this stage, so no version negotiation is necessary
    # Extract layer metadata from Datacube.
    platforms = get_layers(refresh=True)
    return render_template("wms_capabilities.xml", service=service_cfg, platforms=platforms), 200, resp_headers(
        {"Content-Type": "application/xml", "Cache-Control": "no-cache", "Cache-Control": "max-age=0"})

