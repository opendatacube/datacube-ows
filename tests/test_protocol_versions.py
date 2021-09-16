import pytest
import datacube_ows.protocol_versions

class TestException1(Exception):
    pass

class TestException2(Exception):
    pass

def fake_router(*args, **kwargs):
    return None

@pytest.fixture
def supported_service():
    return datacube_ows.protocol_versions.SupportedSvc([
        datacube_ows.protocol_versions.SupportedSvcVersion("wxs", "1.2.7", fake_router, TestException1),
        datacube_ows.protocol_versions.SupportedSvcVersion("wxs", "1.13.0", fake_router, TestException1),
        datacube_ows.protocol_versions.SupportedSvcVersion("wxs", "2.0.0", fake_router, TestException1),
    ], TestException2)

def test_default_exception(supported_service):
    assert supported_service.default_exception_class == TestException2

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
