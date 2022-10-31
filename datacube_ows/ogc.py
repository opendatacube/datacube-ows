# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import sys
import traceback
from time import monotonic

from flask import g, render_template, request
from flask_log_request_id import current_request_id

from datacube_ows import __version__
from datacube_ows.cube_pool import cube
from datacube_ows.legend_generator import create_legend_for_style
from datacube_ows.ogc_exceptions import OGCException, WMSException
from datacube_ows.ogc_utils import (capture_headers, get_service_base_url,
                                    lower_get_args, resp_headers)
from datacube_ows.ows_configuration import get_config
from datacube_ows.protocol_versions import supported_versions
from datacube_ows.startup_utils import *  # pylint: disable=wildcard-import,unused-wildcard-import
from datacube_ows.wcs1 import WCS_REQUESTS
from datacube_ows.wms import WMS_REQUESTS

# Logging intialisation
_LOG = initialise_logger()
initialise_ignorable_warnings()

# Initialisation of external libraries - controlled by environment variables.
initialise_debugging(_LOG)
initialise_sentry(_LOG)
initialise_aws_credentials(_LOG)

# Prepare parsed configuration object
cfg = parse_config_file()

# Initialise Flask
app = initialise_flask(__name__)

babel = initialise_babel(cfg, app)

# Initialisation of external libraries that depend on Flask
# (controlled by environment variables)
metrics = initialise_prometheus(app, _LOG)

# Protocol/Version lookup table
OWS_SUPPORTED = supported_versions()

# Prometheus Metrics
prometheus_ows_ogc_metric = metrics.histogram(
    "ows_ogc",
    "Summary by OGC request protocol, version, operation, layer, and HTTP Status",
    labels={
        'query_request': lambda: request.args.get('request', "NONE").upper(),
        'query_service': lambda: request.args.get('service', "NONE").upper(),
        'query_version': lambda: request.args.get('version'),
        'query_layer': lambda: (request.args.get('query_layers') # WMS GetFeatureInfo
                                or request.args.get('layers')  # WMS
                                or request.args.get('layer')  # WMTS
                                or request.args.get('coverage')  # WCS 1.x
                                or request.args.get('coverageid')  # WCS 2.x
                                ),
        'status': lambda r: r.status_code,
    }
)



# Flask Routes


@app.route('/')
@prometheus_ows_ogc_metric
def ogc_impl():
    #pylint: disable=too-many-branches
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
        elif op in WCS_REQUESTS:
            return ogc_svc_impl("wcs")
        elif op:
            # Should we return a WMS or WCS exception if there is no service specified?
            # Defaulting to WMS because that's what we already have.
            raise WMSException("Invalid service and/or request", locator="Service and request parameters")
        else:
            cfg = get_config()   # pylint: disable=redefined-outer-name
            url = nocase_args.get('Host', nocase_args['url_root'])
            base_url = get_service_base_url(cfg.allowed_urls, url)
            return (render_template(
                            "index.html",
                            cfg=cfg,
                            supported=OWS_SUPPORTED,
                            base_url=base_url,
                            version=__version__,
                    ),
                    200,
                    resp_headers({"Content-Type": "text/html"}))
    except OGCException as e:
        _LOG.error("Handled Error: %s", repr(e.errors))
        return e.exception_response()
    except Exception as e: # pylint: disable=broad-except
        tb = sys.exc_info()[2]
        ogc_e = WMSException("Unexpected server error: %s" % str(e), http_response=500)
        return ogc_e.exception_response(traceback=traceback.extract_tb(tb))


