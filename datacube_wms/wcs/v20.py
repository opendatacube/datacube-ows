from datacube_wms.ogc_exceptions import WCS2Exception
from datacube_wms.ogc_utils import resp_headers, get_service_base_url
from datacube_wms.wms_layers import get_layers, get_service_cfg

from eoxserver.core.decoders import xml, kvp, typelist, lower, enum
from eoxserver.render.coverage.objects import (
    Coverage, Grid, Origin, RangeType, Field, Axis, IrregularAxis
)
from eoxserver.services.ows.wcs.v20.encoders import OWS, WCS, WCS20CapabilitiesXMLEncoder
from eoxserver.services.ows.wcs.v21.encoders import WCS21XMLEncoder
from eoxserver.services.ows.wcs.v20.util import (
    nsmap, parse_subset_kvp, parse_subset_xml, parse_range_subset_kvp,
    parse_range_subset_xml,
    parse_scaleaxis_kvp, parse_scalesize_kvp, parse_scaleextent_kvp,
    parse_scaleaxis_xml, parse_scalesize_xml, parse_scaleextent_xml,
)


class WCS2Exception(Exception):
    pass

def handle_wcs(nocase_args):
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



class CapabilitiesEncoder(WCS20CapabilitiesXMLEncoder):
    def get_conf(self):
        return DummyConf()

    def encode_service_metadata(self):
        return OWS("ServiceMetadata")

    def encode_service_identification(self, *args, **kwargs):
        return OWS("ServiceIdentification")

    def encode_operations_metadata(self, *args, **kwargs):
        return OWS("OperationsMetadata")

class DummyConf:
    def __getattr__(self, name):
        return ""

def get_capabilities(args):
    encoder = CapabilitiesEncoder()

    return (
        encoder.serialize(
            encoder.encode_capabilities(args.get('sections', 'all'), DummyConf())
        ),
        200,
        resp_headers({
            "Content-Type": "application/xml",
            "Cache-Control": "no-cache, max-age=0"
        })
    )


def get_coverage_object(svc_cfg, product):
    crs = svc_cfg.published_CRSs[product.native_CRS]
    bbox = product.ranges["bboxes"][product.native_CRS]

    return Coverage(
        identifier=product.name,
        eo_metadata=None,
        range_type=RangeType('%s__range_type' % product.name, [
            Field(
                index=i,
                identifier=band_label,
                description=band_label,
                definition='',
                unit_of_measure='',
                wavelength=None,
                significant_figures=None,
                allowed_values=None,
                nil_values=[(str(product.band_idx.nodata_val(band_label)), 'nodata')],
                data_type=None,
                data_type_range=None,
            ) for i, band_label in enumerate(product.band_idx.band_labels())
        ]),
        grid=Grid(
            product.native_CRS, [
                Axis(
                    crs['horizontal_coord'],
                    0,
                    product.resolution_x,
                    'm' if crs['geographic'] else 'deg'
                ),
                Axis(
                    crs['vertical_coord'],
                    0,
                    product.resolution_y,
                    'm' if crs['geographic'] else 'deg'
                ),
                IrregularAxis('time', 2, product.ranges['times'], 's')
            ]
        ),
        origin=Origin([
            min(bbox["left"], bbox["right"]),
            min(bbox["top"], bbox["bottom"])
        ]),
        size=[product.grid_high_x, product.grid_high_y],
        arraydata_locations=[],
        metadata_locations=[],
        native_format=svc_cfg.wcs_formats[svc_cfg.native_wcs_format]['mime'],
    )

def desc_coverages(args):
    try:
        coverage_ids = [s.strip() for s in args['coverageid'].split(',')]
    except KeyError:
        raise WCS2Exception("Missing coverageid parameter", locator="coverageid")

    svc_cfg = get_service_cfg(refresh=True)
    layers = get_layers(refresh=True)

    products = []
    for coverage_id in coverage_ids:
        product = layers.product_index.get(coverage_id)
        if product:
            products.append(product)
        else:
            raise WCS2Exception("Invalid coverage: %s" % coverage_id,
                                WCS2Exception.COVERAGE_NOT_DEFINED,
                                locator="Coverage parameter")

    # TODO: make a coverge object from each of the 'products'

    coverages = [
        get_coverage_object(svc_cfg, product)
        for product in products
    ]

    encoder = WCS21XMLEncoder()
    return (
        encoder.serialize(
            encoder.encode_coverage_descriptions(coverages)
        ),
        200,
        resp_headers({
            "Content-Type": "application/xml",
            "Cache-Control": "no-cache, max-age=0"
        })
    )


