# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import logging

from flask import request
from ows.common import WGS84BoundingBox
from ows.common.v20.decoders import kvp_decode_get_capabilities
from ows.gml import Grid, IrregularAxis, RegularAxis, SpatioTemporalType
from ows.swe import Field
from ows.wcs import CoverageDescription, CoverageSummary, ServiceCapabilities
from ows.wcs.v20 import encoders as encoders_v20
from ows.wcs.v20.decoders import (kvp_decode_describe_coverage,
                                  kvp_decode_get_coverage)
from ows.wcs.v21 import encoders as encoders_v21

from datacube_ows.data import json_response
from datacube_ows.ogc_exceptions import WCS2Exception
from datacube_ows.ogc_utils import (cache_control_headers,
                                    get_service_base_url, resp_headers)
from datacube_ows.ows_configuration import get_config
from datacube_ows.query_profiler import QueryProfiler
from datacube_ows.utils import log_call
from datacube_ows.wcs2_utils import get_coverage_data

_LOG = logging.getLogger(__name__)

WCS_REQUESTS = ("DESCRIBECOVERAGE", "GETCOVERAGE")


@log_call
def handle_wcs2(nocase_args):
    operation = nocase_args.get("request", "").upper()
    if not operation:
        raise WCS2Exception("No operation specified", locator="Request parameter")
    elif operation == "GETCAPABILITIES":
        return get_capabilities(nocase_args)
    elif operation == "DESCRIBECOVERAGE":
        return desc_coverages(nocase_args)
    elif operation == "GETCOVERAGE":
        return get_coverage(request.args.lists(), bool(nocase_args.get("ows_stats")))
    else:
        raise WCS2Exception("Unrecognised operation: %s" % operation, locator="Request parameter")


@log_call
def get_capabilities(args):
    # Extract layer metadata from Datacube.
    cfg = get_config()
    url = args.get('Host', args['url_root'])
    base_url = get_service_base_url(cfg.allowed_urls, url)

    request_obj = kvp_decode_get_capabilities(args)
    sections = request_obj.sections or ['all']

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
        service_url =base_url + '/wcs',
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
        individual_name=cfg.contact_info.person,
        organisation_name=cfg.contact_info.organisation,
        position_name=cfg.contact_info.position,
        phone_voice=cfg.contact_info.telephone,
        phone_facsimile=cfg.contact_info.fax,
        delivery_point=cfg.contact_info.address.address,
        city=cfg.contact_info.address.city,
        administrative_area=cfg.contact_info.address.state,
        postal_code=cfg.contact_info.address.postcode,
        country=cfg.contact_info.address.country,
        electronic_mail_address=cfg.contact_info.email,
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
            if product.ready and not product.hide and product.wcs
        ],
        formats_supported=[
            fmt.mime
            for fmt in cfg.wcs_formats
            if 2 in fmt.renderers
        ],
        crss_supported=[
            crs  # TODO: conversion to URL format
            for crs in cfg.published_CRSs
        ],
        interpolations_supported=None,  # TODO: find out interpolations
    )
    result = encoders_v20.xml_encode_capabilities(
        capabilities,
        include_service_identification=include_service_identification,
        include_service_provider=include_service_provider,
        include_operations_metadata=include_operations_metadata,
        include_service_metadata=include_service_metadata,
        include_coverage_summary=include_coverage_summary
    )

    headers = cache_control_headers(cfg.wms_cap_cache_age)
    headers["Content-Type"] = result.content_type
    return (
        result.value,
        200,
        cfg.response_headers(headers)
    )


def create_coverage_description(cfg, product):
    axes = [
        RegularAxis(
            label=product.native_CRS_def["horizontal_coord"],
            index_label='i',
            lower_bound=min(
                product.ranges["bboxes"][product.native_CRS]["left"],
                product.ranges["bboxes"][product.native_CRS]["right"],
            ),
            upper_bound=max(
                product.ranges["bboxes"][product.native_CRS]["left"],
                product.ranges["bboxes"][product.native_CRS]["right"],
            ),
            resolution=product.resolution_x,
            uom='deg',
            size=product.grid_high_x,
        ),
        RegularAxis(
            label=product.native_CRS_def["vertical_coord"],
            index_label='j',
            lower_bound=min(
                product.ranges["bboxes"][product.native_CRS]["top"],
                product.ranges["bboxes"][product.native_CRS]["bottom"],
            ),
            upper_bound=max(
                product.ranges["bboxes"][product.native_CRS]["top"],
                product.ranges["bboxes"][product.native_CRS]["bottom"],
            ),
            resolution=product.resolution_y,
            uom='deg',
            size=product.grid_high_y,
        ),
    ]

    # swap axes if necessary
    if product.native_CRS_def.get("vertical_coord_first"):
        axes = list(reversed(axes))

    if product.regular_time_axis:
        start, end = product.time_range()
        size = (end - start).days // product.time_axis_interval
        axes.append(
            RegularAxis(
                label='time',
                index_label='k',
                lower_bound=start.isoformat(),
                upper_bound=end.isoformat(),
                resolution=f'P{product.time_axis_interval}D',
                uom="ISO-8601",
                type=SpatioTemporalType.TEMPORAL,
                size=size,
            )
        )
    else:
        axes.append(
            IrregularAxis(
                label='time',
                index_label='k',
                positions=[
                    f'{t.isoformat()}T00:00:00.000Z'
                    for t in product.ranges['times']
                ],
                uom='ISO-8601',
                type=SpatioTemporalType.TEMPORAL,
            )
        )

    return CoverageDescription(
        identifier=product.name,
        title=product.title,
        abstract=product.definition.get('description'),
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
        grid=Grid(
            axes=axes,
            srs=product.native_CRS,
        ),
        native_format=cfg.wcs_formats_by_name[product.native_format].mime,
        coverage_subtype='RectifiedGridCoverage',
    )


@log_call
def desc_coverages(args):
    cfg = get_config()

    request_obj = kvp_decode_describe_coverage(args)

    products = []

    for coverage_id in request_obj.coverage_ids:
        product = cfg.product_index.get(coverage_id)
        if product and product.wcs:
            products.append(product)
        else:
            raise WCS2Exception("Invalid coverage: %s" % coverage_id,
                                WCS2Exception.NO_SUCH_COVERAGE,
                                locator=coverage_id)

    coverage_descriptions = [
        create_coverage_description(cfg, product)
        for product in products
    ]

    version = request_obj.version

    if version == (2, 0):
        result = encoders_v20.xml_encode_coverage_descriptions(coverage_descriptions)
    elif version == (2, 1):
        result = encoders_v21.xml_encode_coverage_descriptions(coverage_descriptions)
    else:
        raise WCS2Exception("Unsupported version: %s" % version,
                            WCS2Exception.INVALID_PARAMETER_VALUE,
                            locator="version")
    min_cache_age = min(p.resource_limits.wcs_desc_cache_rule for p in products)
    headers = cache_control_headers(min_cache_age)
    headers["Content-Type"] = result.content_type
    return (
        result.value,
        200,
        resp_headers(headers)
    )


@log_call
def get_coverage(args, ows_stats=False):
    request_obj = kvp_decode_get_coverage(args)
    qprof = QueryProfiler(ows_stats)
    output, headers = get_coverage_data(request_obj, qprof)
    if ows_stats:
        return json_response(qprof.profile())
    return (
        output,
        200,
        resp_headers(headers)
    )
