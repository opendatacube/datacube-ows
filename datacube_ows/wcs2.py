from __future__ import absolute_import, division, print_function

from flask import render_template


from ows.common.v20.decoders import kvp_decode_get_capabilities
from ows.common.objects import WGS84BoundingBox
from ows.wcs.objects import (
    CoverageSummary, ServiceCapabilities, CoverageDescription, Field,
    Grid, RectifiedGrid
)
from ows.wcs.v20.objects import (
    GetCapabilitiesRequest, DescribeCoverageRequest, GetCoverageRequest
)
from ows.wcs.v20.decoders import kvp_decode_describe_coverage
from ows.wcs.v20.encoders import xml_encode_capabilities, xml_encode_coverage_descriptions

from datacube_ows.ogc_utils import resp_headers, get_service_base_url

from datacube_ows.ogc_exceptions import WCS2Exception
from datacube_ows.wcs_utils import WCS1GetCoverageRequest, get_coverage_data

from datacube_ows.ows_configuration import get_config

from datacube_ows.utils import log_call, opencensus_trace_call, get_opencensus_tracer


WCS_REQUESTS = ("DESCRIBECOVERAGE", "GETCOVERAGE")

tracer = get_opencensus_tracer()

@log_call
@opencensus_trace_call(tracer=tracer)
def handle_wcs2(nocase_args):
    operation = nocase_args.get("request", "").upper()
    if not operation:
        raise WCS2Exception("No operation specified", locator="Request parameter")
    elif operation == "GETCAPABILITIES":
        return get_capabilities(nocase_args)
    elif operation == "DESCRIBECOVERAGE":
        return desc_coverages(nocase_args)
    elif operation == "GETCOVERAGE":
        return get_coverage(nocase_args)
    else:
        raise WCS2Exception("Unrecognised operation: %s" % operation, locator="Request parameter")


@log_call
@opencensus_trace_call(tracer=tracer)
def get_capabilities(args):
    # Extract layer metadata from Datacube.
    cfg = get_config()
    url = args.get('Host', args['url_root'])
    base_url = get_service_base_url(cfg.allowed_urls, url)

    request = kvp_decode_get_capabilities(args)
    sections = request.sections or ['all']

    # TODO: check for invalid sections
    include_service_identification = False
    include_service_provider = False
    include_operations_metadata = False
    include_service_metadata = False
    include_coverage_summary = False

    if 'all' in sections:
        include_service_identification = True
        include_service_provider = True
        include_operations_metadata = True
        include_service_metadata = True
        include_coverage_summary = True
    if 'serviceidentification' in sections:
        include_service_identification = True
    if 'serviceprovider' in sections:
        include_service_provider = True
    if 'operationsmetadata' in sections:
        include_operations_metadata = True
    if 'servicemetadata' in sections:
        include_service_metadata = True
    if 'coveragesummary' in sections:
        include_coverage_summary = True

    capabilities = ServiceCapabilities.with_defaults_v20(
        service_url=base_url,
        allowed_operations=[
            'GetCapabilities', 'DescribeCoverage', 'GetCoverage'
        ],
        allow_post=False,
        title=cfg.title,
        abstract=cfg.abstract,
        keywords=cfg.keywords,
        fees=cfg.fees,
        access_constraints=[cfg.access_constraints],
        provider_name='',
        provider_site='',
        individual_name=cfg.contact_info['person'],
        organisation_name=cfg.contact_info['organisation'],
        position_name=cfg.contact_info['position'],
        phone_voice=cfg.contact_info['telephone'],
        phone_facsimile=cfg.contact_info['fax'],
        delivery_point=cfg.contact_info['address']['address'],
        city=cfg.contact_info['address']['city'],
        administrative_area=cfg.contact_info['address']['state'],
        postal_code=cfg.contact_info['address']['postcode'],
        country=cfg.contact_info['address']['country'],
        electronic_mail_address=cfg.contact_info['email'],
        online_resource=base_url,
        # hours_of_service=,
        # contact_instructions=,
        # role=,
        coverage_summaries=[
            CoverageSummary(
                identifier=product.name,
                coverage_subtype='RectifiedGridCoverage',
                title=product.title,
                wgs84_bbox=WGS84BoundingBox([
                    product.ranges['lon']['min'], product.ranges['lat']['min'],
                    product.ranges['lon']['max'], product.ranges['lat']['max'],
                ])
            )
            for product in cfg.product_index.values()
        ],
        formats_supported=[
            fmt['mime']
            for fmt in cfg.wcs_formats.values()
        ],
        crss_supported=[
            crs  # TODO: conversion to URL format
            for crs in cfg.published_CRSs
        ],
        interpolations_supported=None,  # TODO: find out interpolations
    )
    result = xml_encode_capabilities(capabilities,
                                     include_service_identification=include_service_identification,
                                     include_service_provider=include_service_provider,
                                     include_operations_metadata=include_operations_metadata,
                                     include_service_metadata=include_service_metadata,
                                     include_coverage_summary=include_coverage_summary)

    return (
        result.value,
        200,
        resp_headers({
            "Content-Type": result.content_type,
            "Cache-Control": "no-cache, max-age=0"
        })
    )

