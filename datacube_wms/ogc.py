from __future__ import absolute_import, division, print_function
import sys
import traceback

from flask import Flask, request, render_template

from datacube_wms.wms import handle_wms
from datacube_wms.wcs import handle_wcs
from datacube_wms.ogc_exceptions import OGCException, WCS1Exception, WMSException

from datacube_wms.wms_layers import get_service_cfg



app = Flask(__name__.split('.')[0])


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
    nocase_args = lower_get_args()
    nocase_args['referer'] = request.headers.get('Referer', None)
    service = nocase_args.get("service","").upper()
    svc_cfg = get_service_cfg()
    try:
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
        else:
            # Should we return a WMS or WCS exception if there is no service specified?
            # Defaulting to WMS because that's what we already have.
            raise WMSException("Invalid service", locator="Service parameter")
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



