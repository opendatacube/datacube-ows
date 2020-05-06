from __future__ import absolute_import, division, print_function

from flask import render_template

from datacube_ows.ogc_utils import get_service_base_url

from datacube_ows.ogc_exceptions import WCS1Exception
from datacube_ows.wcs_utils import WCS1GetCoverageRequest, get_coverage_data

from datacube_ows.ows_configuration import get_config

from datacube_ows.utils import log_call, opencensus_trace_call, get_opencensus_tracer


WCS_REQUESTS = ("DESCRIBECOVERAGE", "GETCOVERAGE")

tracer = get_opencensus_tracer()

@log_call
@opencensus_trace_call(tracer=tracer)
def handle_wcs(nocase_args):
    operation = nocase_args.get("request", "").upper()
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


@log_call
@opencensus_trace_call(tracer=tracer)
def get_capabilities(args):
    # TODO: Handle updatesequence request parameter for cache consistency.
    section = args.get("section")
    if section:
        section = section.lower()
    show_service = False
    show_capability = False
    show_content_metadata = False
    if section is None or section == "/":
        show_service = True
        show_capability = True
        show_content_metadata = True
    elif section == "/wcs_capabilities/service":
        show_service = True
    elif section == "/wcs_capabilities/capability":
        show_capability = True
    elif section == "/wcs_capabilities/contentmetadata":
        show_content_metadata = True
    else:
        raise WCS1Exception("Invalid section: %s" % section,
                            WCS1Exception.INVALID_PARAMETER_VALUE,
                            locator="Section parameter")

    # Extract layer metadata from Datacube.
    cfg = get_config()
    url = args.get('Host', args['url_root'])
    base_url = get_service_base_url(cfg.allowed_urls, url)
    return (
        render_template("wcs_capabilities.xml",
                        show_service=show_service,
                        show_capability=show_capability,
                        show_content_metadata=show_content_metadata,
                        cfg=cfg,
                        base_url=base_url),
        200,
        cfg.response_headers({
            "Content-Type": "application/xml",
            "Cache-Control": "no-cache, max-age=0"
        }))


@log_call
@opencensus_trace_call(tracer=tracer)
def desc_coverages(args):
    # Note: Only WCS v1.0.0 is fully supported at this stage, so no version negotiation is necessary
    # Extract layer metadata from Datacube.
    cfg = get_config()

    coverages = args.get("coverage")
    products = []
    if coverages:
        coverages = coverages.split(",")
        for c in coverages:
            p = cfg.product_index.get(c)
            if p and p.wcs:
                products.append(p)
            else:
                raise WCS1Exception("Invalid coverage: %s" % c,
                                    WCS1Exception.COVERAGE_NOT_DEFINED,
                                    locator="Coverage parameter")
    else:
        for p in cfg.product_index.values():
            if p.wcs:
                products.append(p)

    return (
        render_template("wcs_desc_coverage.xml",
                        cfg=cfg,
                        products=products),
        200,
        cfg.response_headers({
            "Content-Type": "application/xml",
            "Cache-Control": "max-age=10"
        })
    )


@log_call
@opencensus_trace_call(tracer=tracer)
def get_coverage(args):
    # Note: Only WCS v1.0.0 is fully supported at this stage, so no version negotiation is necessary
    cfg = get_config()
    req = WCS1GetCoverageRequest(args)
    if req.format["multi-time"] and len(req.times) > 1:
        raise WCS1Exception("Multi-time requests are not currently supported for WCS1",
                            WCS1Exception.INVALID_PARAMETER_VALUE,
                            locator="Time parameter")
    data = get_coverage_data(req)
    return (
        req.format["renderer"](req, data),
        200,
        cfg.response_headers({
            "Content-Type": req.format["mime"],
            'content-disposition': 'attachment; filename=%s.%s' % (req.product_name, req.format["extension"])
        })
    )
