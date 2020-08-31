from __future__ import absolute_import, division, print_function
import sys
import traceback
import warnings
import sentry_sdk
from rasterio.errors import NotGeoreferencedWarning
from sentry_sdk.integrations.flask import FlaskIntegration
from prometheus_flask_exporter.multiprocess import GunicornInternalPrometheusMetrics

from time import monotonic

from flask import Flask, request, g, render_template
from flask_log_request_id import RequestID, RequestIDLogFilter, current_request_id
import os

from datacube_ows.legend_generator import create_legend_for_style
from datacube_ows.ogc_utils import capture_headers, resp_headers, get_service_base_url
from datacube_ows.wms import handle_wms, WMS_REQUESTS
from datacube_ows.wcs1 import handle_wcs1, WCS_REQUESTS
from datacube_ows.wcs2 import handle_wcs2
from datacube_ows.wmts import handle_wmts
from datacube_ows.ogc_exceptions import OGCException, WCS1Exception, WCS2Exception, WMSException, WMTSException
from datacube_ows.cube_pool import cube
from datacube.utils.aws import configure_s3_access
from datacube_ows.ows_configuration import get_config

import logging

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

# Suppress annoying rasterio warning message every time we write to a non-georeferenced image format
warnings.simplefilter("ignore", category=NotGeoreferencedWarning)

# For Prometheus
metrics = None

def ows_init_libs():
    # Startup initialisation of libraries controlled by environment variables
    #
    # Move to a function to facilitate unit testing.
    # Should be done in a more flexible pluggable way.

    # PYCHARM Debugging
    if os.environ.get("PYDEV_DEBUG"):
        import pydevd_pycharm
        pydevd_pycharm.settrace('172.17.0.1', port=12321, stdoutToServer=True, stderrToServer=True)

    # Sentry
    if os.environ.get("SENTRY_KEY") and os.environ.get("SENTRY_PROJECT"):
        sentry_sdk.init(
            dsn="https://%s@sentry.io/%s" % (os.environ["SENTRY_KEY"], os.environ["SENTRY_PROJECT"]),
            integrations = [FlaskIntegration()]
        )
        _LOG.info("Sentry logging enabled")

    # Prometheus
    if os.environ.get("prometheus_multiproc_dir", False):
        #pylint: disable=global-statement
        global metrics
        metrics = GunicornInternalPrometheusMetrics(app)
        _LOG.info("Prometheus metrics enabled")

    # Boto3/AWS
    if os.environ.get("AWS_DEFAULT_REGION"):
        env_nosign = os.environ.get("AWS_NO_SIGN_REQUEST", "yes")
        unsigned = bool(env_nosign)
        if not unsigned or env_nosign.lower() in ("n", "f", "no", "false", "0"):
            unsigned = False
            # set env variable to comply with gdal
            os.environ["AWS_NO_SIGN_REQUEST"] = "NO"
        else:
            # Workaround for rasterio bug
            os.environ["AWS_ACCESS_KEY_ID"] = "fake"
            os.environ["AWS_SECRET_ACCESS_KEY"] = "fake"
        credentials = configure_s3_access(aws_unsigned=unsigned)
    else:
        _LOG.warning("Environment variable $AWS_DEFAULT_REGION not set.  (This warning can be ignored if all data is stored locally.)")

ows_init_libs()

# Parse config file
if not os.environ.get("DEFER_CFG_PARSE"):
    get_config()

app = Flask(__name__.split('.')[0])
RequestID(app)


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
        SupportedSvcVersion("wcs", "1.0.0", handle_wcs1, WCS1Exception),
        SupportedSvcVersion("wcs", "2.0.0", handle_wcs2, WCS2Exception),
        SupportedSvcVersion("wcs", "2.1.0", handle_wcs2, WCS2Exception),
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
        elif op:
            # Should we return a WMS or WCS exception if there is no service specified?
            # Defaulting to WMS because that's what we already have.
            raise WMSException("Invalid service and/or request", locator="Service and request parameters")
        else:
            cfg = get_config()
            url = nocase_args.get('Host', nocase_args['url_root'])
            base_url = get_service_base_url(cfg.allowed_urls, url)
            return (render_template("index.html", cfg=cfg, supported=OWS_SUPPORTED, base_url=base_url),
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
def legend(layer, style, dates=None):
    cfg = get_config()
    product = cfg.product_index.get(layer)
    if not product:
        return ("Unknown Layer", 404, resp_headers({"Content-Type": "text/plain"}))
    if dates is None:
        args = lower_get_args()
        ndates = int(args.get("ndates", 0))
    else:
        ndates = len(dates)
    img = create_legend_for_style(product, style, ndates)
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


# Note: register your default metrics after all routes have been set up.
# Also note, that Gauge metrics registered as default will track the /metrics endpoint, and this can't be disabled at the moment.

if os.environ.get("prometheus_multiproc_dir", False):
    metrics.register_default(
        metrics.summary(
            'flask_ows_request_full_url', 'Request summary by request url',
            labels={
                'query_request': lambda: request.args.get('request'),
                'query_service': lambda: request.args.get('service'),
                'query_layers': lambda: request.args.get('layers'),
                'query_url': lambda: request.full_path
            }
        )
    )