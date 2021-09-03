# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import absolute_import, division, print_function

import traceback as tb

from flask import render_template
from ows.common.types import OWSException, Version
from ows.common.v20.encoders import xml_encode_exception_report

from datacube_ows.ogc_utils import resp_headers


class OGCException(Exception):
    INVALID_FORMAT = "InvalidFormat"
    CURRENT_UPDATE_SEQUENCE = "CurrentUpdateSequence"
    INVALID_UPDATE_SEQUENCE = "InvalidUpdateSequence"

    version = None
    schema_url = None

    # pylint: disable=super-init-not-called
    def __init__(self, msg, code=None, locator=None, http_response=400, valid_keys=None):
        self.http_response = http_response
        self.errors = []
        self.add_error(msg, code, locator, valid_keys)

    def add_error(self, msg, code=None, locator=None, valid_keys=None):
        self.errors.append({
            "msg": msg,
            "code": code,
            "locator": locator,
            "valid_keys": valid_keys
        })

    # pylint: disable=dangerous-default-value
    def exception_response(self, traceback=[]):
        return (render_template("ogc_error.xml",
                                exception=self,
                                traceback=traceback,
                                version=self.version,
                                schema_url=self.schema_url),
                self.http_response,
                resp_headers({"Content-Type": "application/xml"})
               )


class WMSException(OGCException):
    INVALID_CRS = "InvalidCRS"
    LAYER_NOT_DEFINED = "LayerNotDefined"
    STYLE_NOT_DEFINED = "StyleNotDefined"
    LAYER_NOT_QUERYABLE = "LayerNotQueryable"
    INVALID_POINT = "InvalidPoint"
    MISSING_DIMENSION_VALUE = "MissingDimensionValue"
    INVALID_DIMENSION_VALUE = "InvalidDimensionValue"
    OPERATION_NOT_SUPPORTED = "OperationNotSupported"

    version = "1.3.0"
    schema_url = "http://schemas.opengis.net/wms/1.3.0/exceptions_1_3_0.xsd"


class WMTSException(WMSException):
    INVALID_PARAMETER_VALUE = "InvalidParameterValue"
    version = "1.0.0"
    schema_url = "http://schemas.opengis.net/ows/1.1.0/owsExceptionReport.xsd"


class WCS1Exception(OGCException):
    COVERAGE_NOT_DEFINED = "CoverageNotDefined"
    MISSING_PARAMETER_VALUE = "MissingParameterValue"
    INVALID_PARAMETER_VALUE = "InvalidParameterValue"

    version = "1.2.0"
    schema_url = "http://schemas.opengis.net/wcs/1.0.0/OGC-exception.xsd"


class WCS2Exception(OGCException):
    NO_SUCH_COVERAGE = "NoSuchCoverage"
    INVALID_AXIS_LABEL = "InvalidAxisLabel"
    INVALID_SUBSETTING = "InvalidSubsetting"
    EMPTY_COVERAGE_ID_LIST = "emptyCoverageIdList"
    NO_SUCH_FIELD = "NoSuchField"
    ILLEGAL_FIELD_SEQUENCE = "IllegalFieldSequence"
    INVALID_COVERAGE_TYPE = "InvalidCoverageType"
    INVALID_SCALE_FACTOR = "InvalidScaleFactor"
    INVALID_EXTENT = "InvalidExtent"
    SCALE_AXIS_UNDEFINED = "ScaleAxisUndefined"
    NOT_A_CRS = "NotACrs"
    CRS_MISMATCH = "CrsMismatch"
    SUBSETTING_CRS_NOT_SUPPORTED = "SubsettingCrsNotSupported"
    OUTPUT_CRS_NOT_SUPPORTED = "OutputCrsNotSupported"
    INTERPOLATION_METHOD_NOT_SUPPORTED = "InterpolationMethodNotSupported"
    NO_SUCH_AXIS = "NoSuchAxis"
    MISSING_PARAMETER_VALUE = "MissingParameterValue"
    INVALID_PARAMETER_VALUE = "InvalidParameterValue"

    version = "2.0.1"
    schema_url = "http://schemas.opengis.net/wcs/2.0/wcsAll.xsd"

    # pylint: disable=dangerous-default-value
    def exception_response(self, traceback=[]):
        exceptions = [
            OWSException(
                code=error['code'],
                locator=error['locator'],
                text=[error['msg']] + tb.format_list(traceback)
            )
            for error in self.errors
        ]

        if traceback:
            exceptions[0].traceback = tb.format_list(traceback)

        result = xml_encode_exception_report(exceptions, Version.from_str(self.version))
        return (
            result.value,
            self.http_response,
            resp_headers({"Content-Type": "application/xml"})
        )
