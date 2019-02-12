from __future__ import absolute_import, division, print_function
import sys
import traceback

from time import monotonic

from flask import Flask, request, g
from flask_log_request_id import RequestID, RequestIDLogFilter, current_request_id
import os

from datacube_wms.legend_generator import create_legend_for_style
from datacube_wms.ogc_utils import capture_headers, resp_headers
from datacube_wms.wms import handle_wms, WMS_REQUESTS
from datacube_wms.wcs import handle_wcs, WCS_REQUESTS
from datacube_wms.wmts import handle_wmts
from datacube_wms.ogc_exceptions import OGCException, WCS1Exception, WMSException, WMTSException

from datacube_wms.wms_layers import get_service_cfg, get_layers

from datacube_wms.utils import time_call

from .rasterio_env import rio_env

import logging

# pylint: disable=invalid-name, broad-except

app = Flask(__name__.split('.')[0])
RequestID(app)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] %(name)s [%(request_id)s] [%(levelname)s] %(message)s"))
handler.addFilter(RequestIDLogFilter())
_LOG = logging.getLogger()
_LOG.addHandler(handler)

# If invoked using Gunicorn, link our root logger to the gunicorn logger
# this will mean the root logs will be captured and managed by the gunicorn logger
# allowing you to set the gunicorn log directories and levels for logs
# produced by this application
_LOG.setLevel(logging.getLogger('gunicorn.error').getEffectiveLevel())

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
                    raise WMTSException("Invalid service", locator="Service parameter")
            else:
                # service argument is only required (in fact only defined) by OGC for
                # GetCapabilities requests.  As long as we are persisting with a single
                # routing end point for all services, we must derive the service from the request
                # parameter.
                # This is a quick hack to fix #64.  Service and operation routing could be
                # handled more elegantly.
                op = nocase_args.get("request", "").upper()
                if op in WMS_REQUESTS and svc_cfg.wms:
                    return handle_wms(nocase_args)
                elif op in WCS_REQUESTS and svc_cfg.wcs:
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


@app.route('/wms')
def ogc_wms_impl():
    #pylint: disable=too-many-branches
    nocase_args = lower_get_args()
    nocase_args = capture_headers(request, nocase_args)
    service = nocase_args.get("service", "").upper()
    svc_cfg = get_service_cfg()

    # create dummy env if not exists
    try:
        with rio_env():
            if service == "WMS" or service is None:
                # WMS operation Map
                if svc_cfg.wms:
                    return handle_wms(nocase_args)
                else:
                    raise WMSException("Invalid service", locator="Service parameter")
            else:
                raise WMSException("Invalid service and/or request", locator="Service and request parameters")
    except OGCException as e:
        return e.exception_response()
    except Exception as e:
        tb = sys.exc_info()[2]
        ogc_e = WMSException("Unexpected server error: %s" % str(e), http_response=500)
        return ogc_e.exception_response(traceback=traceback.extract_tb(tb))


@app.route('/wmts')
def ogc_wmts_impl():
    #pylint: disable=too-many-branches
    nocase_args = lower_get_args()
    nocase_args = capture_headers(request, nocase_args)
    service = nocase_args.get("service", "").upper()
    svc_cfg = get_service_cfg()

    # create dummy env if not exists
    try:
        with rio_env():
            if service == "WMTS" or service is None:
                # WMTS operation Map
                if svc_cfg.wmts:
                    return handle_wmts(nocase_args)
                else:
                    raise WMTSException("Invalid service", locator="Service parameter")
            else:
                raise WMTSException("Invalid service and/or request", locator="Service and request parameters")
    except OGCException as e:
        return e.exception_response()
    except Exception as e:
        tb = sys.exc_info()[2]
        ogc_e = WMTSException("Unexpected server error: %s" % str(e), http_response=500)
        return ogc_e.exception_response(traceback=traceback.extract_tb(tb))


@app.route('/wcs')
def ogc_wcs_impl():
    #pylint: disable=too-many-branches
    nocase_args = lower_get_args()
    nocase_args = capture_headers(request, nocase_args)
    service = nocase_args.get("service", "").upper()
    svc_cfg = get_service_cfg()

    # create dummy env if not exists
    try:
        with rio_env():
            if service == "WCS" or service is None:
                # WCS operation Map
                if svc_cfg.wcs:
                    return handle_wcs(nocase_args)
                else:
                    raise WCS1Exception("Invalid service", locator="Service parameter")
            else:
                raise WCS1Exception("Invalid service and/or request", locator="Service and request parameters")
    except OGCException as e:
        return e.exception_response()
    except Exception as e:
        tb = sys.exc_info()[2]
        ogc_e = WCS1Exception("Unexpected server error: %s" % str(e), http_response=500)
        return ogc_e.exception_response(traceback=traceback.extract_tb(tb))


@app.route("/legend/<string:layer>/<string:style>/legend.png")
def legend(layer, style):
    platforms = get_layers()
    product = platforms.product_index.get(layer)
    if not product:
        return ("Unknown Layer", 404, resp_headers({"Content-Type": "text/plain"}))
    img = create_legend_for_style(product, style)
    if not img:
        return ("Unknown Style", 404, resp_headers({"Content-Type": "text/plain"}))
    return img

@app.after_request
def append_request_id(response):
    response.headers.add("X-REQUEST-ID", current_request_id())
    return response

@app.before_request
def start_timer():
    g.ogc_start_time = monotonic()

@app.after_request
def log_time_and_request_response(response):
    time_taken = int((monotonic() - g.ogc_start_time) * 1000)
    _LOG.info("request: %s returned status: %d and took: %d ms", request.url, response.status_code, time_taken)
    return response