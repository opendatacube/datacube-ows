from __future__ import absolute_import, division, print_function
import sys
import traceback

from flask import Flask, request, render_template
from flask_request_id import RequestID
import boto3
import rasterio
import os

from datacube_wms.ogc_utils import capture_headers
from datacube_wms.wms import handle_wms, WMS_REQUESTS
from datacube_wms.wcs import handle_wcs, WCS_REQUESTS
from datacube_wms.wmts import handle_wmts
from datacube_wms.ogc_exceptions import OGCException, WCS1Exception, WMSException

from datacube_wms.wms_layers import get_service_cfg

from .rasterio_env import rio_env

import logging

# pylint: disable=invalid-name, broad-except

_LOG = logging.getLogger(__name__)

app = Flask(__name__.split('.')[0])
RequestID(app)

if os.environ.get("prometheus_multiproc_dir", False):
    from datacube_wms.metrics.prometheus import setup_prometheus
    setup_prometheus(app)

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
def ogc_impl():
    #pylint: disable=too-many-branches
    nocase_args = lower_get_args()
    nocase_args = capture_headers(request, nocase_args)
    service = nocase_args.get("service", "").upper()
    svc_cfg = get_service_cfg()
    # create dummy env if not exists
    try:
        with rio_env():
            if service == "WMS":
                # WMS operation Map
                if svc_cfg.wms:
                    return handle_wms(nocase_args)
                else:
                    raise WMSException("Invalid service", locator="Service parameter")
            elif service == "WCS":
                # WCS operation Map
                if svc_cfg.wcs:
                    return handle_wcs(nocase_args)
                else:
                    raise WCS1Exception("Invalid service", locator="Service parameter")
            elif service == "WMTS":
                # WMTS operation Map
                # Note that SERVICE is a required parameter for all operations in WMTS
                if svc_cfg.wmts:
                    return handle_wmts(nocase_args)
                else:
                    raise WCS1Exception("Invalid service", locator="Service parameter")
            else:
                # service argument is only required (in fact only defined) by OGC for
                # GetCapabilities requests.  As long as we are persisting with a single
                # routing end point for all services, we must derive the service from the request
                # parameter.
                # This is a quick hack to fix #64.  Service and operation routing could be
                # handled more elegantly.
                op = nocase_args.get("request", "").upper()
                if op in WMS_REQUESTS:
                    return handle_wms(nocase_args)
                elif op in WCS_REQUESTS:
                    return handle_wcs(nocase_args)
                else:
                    # Should we return a WMS or WCS exception if there is no service specified?
                    # Defaulting to WMS because that's what we already have.
                    raise WMSException("Invalid service and/or request", locator="Service and request parameters")
    except OGCException as e:
        return e.exception_response()
    except Exception as e:
        tb = sys.exc_info()[2]
        if service == "WCS":
            eclass = WCS1Exception
        else:
            eclass = WMSException
        ogc_e = eclass("Unexpected server error: %s" % str(e), http_response=500)
        return ogc_e.exception_response(traceback=traceback.extract_tb(tb))