@log_call
@opencensus_trace_call(tracer=tracer)
def desc_coverages(args):
    # Note: Only WCS v1.0.0 is fully supported at this stage, so no version negotiation is necessary
    # Extract layer metadata from Datacube.
    cfg = get_config()

    request = kvp_decode_describe_coverage(args)

    products = []

    for coverage_id in request.coverage_ids:
        product = cfg.product_index.get(coverage_id)
        if product and product.wcs:
            products.append(product)
        else:
            raise WCS2Exception("Invalid coverage: %s" % coverage_id,
                                WCS2Exception.COVERAGE_NOT_DEFINED,
                                locator="Coverage parameter")

    coverage_descriptions = [
        CoverageDescription(
            identifier=product.name,
            range_type=[
                Field(
                    name=band_label,
                    description=band_label,
                    uom=band_label,
                    nil_values={
                        nv: 'invalid'
                        for nv in product.band_idx.band_nodata_vals()
                    }
                )
                for band_label in product.band_idx.band_labels()
            ],
            grid=RectifiedGrid(
                identifier='%s__grid' % product.name,
                limits=[
                    [0, 0],
                    [product.grid_high_x, product.grid_high_y],
                ],

                # TODO: flip axes when CRS is flipped

                origin=[
                    min(
                        product.ranges["bboxes"][product.native_CRS]["left"],
                        product.ranges["bboxes"][product.native_CRS]["right"],
                    ),
                    min(
                        product.ranges["bboxes"][product.native_CRS]["top"],
                        product.ranges["bboxes"][product.native_CRS]["bottom"],
                    ),
                ],
                offsets=[
                    [product.resolution_x, 0.0],
                    [0.0, product.resolution_y],
                ],
                axis_names=[
                    product.native_CRS_def["horizontal_coord"],
                    product.native_CRS_def["vertical_coord"],
                ],
                srs=product.native_CRS,
                # uom_labels=,
            ),
            native_format=cfg.native_wcs_format,
            coverage_subtype='RectifiedGridCoverage',
        )
        for product in products
    ]

    result = xml_encode_coverage_descriptions(coverage_descriptions)

    return (
        result.value,
        200,
        resp_headers({
            "Content-Type": result.content_type,
            "Cache-Control": "no-cache, max-age=0"
        })
    )


@log_call
@opencensus_trace_call(tracer=tracer)
def get_coverage(args):
    # Note: Only WCS v1.0.0 is fully supported at this stage, so no version negotiation is necessary
    req = WCS1GetCoverageRequest(args)
    data = get_coverage_data(req)
    return (
        req.format["renderer"](req, data),
        200,
        resp_headers({
            "Content-Type": req.format["mime"],
            'content-disposition': 'attachment; filename=%s.%s' % (req.product_name, req.format["extension"])
        })
    )
