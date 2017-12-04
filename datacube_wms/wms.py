from __future__ import absolute_import, division, print_function

import sys
import traceback

from flask import Flask, request, render_template

from datacube_wms.data import get_map, feature_info
from datacube_wms.wms_utils import resp_headers, WMSException, wms_exception

app = Flask(__name__.split('.')[0])

from datacube_wms.wms_cfg import service_cfg
from datacube_wms.wms_layers import get_layers


def lower_get_args():
    # Get parameters in WMS are case-insensitive, and intended to be single use.
    # Spec does not specify which instance should be used if a parameter is provided more than once.
    # This function uses the LAST instance.
    d = {}
    for k in request.args.keys():
        kl = k.lower()
        for v in request.args.getlist(k):
            d[kl] = v
    return d


@app.route('/')
def wms_impl():
    nocase_args = lower_get_args()
    operation = nocase_args.get("request")
    try:
        if not operation:
            raise WMSException("No operation specified", locator="Request parameter")
        elif operation == "GetCapabilities":
            return get_capabilities(nocase_args)
        elif operation == "GetMap":
            return get_map(nocase_args)
        elif operation == "GetFeatureInfo":
            return feature_info(nocase_args)
        else:
            raise WMSException("Unrecognised operation: %s" % operation, WMSException.OPERATION_NOT_SUPPORTED,
                               "Request parameter")
    except WMSException as e:
        return wms_exception(e)
    except Exception as e:
        tb = sys.exc_info()[2]
        wms_e = WMSException("Unexpected server error: %s" % str(e), http_response=500)
        return wms_exception(wms_e, traceback=traceback.extract_tb(tb))


@app.route('/test_client')
def test_client():
    return render_template("test_client.html")


def get_capabilities(args):
    if args.get("service") != "WMS":
        raise WMSException("Invalid service", locator="Service parameter")
    # TODO: Handle updatesequence request parameter for cache consistency.
    # Note: Only WMS v1.3.0 is fully supported at this stage, so no version negotiation is necessary
    # Extract layer metadata from Datacube.
    platforms = get_layers()
    return render_template("capabilities.xml", service=service_cfg, platforms=platforms), 200, resp_headers(
        {"Content-Type": "application/xml"})
