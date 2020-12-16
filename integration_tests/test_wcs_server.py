import pytest

from owslib.wcs import WebCoverageService
from owslib.util import ServiceException
import requests
from requests.exceptions import HTTPError
import requests
from urllib import request
from lxml import etree

from datacube_ows.ows_configuration import get_config, OWSConfig
from integration_tests.utils import WCS20Extent, ODCExtent


def get_xsd(name):
    # TODO: Get XSD's for different versions
    xsd_f = request.urlopen("http://schemas.opengis.net/wcs/" + name)
    schema_doc = etree.parse(xsd_f)

    return etree.XMLSchema(schema_doc)


def check_wcs_error(url, expected_error_message=None, expected_status_code=400, params=None):
    if params is None:
        params = {}
    resp = requests.get(url, params=params, timeout=10.0)
    assert resp.status_code == expected_status_code

    assert expected_error_message in resp.text
    resp_xml = etree.XML(resp.content)
    assert resp_xml is not None


def test_no_request(ows_server):
    # Make empty request to server:
    check_wcs_error(ows_server.url + "/wcs", "No operation specified", 400)


def test_invalid_operation(ows_server):
    # Make invalid operation request to server:
    check_wcs_error(ows_server.url + "/wcs?request=NoSuchOperation", "Unrecognised operation: NOSUCHOPERATION", 400)


def test_getcap_badsvc(ows_server):
    # Make bad service request to server:
    check_wcs_error(ows_server.url + "/wcs?request=GetCapabilities&service=NotWCS", "Invalid service", 400)


def test_wcs1_getcap(ows_server):
    resp = request.urlopen(ows_server.url + "/wcs?request=GetCapabilities&service=WCS&version=1.0.0", timeout=10)

    # Confirm success
    assert resp.code == 200

    # Validate XML Schema
    resp_xml = etree.parse(resp.fp)
    gc_xds = get_xsd("1.0.0/wcsCapabilities.xsd")
    assert gc_xds.validate(resp_xml)

