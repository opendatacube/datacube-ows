
from flask import render_template

from datacube_wms.ogc_utils import resp_headers


class OGCException(Exception):
    INVALID_FORMAT = "InvalidFormat"
    CURRENT_UPDATE_SEQUENCE = "CurrentUpdateSequence"
    INVALID_UPDATE_SEQUENCE = "InvalidUpdateSequence"

    version = None
    schema_url = None

    def __init__(self, msg, code=None, locator=None, http_response=400):
        self.http_response = http_response
        self.errors = []
        self.add_error(msg, code, locator)

    def add_error(self, msg, code=None, locator=None):
        self.errors.append({
            "msg": msg,
            "code": code,
            "locator": locator
        })

    def exception_response(self, traceback=[]):
        return (render_template("wms_error.xml",
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
    schema_url="http://schemas.opengis.net/wms/1.3.0/exceptions_1_3_0.xsd"


class WCS1Exception(OGCException):
    COVERAGE_NOT_DEFINED = "CoverageNotDefined"
    MISSING_PARAMETER_VALUE = "MissingParameterValue"
    INVALID_PARAMETER_VALUE = "InvalidParameterValue"

    version = "1.2.0"
    schema_url="http://schemas.opengis.net/wcs/1.0.0/OGC-exception.xsd"


def wms_exception(e, traceback=[]):
    return (render_template("wms_error.xml",
                            exception=e,
                            traceback=traceback,
                            version="1.3.0",
                            schema_url="http://schemas.opengis.net/wms/1.3.0/exceptions_1_3_0.xsd"),
            e.http_response,
            resp_headers({"Content-Type": "application/xml"})
           )

