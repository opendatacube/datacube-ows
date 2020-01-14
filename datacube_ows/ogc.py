from __future__ import absolute_import, division, print_function
import sys
import traceback
import sentry_sdk
from sentry_sdk.integrations.flask import FlaskIntegration

from time import monotonic

from flask import Flask, request, g, render_template
from flask_log_request_id import RequestID, RequestIDLogFilter, current_request_id
import os

from datacube_ows.legend_generator import create_legend_for_style
from datacube_ows.ogc_utils import capture_headers, resp_headers
from datacube_ows.wms import handle_wms, WMS_REQUESTS
from datacube_ows.wcs import handle_wcs, WCS_REQUESTS
from datacube_ows.wmts import handle_wmts
from datacube_ows.ogc_exceptions import OGCException, WCS1Exception, WMSException, WMTSException
from datacube_ows.utils import opencensus_trace_call, get_jaeger_exporter, get_opencensus_tracer, opencensus_tracing_enabled
from datacube_ows.cube_pool import cube
from datacube.utils.rio import set_default_rio_config
from datacube_ows.ows_configuration import get_config

import logging

# pylint: disable=invalid-name, broad-except



if os.environ.get("PYDEV_DEBUG"):
    import pydevd_pycharm
    pydevd_pycharm.settrace('172.17.0.1', port=12321, stdoutToServer=True, stderrToServer=True)

handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("[%(asctime)s] %(name)s [%(request_id)s] [%(levelname)s] %(message)s"))
handler.addFilter(RequestIDLogFilter())
_LOG = logging.getLogger()
_LOG.addHandler(handler)

if os.environ.get("SENTRY_KEY") and os.environ.get("SENTRY_PROJECT"):
    sentry_sdk.init(
        dsn="https://%s@sentry.io/%s" % (os.environ["SENTRY_KEY"], os.environ["SENTRY_PROJECT"]),
        integrations = [FlaskIntegration()]
    )
    _LOG.info("Sentry logging enabled")

app = Flask(__name__.split('.')[0])
RequestID(app)

tracer = None
if opencensus_tracing_enabled():
    from opencensus.trace import config_integration
    from opencensus.ext.flask.flask_middleware import FlaskMiddleware
    tracer = get_opencensus_tracer()
    integration = ['sqlalchemy']
    config_integration.trace_integrations(integration, tracer=tracer)
    jaegerExporter = get_jaeger_exporter()
    middleware = FlaskMiddleware(app, exporter=jaegerExporter)
    _LOG.info("Opencensus tracing enabled")

# If invoked using Gunicorn, link our root logger to the gunicorn logger
# this will mean the root logs will be captured and managed by the gunicorn logger
# allowing you to set the gunicorn log directories and levels for logs
# produced by this application
_LOG.setLevel(logging.getLogger('gunicorn.error').getEffectiveLevel())

if os.environ.get("prometheus_multiproc_dir", False):
    from datacube_ows.metrics.prometheus import setup_prometheus
    setup_prometheus(app)
    _LOG.info("Prometheus metrics enabled")

if os.environ.get("AWS_DEFAULT_REGION"):
    set_default_rio_config(aws=dict(aws_unsigned=True,
                                    region_name="auto"),
                           cloud_defaults=True)
else:
    set_default_rio_config()
    _LOG.warning("Environment variable $AWS_DEFAULT_REGION not set.  (This warning can be ignored if all data is stored locally.)")


class SupportedSvcVersion(object):
    def __init__(self, service, version, router, exception_class):
        self.service = service.lower()
        self.service_upper = service.upper()
        self.version = version
        self.version_parts = version.split(".")
        assert len(self.version_parts) == 3
        self.router = router
        self.exception_class = exception_class


class SupportedSvc(object):
    def __init__(self, versions, default_exception_class=None):
        self.versions = sorted(versions, key=lambda x: x.version_parts)
        assert len(self.versions) > 0
        self.service = self.versions[0].service
        self.service_upper = self.versions[0].service_upper
        assert self.service.upper() == self.service_upper
        assert self.service == self.service_upper.lower()
        for v in self.versions[1:]:
            assert v.service == self.service
            assert v.service_upper == self.service_upper
        if default_exception_class:
            self.default_exception_class = default_exception_class
        else:
            self.default_exception_class = self.versions[0].exception_class

    def negotiated_version(self, request_version):
        if not request_version:
            return self.versions[-1]
        rv_parts = request_version.split(".")
        for v in reversed(self.versions):
            if rv_parts >= v.version_parts:
                return v
        # The constructor asserted that self.versions is not empty, so this is safe.
        #pylint: disable=undefined-loop-variable
        return v

    def activated(self):
        cfg = get_config()
        return getattr(cfg, self.service)


OWS_SUPPORTED = {
    "wms": SupportedSvc([
        SupportedSvcVersion("wms", "1.3.0", handle_wms, WMSException),
    ]),
    "wmts": SupportedSvc([
        SupportedSvcVersion("wmts", "1.0.0", handle_wmts, WMTSException),
    ]),
    "wcs": SupportedSvc([
        SupportedSvcVersion("wcs", "1.0.0", handle_wcs, WCS1Exception),
    ]),
}


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
        else:
            # Should we return a WMS or WCS exception if there is no service specified?
            # Defaulting to WMS because that's what we already have.
            raise WMSException("Invalid service and/or request", locator="Service and request parameters")
    except OGCException as e:
        _LOG.error("Handled Error: %s", repr(e.errors))
        return e.exception_response()
    except Exception as e:
        tb = sys.exc_info()[2]
        ogc_e = WMSException("Unexpected server error: %s" % str(e), http_response=500)
        return ogc_e.exception_response(traceback=traceback.extract_tb(tb))


@opencensus_trace_call(tracer=tracer)
def ogc_svc_impl(svc):
    svc_support = OWS_SUPPORTED[svc]
    nocase_args = lower_get_args()
    nocase_args = capture_headers(request, nocase_args)
    service = nocase_args.get("service", svc).upper()

    # Is service activated in config?
    try:
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
    except Exception as e:
        tb = sys.exc_info()[2]
        ogc_e = version_support.exception_class("Unexpected server error: %s" % str(e), http_response=500)
        return ogc_e.exception_response(traceback=traceback.extract_tb(tb))


@app.route('/wms')
def ogc_wms_impl():
    return ogc_svc_impl("wms")


@app.route('/wmts')
def ogc_wmts_impl():
    return ogc_svc_impl("wmts")


@app.route('/wcs')
def ogc_wcs_impl():
    return ogc_svc_impl("wcs")


@app.route('/ping')
def ping():
    db_ok = False
    with cube() as dc:
        # pylint: disable=protected-access
        with dc.index._db.give_me_a_connection() as conn:
            try:
                results = conn.execute("""
                        SELECT *
                        FROM wms.product_ranges
                        LIMIT 1"""
                )
                for r in results:
                    db_ok = True
            except Exception:
                pass
    if db_ok:
        return (render_template("ping.html", status="Up"), 200, resp_headers({"Content-Type": "text/html"}))
    else:
        return (render_template("ping.html", status="Down"), 500, resp_headers({"Content-Type": "text/html"}))


@app.route("/legend/<string:layer>/<string:style>/legend.png")
def legend(layer, style):
    cfg = get_config()
    product = cfg.product_index.get(layer)
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