def test_wcs1_server(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0", timeout=120)

    # Ensure that we have at least some layers available
    contents = list(wcs.contents)
    assert contents


def test_wcs1_getcov_nocov(ows_server):
    check_wcs_error(ows_server.url + "/wcs", params={
                        "request": "GetCoverage",
                        "service": "WCS",
                        "version": "1.0.0",
                    },
                    expected_error_message="No coverage specified",
                    expected_status_code=400)


def test_wcs1_getcov_nofmt(ows_server):
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0", timeout=120)
    contents = list(wcs.contents)
    test_layer_name = contents[0]
    check_wcs_error(ows_server.url + "/wcs", params={
                        "request": "GetCoverage",
                        "service": "WCS",
                        "version": "1.0.0",
                        "coverage": test_layer_name,
                    },
                    expected_error_message="No FORMAT parameter supplied",
                    expected_status_code=400)

def test_wcs1_getcov_bad_respcrs(ows_server):
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0", timeout=120)
    contents = list(wcs.contents)
    test_layer_name = contents[0]
    check_wcs_error(ows_server.url + "/wcs", params={
                        "request": "GetCoverage",
                        "service": "WCS",
                        "version": "1.0.0",
                        "coverage": test_layer_name,
                        "crs": 'EPSG:4326',
                        "response_crs": 'PEGS:2346',
                        "format": 'GeoTIFF',
                    },
                    expected_error_message="PEGS:2346 is not a supported CRS",
                    expected_status_code=400)

def test_wcs1_getcov_nobbox(ows_server):
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0", timeout=120)
    contents = list(wcs.contents)
    test_layer_name = contents[0]
    check_wcs_error(ows_server.url + "/wcs", params={
                        "request": "GetCoverage",
                        "service": "WCS",
                        "version": "1.0.0",
                        "coverage": test_layer_name,
                        "crs": 'EPSG:4326',
                        "format": 'GeoTIFF',
                    },
                    expected_error_message="No BBOX parameter supplied",
                    expected_status_code=400)

def test_wcs1_getcov_no_meas(ows_server):
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0", timeout=120)
    contents = list(wcs.contents)
    test_layer_name = contents[0]
    cfg = get_config(refresh=True)
    layer = cfg.product_index[test_layer_name]
    extents = ODCExtent(layer).wcs1_args(space=ODCExtent.CENTRAL_SUBSET_FOR_TIMES, time=ODCExtent.FIRST)
    check_wcs_error(ows_server.url + "/wcs", params={
                        "request": "GetCoverage",
                        "service": "WCS",
                        "version": "1.0.0",
                        "coverage": test_layer_name,
                        "crs": 'EPSG:4326',
                        "format": 'GeoTIFF',
                        "bbox": extents["bbox"],
                        "time": extents["times"],
                        "exceptions": "spam",
                        "measurements": ""
                    },
                    expected_error_message="No measurements supplied",
                    expected_status_code=400)

def test_wcs1_getcov_multi_style(ows_server):
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0", timeout=120)
    contents = list(wcs.contents)
    test_layer_name = contents[0]
    cfg = get_config(refresh=True)
    layer = cfg.product_index[test_layer_name]
    extents = ODCExtent(layer).wcs1_args(space=ODCExtent.CENTRAL_SUBSET_FOR_TIMES, time=ODCExtent.FIRST)
    check_wcs_error(ows_server.url + "/wcs", params={
                        "request": "GetCoverage",
                        "service": "WCS",
                        "version": "1.0.0",
                        "coverage": test_layer_name,
                        "crs": 'EPSG:4326',
                        "format": 'GeoTIFF',
                        "bbox": extents["bbox"],
                        "time": extents["times"],
                        "exceptions": "spam",
                        "styles": "simple_rgb,ndvi"
                    },
                    expected_error_message="Multiple style parameters not supported",
                    expected_status_code=400)

def test_wcs1_getcov_bad_meas(ows_server):
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0", timeout=120)
    contents = list(wcs.contents)
    test_layer_name = contents[0]
    cfg = get_config(refresh=True)
    layer = cfg.product_index[test_layer_name]
    extents = ODCExtent(layer).wcs1_args(space=ODCExtent.CENTRAL_SUBSET_FOR_TIMES, time=ODCExtent.FIRST)
    check_wcs_error(ows_server.url + "/wcs", params={
                        "request": "GetCoverage",
                        "service": "WCS",
                        "version": "1.0.0",
                        "coverage": test_layer_name,
                        "crs": 'EPSG:4326',
                        "format": 'GeoTIFF',
                        "bbox": extents["bbox"],
                        "time": extents["times"],
                        "exceptions": "spam",
                        "measurements": "red,green,spam"
                    },
                    expected_error_message="Invalid measurement: spam",
                    expected_status_code=400)

def test_wcs1_getcov_badexception(ows_server):
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0", timeout=120)
    contents = list(wcs.contents)
    test_layer_name = contents[0]
    cfg = get_config(refresh=True)
    layer = cfg.product_index[test_layer_name]
    extents = ODCExtent(layer).wcs1_args(space=ODCExtent.CENTRAL_SUBSET_FOR_TIMES, time=ODCExtent.FIRST)
    check_wcs_error(ows_server.url + "/wcs", params={
        "request": "GetCoverage",
        "service": "WCS",
        "version": "1.0.0",
        "coverage": test_layer_name,
        "crs": 'EPSG:4326',
        "format": 'GeoTIFF',
        "bbox": extents["bbox"],
        "time": extents["times"],
        "exceptions": "spam",
        "measurements": "red,green,blue"
    },
                    expected_error_message="Unsupported exception format: spam",
                    expected_status_code=400)

def test_wcs1_getcov_interp(ows_server):
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0", timeout=120)
    contents = list(wcs.contents)
    test_layer_name = contents[0]
    cfg = get_config(refresh=True)
    layer = cfg.product_index[test_layer_name]
    extents = ODCExtent(layer).wcs1_args(space=ODCExtent.CENTRAL_SUBSET_FOR_TIMES, time=ODCExtent.FIRST)
    check_wcs_error(ows_server.url + "/wcs", params={
                        "request": "GetCoverage",
                        "service": "WCS",
                        "version": "1.0.0",
                        "coverage": test_layer_name,
                        "crs": 'EPSG:4326',
                        "format": 'GeoTIFF',
                        "bbox": extents["bbox"],
                        "time": extents["times"],
                        "exceptions": "application/vnd.ogc.se_xml",
                        "measurements": "red,green,blue",
                        "interpolation": "bilinear",
        },
                    expected_error_message="Unsupported interpolation method: bilinear",
                    expected_status_code=400)

def test_wcs1_getcoverage_geotiff(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0", timeout=120)

    # Ensure that we have at least some layers available
    contents = list(wcs.contents)
    test_layer_name = contents[0]
    test_layer = wcs.contents[test_layer_name]

    bbox = test_layer.boundingBoxWGS84


    output = wcs.getCoverage(
        identifier=contents[0],
        format='GeoTIFF',
        bbox=pytest.helpers.disjoint_bbox(bbox),
        crs='EPSG:4326',
        width=400,
        height=300,
        timeSequence=test_layer.timepositions[len(test_layer.timepositions) // 2].strip(),
    )

    assert output
    assert output.info()['Content-Type'] == 'image/geotiff'


def test_wcs1_getcoverage_geotiff_respcrs(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0", timeout=120)

    # Ensure that we have at least some layers available
    contents = list(wcs.contents)
    test_layer_name = contents[0]
    test_layer = wcs.contents[test_layer_name]

    bbox = test_layer.boundingBoxWGS84


    output = wcs.getCoverage(
        identifier=contents[0],
        format='GeoTIFF',
        bbox=pytest.helpers.disjoint_bbox(bbox),
        crs='EPSG:4326',
        response_crs='EPSG:3857',
        width=400,
        height=300,
        timeSequence=test_layer.timepositions[len(test_layer.timepositions) // 2].strip(),
    )

    assert output
    assert output.info()['Content-Type'] == 'image/geotiff'

def test_wcs1_getcoverage_netcdf(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0", timeout=120)

    # Ensure that we have at least some layers available
    contents = list(wcs.contents)
    test_layer_name = contents[0]
    test_layer = wcs.contents[test_layer_name]

    bbox = test_layer.boundingBoxWGS84

    output = wcs.getCoverage(
        identifier=contents[0],
        format='netCDF',
        bbox=pytest.helpers.enclosed_bbox(bbox),
        crs='EPSG:4326',
        width=400,
        height=300,
    )

    assert output
    assert output.info()['Content-Type'] == 'application/x-netcdf'

    output = wcs.getCoverage(
        identifier=contents[0],
        format='netCDF',
        bbox=pytest.helpers.enclosed_bbox(bbox),
        crs='I-CANT-BELIEVE-ITS-NOT-EPSG:4326',
        width=400,
        height=300
    )

    assert output
    assert output.info()['Content-Type'] == 'application/x-netcdf'


def test_extent_utils():
    OWSConfig._instance = None
    cfg = get_config(refresh=True)
    layer = None
    for lyr in cfg.product_index.values():
        if lyr.ready and not lyr.hide:
            layer = lyr
            break
    assert layer
    assert layer.ready and not layer.hide
    assert layer is not None
    ext = ODCExtent(layer)
    extent, first_times = ext.subsets(space=ODCExtent.FULL_LAYER_EXTENT, time=ODCExtent.FIRST)
    assert len(first_times) == 1
    assert extent
    assert extent == ext.full_extent
    ft_extent, last_times = ext.subsets(space=ODCExtent.FULL_EXTENT_FOR_TIMES, time=ODCExtent.LAST)
    assert len(last_times) == 1
    assert ft_extent.area < ext.full_extent.area
    assert first_times[0] < last_times[0]
    extent, times = ext.subsets(space=ODCExtent.CENTRAL_SUBSET_FOR_TIMES, time=ODCExtent.LAST)
    assert len(times) == 1
    assert extent.area < ext.full_extent.area
    assert extent.area < ft_extent.area
    assert ext.full_extent.contains(extent)
    extent, times = ext.subsets(space=ODCExtent.OUTSIDE_OF_FULL_EXTENT, time=ODCExtent.SECOND)
    assert len(times) == 1
    assert not ext.full_extent.intersects(extent)
    extent, times = ext.subsets(space=ODCExtent.IN_FULL_BUT_OUTSIDE_OF_TIMES, time=ODCExtent.LAST)
    assert not ft_extent.intersects(extent)
    assert ext.full_extent.contains(extent)


def test_wcs1_getcoverage_exceptions(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0", timeout=120)
    contents = list(wcs.contents)
    test_layer_name = contents[0]
    test_layer = wcs.contents[test_layer_name]

    bbox = test_layer.boundingBoxWGS84

    try:
        # test where product name is not available
        wcs.getCoverage(
            identifier='nonexistentproduct',
            format='GeoTIFF',
            bbox=pytest.helpers.disjoint_bbox(bbox),
            crs='EPSG:4326',
            width=400,
            height=300
        )
    except ServiceException as e:
        assert 'Invalid coverage:' in str(e)

    try:
        # test where  format is not supported
        wcs.getCoverage(
            identifier=contents[0],
            # format='GeoTIFF',
            bbox=pytest.helpers.disjoint_bbox(bbox),
            crs='EPSG:4326',
            width=400,
            height=300
        )
    except ServiceException as e:
        assert 'Unsupported format:' in str(e)

    try:
        # test where crs is not provided
        wcs.getCoverage(
            identifier=contents[0],
            format='GeoTIFF',
            bbox=pytest.helpers.disjoint_bbox(bbox),
            # crs='EPSG:4326',
            width=400,
            height=300
        )
    except ServiceException as e:
        assert 'No request CRS specified' in str(e)

    try:
        # test where crs is not supported
        wcs.getCoverage(
            identifier=contents[0],
            format='GeoTIFF',
            bbox=pytest.helpers.disjoint_bbox(bbox),
            crs='EPSG:432676',
            width=400,
            height=300
        )
    except ServiceException as e:
        assert 'is not a supported CRS' in str(e)

    try:
        # test where bbox is not correctly provided
        wcs.getCoverage(
            identifier=contents[0],
            format='GeoTIFF',
            # bbox=(10,40,18,45),
            crs='EPSG:4326',
            width=400,
            height=300
        )
    except ServiceException as e:
        assert 'Invalid BBOX parameter' in str(e)


def test_wcs1_describecoverage(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="1.0.0", timeout=120)

    # Ensure that we have at least some layers available
    contents = list(wcs.contents)
    test_layer_name = contents[0]

    resp = wcs.getDescribeCoverage(test_layer_name)

    gc_xds = get_xsd("1.0.0/describeCoverage.xsd")
    assert gc_xds.validate(resp)


def test_wcs20_server(ows_server):
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="2.0.0", timeout=120)

    # Ensure that we have at least some layers available
    contents = list(wcs.contents)
    assert contents

    # Test DescribeCoverage
    desc_cov = wcs.getDescribeCoverage(contents[0])
    assert desc_cov


def test_wcs20_getcoverage_geotiff(ows_server):
    cfg = get_config(refresh=True)
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="2.0.0", timeout=120)

    # Ensure that we have at least some layers available
    contents = list(wcs.contents)
    layer = cfg.product_index[contents[0]]
    assert layer.ready and not layer.hide
    extent = ODCExtent(layer)
    subsets = extent.wcs2_subsets(ODCExtent.CENTRAL_SUBSET_FOR_TIMES, ODCExtent.FIRST, "EPSG:4326")
    output = wcs.getCoverage(
        identifier=[layer.name],
        format='image/geotiff',
        subsets=subsets,
        subsettingcrs="EPSG:4326",
        scalesize="x(400),y(300)"
    )
    assert output
    assert output.info()['Content-Type'] == 'image/geotiff'



def test_wcs20_getcoverage_netcdf(ows_server):
    cfg = get_config(refresh=True)
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="2.0.0", timeout=120)

    # Ensure that we have at least some layers available
    contents = list(wcs.contents)
    layer = cfg.product_index[contents[0]]
    extent = ODCExtent(layer)
    subsets = extent.wcs2_subsets(ODCExtent.CENTRAL_SUBSET_FOR_TIMES, ODCExtent.SECOND, "EPSG:4326")
    output = wcs.getCoverage(
        identifier=[layer.name],
        format='application/x-netcdf',
        subsets=subsets,
        subsettingcrs="EPSG:4326",
        scalesize="x(400),y(300)",
    )

    assert output
    assert output.info()['Content-Type'] == 'application/x-netcdf'


def test_wcs20_getcoverage_crs_alias(ows_server):
    cfg = get_config(refresh=True)
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="2.0.0", timeout=120)

    # Ensure that we have at least some layers available
    contents = list(wcs.contents)
    layer = cfg.product_index[contents[0]]
    extent = ODCExtent(layer)
    subsets = extent.wcs2_subsets(ODCExtent.CENTRAL_SUBSET_FOR_TIMES, ODCExtent.SECOND_LAST, "EPSG:4326")
    output = wcs.getCoverage(
        identifier=[layer.name],
        format='application/x-netcdf',
        subsets=[('x', 144, 144.3), ('y', -42.4, -42), ('time', '2019-11-05')],
        subsettingcrs="I-CANT-BELIEVE-ITS-NOT-EPSG:4326",
        scalesize="x(400),y(300)",
    )

    assert output
    assert output.info()['Content-Type'] == 'application/x-netcdf'


def test_wcs20_getcoverage_multidate_geotiff(ows_server):
    cfg = get_config(refresh=True)
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="2.0.0", timeout=120)

    # Ensure that we have at least some layers available
    contents = list(wcs.contents)
    layer = cfg.product_index[contents[0]]
    extent = ODCExtent(layer)
    subsets = extent.wcs2_subsets(ODCExtent.CENTRAL_SUBSET_FOR_TIMES, ODCExtent.FIRST_TWO, crs="EPSG:4326")
    try:
        resp = wcs.getCoverage(
            identifier=[contents[0]],
            format='image/geotiff',
            subsets=subsets,
            subsettingcrs="EPSG:4326",
            scalesize="x(400),y(300)",
        )
    except ServiceException as e:
        assert 'Format does not support multi-time datasets' in str(e)


def test_wcs20_getcoverage_multidate_netcdf(ows_server):
    cfg = get_config(refresh=True)
    # Use owslib to confirm that we have a somewhat compliant WCS service
    wcs = WebCoverageService(url=ows_server.url+"/wcs", version="2.0.0", timeout=120)

    # Ensure that we have at least some layers available
    contents = list(wcs.contents)
    layer = cfg.product_index[contents[0]]
    extent = ODCExtent(layer)
    subsets = extent.wcs2_subsets(ODCExtent.OFFSET_SUBSET_FOR_TIMES, ODCExtent.FIRST_TWO, crs="EPSG:4326")
    resp = wcs.getCoverage(
        identifier=[contents[0]],
        format='application/x-netcdf',
        subsets=subsets,
        subsettingcrs="EPSG:4326",
        scalesize="x(400),y(300)",
    )


def test_wcs21_server(ows_server):
    # N.B. At time of writing owslib does not support WCS 2.1, so we have to make requests manually.
    r = requests.get(ows_server.url + '/wcs', params={
        "request": "GetCapabilities",
        "version": "2.1.0",
        "service": "WCS"
    })
    assert r.status_code == 200
    cfg = get_config(refresh=True)
    layer = None
    for lyr in cfg.product_index.values():
        if lyr.ready and not lyr.hide:
            layer = lyr
            assert lyr.name in r.text
    # Ensure that we have at least some layers available
    assert layer


def test_wcs21_describecoverage(ows_server):
    cfg = get_config(refresh=True)
    layer = None
    for lyr in cfg.product_index.values():
        if lyr.ready and not lyr.hide:
            layer = lyr
            break
    assert layer
    # N.B. At time of writing owslib does not support WCS 2.1, so we have to make requests manually.
    r = requests.get(ows_server.url + '/wcs', params={
        "request": "DescribeCoverage",
        "coverageid": layer.name,
        "version": "2.1.0",
        "service": "WCS"
    })
    assert r.status_code == 200
    # ETree hangs parsing schema!
#   gc_xds = get_xsd("2.1/gml/wcsDescribeCoverage.xsd")
#   assert gc_xds.validate(r.text)


def test_wcs21_getcoverage(ows_server):
    cfg = get_config(refresh=True)
    layer = None
    for lyr in cfg.product_index.values():
        if lyr.ready and not lyr.hide:
            layer = lyr
            break
    assert layer
    extent = ODCExtent(layer)
    subsets = extent.raw_wcs2_subsets(ODCExtent.OFFSET_SUBSET_FOR_TIMES, ODCExtent.SECOND_LAST, crs="EPSG:4326")

    r = requests.get(ows_server.url + "/wcs", params={
        "request": "GetCoverage",
        "coverageid": layer.name,
        "version": "2.1.0",
        "service": "WCS",
        "format": "image/geotiff",
        "subsettingcrs": "EPSG:4326",
        "scalesize": "x(400),y(400)",
        "subset": subsets
    })
    assert r.status_code == 200


def test_wcs2_getcov_badcov(ows_server):
    check_wcs_error(ows_server.url + "/wcs", params={
        "request": "GetCoverage",
        "service": "WCS",
        "version": "2.1.0",
        "coverageid": "not_a_valid_coverage"
    },
                    expected_error_message="Invalid coverage: not_a_valid_coverage",
                    expected_status_code=400)

def test_wcs2_getcov_unpub_subset_crs(ows_server):
    cfg = get_config(refresh=True)
    layer = None
    for lyr in cfg.product_index.values():
        if lyr.ready and not lyr.hide:
            layer = lyr
            break
    assert layer
    check_wcs_error(ows_server.url + "/wcs", params={
        "request": "GetCoverage",
        "service": "WCS",
        "version": "2.1.0",
        "coverageid": layer.name,
        "subsettingcrs": "EPSG:FAKE",
        "outputcrs": "EPSG:4326"
    },
                    expected_error_message="Invalid subsettingCrs: EPSG:FAKE",
                    expected_status_code=400)


def test_wcs2_getcov_unpub_output_crs(ows_server):
    cfg = get_config(refresh=True)
    layer = None
    for lyr in cfg.product_index.values():
        if lyr.ready and not lyr.hide:
            layer = lyr
            break
    assert layer
    check_wcs_error(ows_server.url + "/wcs", params={
        "request": "GetCoverage",
        "service": "WCS",
        "version": "2.1.0",
        "coverageid": layer.name,
        "subsettingcrs": "EPSG:4326",
        "outputcrs": "EPSG:FAKE"
    },
                    expected_error_message="Invalid outputCrs: EPSG:FAKE",
                    expected_status_code=400)


def test_wcs2_getcov_dup_subset_dims(ows_server):
    cfg = get_config(refresh=True)
    layer = None
    for lyr in cfg.product_index.values():
        if lyr.ready and not lyr.hide:
            layer = lyr
            break
    assert layer
    check_wcs_error(ows_server.url + "/wcs", params={
        "request": "GetCoverage",
        "service": "WCS",
        "version": "2.1.0",
        "coverageid": layer.name,
        "subsettingcrs": "EPSG:4326",
        "outputcrs": "EPSG:4326",
        "subset": (
            "x(2345234,-99999.99999)",
            "x(12315.000,-12312321)",
            "y(2345234,-99999.99999)",
            "y(12315.000,-12312321)",
        )
    },
                    expected_error_message="Duplicate dimensions:",
                    expected_status_code=400)