def ogc_svc_impl(svc):
    svc_support = OWS_SUPPORTED.get(svc)
    nocase_args = lower_get_args()
    nocase_args = capture_headers(request, nocase_args)
    service = nocase_args.get("service", svc).upper()

    # Is service activated in config?
    try:
        if not svc_support:
            raise WMSException(f"Invalid service: {svc}",
                               valid_keys=[
                                       service.service
                                       for service in OWS_SUPPORTED.values()
                                       if service.activated()
                               ],
                               code=WMSException.OPERATION_NOT_SUPPORTED,
                               locator="service parameter")
        if not svc_support.activated():
            raise svc_support.default_exception_class("Invalid service and/or request", locator="Service and request parameters")

        # Does service match path (if supplied)
        if service != svc_support.service_upper:
            raise svc_support.default_exception_class("Invalid service", locator="Service parameter")

        version = nocase_args.get("version")
        version_support = svc_support.negotiated_version(version)
    except OGCException as e:
        return e.exception_response()

    try:
        return version_support.router(nocase_args)
    except OGCException as e:
        return e.exception_response()
    except Exception as e: #pylint: disable=broad-except
        tb = sys.exc_info()[2]
        ogc_e = version_support.exception_class("Unexpected server error: %s" % str(e), http_response=500)
        return ogc_e.exception_response(traceback=traceback.extract_tb(tb))


@app.route('/wms')
@prometheus_ows_ogc_metric
def ogc_wms_impl():
    return ogc_svc_impl("wms")


@app.route('/wmts')
@prometheus_ows_ogc_metric
def ogc_wmts_impl():
    return ogc_svc_impl("wmts")


@app.route('/wcs')
@prometheus_ows_ogc_metric
def ogc_wcs_impl():
    return ogc_svc_impl("wcs")

@app.route('/ping')
@metrics.summary('ows_heartbeat_pings', "Ping durations", labels={"status": lambda r: r.status})
def ping():
    db_ok = False
    with cube() as dc:
        if dc:
            # pylint: disable=protected-access
            with dc.index._db.give_me_a_connection() as conn:
                results = conn.execute("""
                        SELECT *
                        FROM wms.product_ranges
                        LIMIT 1"""
                )
                for r in results:
                    db_ok = True
    if db_ok:
        return (render_template("ping.html", status="Up"), 200, resp_headers({"Content-Type": "text/html"}))
    else:
        return (render_template("ping.html", status="Down"), 500, resp_headers({"Content-Type": "text/html"}))


@app.route("/legend/<string:layer>/<string:style>/legend.png")
@metrics.histogram('ows_legends', "Legend query durations", labels={
    "layer": lambda: request.path.split("/")[2],
    "style": lambda: request.path.split("/")[3],
    "status": lambda r: r.status,
})
def legend(layer, style, dates=None):
    # pylint: disable=redefined-outer-name
    cfg = get_config()
    product = cfg.product_index.get(layer)
    if not product:
        return ("Unknown Layer", 404, resp_headers({"Content-Type": "text/plain"}))
    if dates is None:
        args = lower_get_args()
        ndates = int(args.get("ndates", 0))
    else:
        ndates = len(dates)
    try:
        img = create_legend_for_style(product, style, ndates)
    except WMSException as e:
        return (str(e), e.http_response, resp_headers({"Content-Type": "text/plain"}))

    if not img:
        return ("Unknown Style", 404, resp_headers({"Content-Type": "text/plain"}))
    return img

# Flask middleware


@app.after_request
def append_request_id(response):
    response.headers.add("X-REQUEST-ID", current_request_id())
    return response


@app.before_request
def start_timer():
    # pylint: disable=assigning-non-slot
    g.ogc_start_time = monotonic()


@app.after_request
def log_time_and_request_response(response):
    time_taken = int((monotonic() - g.ogc_start_time) * 1000)
    # request.environ.get('HTTP_X_REAL_IP') captures requester ip on a local docker container via gunicorn
    if request.environ.get('HTTP_X_REAL_IP'):
        ip = request.environ.get('HTTP_X_REAL_IP')
    # request.environ.get('HTTP_X_FORWARDED_FOR') captures request IP forwarded by ingress/loadbalancer
    elif request.environ.get('HTTP_X_FORWARDED_FOR'):
        ip = request.environ.get('HTTP_X_FORWARDED_FOR')
    # request.environ.get('REMOTE_ADDR') is standard internal IP address
    elif request.environ.get('REMOTE_ADDR'):
        ip = request.environ.get('REMOTE_ADDR')
    else:
        ip = 'Not found'
    _LOG.info("ip: %s request: %s returned status: %d and took: %d ms", ip, request.url, response.status_code, time_taken)
    return response
