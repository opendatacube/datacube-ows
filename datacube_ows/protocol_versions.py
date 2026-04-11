# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import annotations

import contextlib
import re
from collections.abc import Callable, Mapping
from typing import TypeAlias

from datacube_ows.ogc_exceptions import (
    WCS1Exception,
    WCS2Exception,
    WMSException,
    WMTSException,
)
from datacube_ows.wcs1 import handle_wcs1
from datacube_ows.wcs2 import handle_wcs2
from datacube_ows.wms import handle_wms
from datacube_ows.wmts import handle_wmts

TYPE_CHECKING = False
if TYPE_CHECKING:
    from collections.abc import Sequence

    from datacube_ows.ogc_exceptions import OGCException
    from datacube_ows.ows_configuration import OWSConfig

FlaskResponse: TypeAlias = tuple[str | bytes, int, dict[str, str]]
FlaskHandler: TypeAlias = Callable[[Mapping[str, str]], FlaskResponse]


class SupportedSvcVersion:
    def __init__(
        self,
        service: str,
        version: str,
        # FIXME: second argument should be dict[str, str | None].
        router: Callable[[OWSConfig, dict[str, str]], FlaskResponse],
        exception_class: type[OGCException],
    ) -> None:
        self.service = service.lower()
        self.service_upper = service.upper()
        self.version = version
        self.version_parts = [int(i) for i in version.split(".")]
        assert len(self.version_parts) == 3
        self.router = router
        self.exception_class = exception_class


class SupportedSvc:
    def __init__(
        self,
        versions: Sequence[SupportedSvcVersion],
        default_exception_class: type[OGCException] | None = None,
    ) -> None:
        if not versions:
            raise RuntimeError("Empty versions sequence")
        self.versions = sorted(versions, key=lambda x: x.version_parts)
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

    @staticmethod
    def _clean_version_parts(unclean: list[str]) -> list[int]:
        clean = []
        for part in unclean:
            try:
                clean.append(int(part))
                continue
            except ValueError:
                pass
            with contextlib.suppress(ValueError):
                clean.append(int(re.split(r"[^\d]", part)[0]))
            break
        return clean

    def negotiated_version(self, request_version: str | None) -> SupportedSvcVersion:
        if not request_version:
            return self.versions[-1]
        parts: list[str] = list(request_version.split("."))
        rv_parts: list[int] = self._clean_version_parts(parts)
        while len(rv_parts) < 3:
            rv_parts.append(0)
        for v in reversed(self.versions):
            if rv_parts >= v.version_parts:
                return v
        # The constructor ensures that self.versions is not empty, so this is safe.
        return self.versions[0]

    def activated(self, cfg: OWSConfig) -> bool:
        return bool(getattr(cfg, self.service))


OWS_SUPPORTED = {
    "wms": SupportedSvc(
        [SupportedSvcVersion("wms", "1.3.0", handle_wms, WMSException)]
    ),
    "wmts": SupportedSvc(
        [SupportedSvcVersion("wmts", "1.0.0", handle_wmts, WMTSException)]
    ),
    "wcs": SupportedSvc(
        [
            SupportedSvcVersion("wcs", "1.0.0", handle_wcs1, WCS1Exception),
            SupportedSvcVersion("wcs", "2.0.0", handle_wcs2, WCS2Exception),
            SupportedSvcVersion("wcs", "2.1.0", handle_wcs2, WCS2Exception),
        ]
    ),
}


def supported_versions() -> dict[str, SupportedSvc]:
    return OWS_SUPPORTED
