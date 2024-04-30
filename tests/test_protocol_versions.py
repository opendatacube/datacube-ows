# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import pytest

import datacube_ows.protocol_versions


class DummyException1(Exception):
    pass

class DummyException2(Exception):
    pass

def fake_router(*args, **kwargs):
    return None

@pytest.fixture
def supported_service():
    return datacube_ows.protocol_versions.SupportedSvc([
        datacube_ows.protocol_versions.SupportedSvcVersion("wxs", "1.2.7", fake_router, DummyException1),
        datacube_ows.protocol_versions.SupportedSvcVersion("wxs", "1.13.0", fake_router, DummyException1),
        datacube_ows.protocol_versions.SupportedSvcVersion("wxs", "2.0.0", fake_router, DummyException1),
    ], DummyException2)

def test_default_exception(supported_service):
    assert supported_service.default_exception_class == DummyException2


def test_version_negotiation(supported_service):
    assert supported_service.negotiated_version("1.0").version == "1.2.7"
    assert supported_service.negotiated_version("1.2").version == "1.2.7"
    assert supported_service.negotiated_version("1.0.0").version == "1.2.7"
    assert supported_service.negotiated_version("1.2.1").version == "1.2.7"
    assert supported_service.negotiated_version("1.2.7").version == "1.2.7"
    assert supported_service.negotiated_version("1.2.8").version == "1.2.7"
    assert supported_service.negotiated_version("1.13.0").version == "1.13.0"
    assert supported_service.negotiated_version("1.13.100").version == "1.13.0"
    assert supported_service.negotiated_version("2.0").version == "2.0.0"
    assert supported_service.negotiated_version("2.7.22").version == "2.0.0"


def test_version_cleaner(supported_service):
    assert supported_service._clean_version_parts(["0", "1", "2"]) == [0, 1, 2]
    assert supported_service._clean_version_parts(["0", "1", "2/spam"]) == [0, 1, 2]
    assert supported_service._clean_version_parts(["0", "1spam", "2"]) == [0, 1]
    assert supported_service._clean_version_parts(["0?bacon", "1/eggs", "2/spam"]) == [0]
    assert supported_service._clean_version_parts(["spam", "spam", "spam"]) == []
