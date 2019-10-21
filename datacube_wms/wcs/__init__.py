from datacube_wms.utils import log_call, opencensus_trace_call, get_opencensus_tracer

from .v10 import handle_wcs as handle_wcs_v10
from .v20 import handle_wcs as handle_wcs_v20



tracer = get_opencensus_tracer()

WCS_REQUESTS = ("DESCRIBECOVERAGE", "GETCOVERAGE")

@log_call
@opencensus_trace_call(tracer=tracer)
def handle_wcs(nocase_args):


    version = nocase_args.get("request", "2.0.0")
    if not operation:
        raise WCS1Exception("No operation specified", locator="Request parameter")
    elif operation == "GETCAPABILITIES":
        return get_capabilities(nocase_args)
    elif operation == "DESCRIBECOVERAGE":
        return desc_coverages(nocase_args)
    elif operation == "GETCOVERAGE":
        return get_coverage(nocase_args)
    else:
        raise WCS1Exception("Unrecognised operation: %s" % operation, locator="Request parameter")