def get_coverage(args):
    decoder = WCS20GetCoverageKVPDecoder(args)

    try:
        coverage_id = decoder.coverage_id
    except KeyError:
        raise WCS2Exception("Missing coverageid parameter", locator="coverageid")

    svc_cfg = get_service_cfg(refresh=True)
    layers = get_layers(refresh=True)

    product = layers.product_index.get(coverage_id)

    if not product:
        raise WCS2Exception("Invalid coverage: %s" % coverage_id,
                            WCS2Exception.COVERAGE_NOT_DEFINED,
                            locator="COVERAGE parameter")

    if decoder.format:
        if decoder.format not in svc_cfg.wcs_formats:
            raise WCS2Exception("Unsupported format: %s" % decoder.format,
                                WCS2Exception.INVALID_PARAMETER_VALUE,
                                locator="FORMAT parameter")
    elif not svc_cfg.native_wcs_format:
        raise WCS2Exception("Missing parameter format 'format'",
                            WCS2Exception.MISSING_PARAMETER_VALUE,
                            locator="FORMAT parameter")

    fmt_cfg = svc_cfg.wcs_formats[decoder.format or svc_cfg.native_wcs_format]

    

    return (
        '',
        200,
        resp_headers({
            "Content-Type": "application/xml",
            "Cache-Control": "no-cache, max-age=0"
        })
    )




def parse_interpolation(raw):
    """ Returns a unified string denoting the interpolation method used.
    """
    if raw.startswith("http://www.opengis.net/def/interpolation/OGC/1/"):
        raw = raw[len("http://www.opengis.net/def/interpolation/OGC/1/"):]

    value = raw.lower()

    if value not in SUPPORTED_INTERPOLATIONS:
        raise Exception(
            "Interpolation method '%s' is not supported." % raw
        )
    return value.upper()

class WCS20GetCoverageKVPDecoder(kvp.Decoder):
    coverage_id = kvp.Parameter("coverageid", num=1)
    subsets     = kvp.Parameter("subset", type=parse_subset_kvp, num="*")
    scalefactor = kvp.Parameter("scalefactor", type=float, num="?")
    scaleaxes   = kvp.Parameter("scaleaxes", type=typelist(parse_scaleaxis_kvp, ","), default=(), num="?")
    scalesize   = kvp.Parameter("scalesize", type=typelist(parse_scalesize_kvp, ","), default=(), num="?")
    scaleextent = kvp.Parameter("scaleextent", type=typelist(parse_scaleextent_kvp, ","), default=(), num="?")
    rangesubset = kvp.Parameter("rangesubset", type=parse_range_subset_kvp, num="?")
    format      = kvp.Parameter("format", num="?")
    subsettingcrs = kvp.Parameter("subsettingcrs", num="?")
    outputcrs   = kvp.Parameter("outputcrs", num="?")
    mediatype   = kvp.Parameter("mediatype", num="?")
    interpolation = kvp.Parameter("interpolation", type=parse_interpolation, num="?")


class WCS20GetCoverageXMLDecoder(xml.Decoder):
    coverage_id = xml.Parameter("wcs:CoverageId/text()", num=1, locator="coverageid")
    subsets     = xml.Parameter("wcs:DimensionTrim", type=parse_subset_xml, num="*", locator="subset")
    scalefactor = xml.Parameter("wcs:Extension/scal:ScaleByFactor/scal:scaleFactor/text()", type=float, num="?", locator="scalefactor")
    scaleaxes   = xml.Parameter("wcs:Extension/scal:ScaleByAxesFactor/scal:ScaleAxis", type=parse_scaleaxis_xml, num="*", default=(), locator="scaleaxes")
    scalesize   = xml.Parameter("wcs:Extension/scal:ScaleToSize/scal:TargetAxisSize", type=parse_scalesize_xml, num="*", default=(), locator="scalesize")
    scaleextent = xml.Parameter("wcs:Extension/scal:ScaleToExtent/scal:TargetAxisExtent", type=parse_scaleextent_xml, num="*", default=(), locator="scaleextent")
    rangesubset = xml.Parameter("wcs:Extension/rsub:RangeSubset", type=parse_range_subset_xml, num="?", locator="rangesubset")
    format      = xml.Parameter("wcs:format/text()", num="?", locator="format")
    subsettingcrs = xml.Parameter("wcs:Extension/crs:subsettingCrs/text()", num="?", locator="subsettingcrs")
    outputcrs   = xml.Parameter("wcs:Extension/crs:outputCrs/text()", num="?", locator="outputcrs")
    mediatype   = xml.Parameter("wcs:mediaType/text()", num="?", locator="mediatype")
    interpolation = xml.Parameter("wcs:Extension/int:Interpolation/int:globalInterpolation/text()", type=parse_interpolation, num="?", locator="interpolation")

    namespaces = nsmap