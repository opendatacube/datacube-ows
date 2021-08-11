import pytest
from datacube.utils import geometry as geom

import datacube_ows.resource_limits
from datacube_ows.ogc_utils import create_geobox


def test_request_scale():
    band = {'dtype': 'float64'}
    stdtile = create_geobox(minx=-20037508.342789, maxx=20037508.342789,
                            miny=-20037508.342789, maxy=20037508.342789,
                            crs=geom.CRS("EPSG:3857"),
                            width=256, height=256)
    bigtile = create_geobox(minx=-20037508.342789, maxx=20037508.342789,
                           miny=-20037508.342789, maxy=20037508.342789,
                           crs=geom.CRS("EPSG:3857"),
                           width=512, height=512)
    rs1 = datacube_ows.resource_limits.RequestScale(geom.CRS("EPSG:3857"), (10.0, 10.0),
                                                    bigtile, 2,
                                                    request_bands=[band])
    assert pytest.approx(rs1.standard_scale / rs1.standard_scale, 1e-8) == 1.0
    assert pytest.approx(rs1 / rs1.standard_scale, 1e-8) == 200 / 3
    assert pytest.approx(rs1.load_factor, 1e-8) == 200 / 3
    assert pytest.approx(rs1.standard_scale.zoom_lvl_offset, 1e-64) == 0.0
    rs2 = datacube_ows.resource_limits.RequestScale(geom.CRS("EPSG:3857"), (25.0, 25.0),
                                                    stdtile, 4,
                                                    total_band_size=6)
    assert pytest.approx(rs2.zoom_lvl_offset, 1e-8) == 1.0
    rs3 = datacube_ows.resource_limits.RequestScale(geom.CRS("EPSG:3857"), (25.0, 25.0),
                                                   stdtile, 64,
                                                   total_band_size=6)
    assert pytest.approx(rs3.zoom_lvl_offset, 1e-8) == 3.0
    assert pytest.approx(rs3.base_zoom_level, 0.1) == 0.0
    assert pytest.approx(rs3.load_adjusted_zoom_level, 0.1) == -3.0
