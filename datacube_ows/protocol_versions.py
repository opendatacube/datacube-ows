# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from datacube_ows.ogc_exceptions import (WCS1Exception, WCS2Exception,
                                         WMSException, WMTSException)
from datacube_ows.ows_configuration import get_config
from datacube_ows.wcs1 import handle_wcs1
from datacube_ows.wcs2 import handle_wcs2
from datacube_ows.wms import handle_wms
from datacube_ows.wmts import handle_wmts


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


def supported_versions():
    return OWS_SUPPORTED
