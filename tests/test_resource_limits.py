import pytest

from datacube.utils import geometry as geom
import datacube_ows.resource_limits

def test_request_scale():
    band = {'dtype': 'float64'}
    rs1 = datacube_ows.resource_limits.RequestScale(geom.CRS("EPSG:3857"), (10.0, 10.0),
                                                    (512, 512), 2,
                                                    request_bands=[band])
    assert pytest.approx(rs1.scale_factor * 3 / 200, 1e-8) == rs1.standard_scale.scale_factor
    assert pytest.approx(rs1.standard_scale / rs1.standard_scale, 1e-8) == 1.0
    assert pytest.approx(rs1 / rs1.standard_scale, 1e-8) == 200 / 3
    assert pytest.approx(rs1.load_factor, 1e-8) == 200 / 3
    assert pytest.approx(rs1.standard_scale.zoom_lvl_offset, 1e-64) == 0.0
    rs2 = datacube_ows.resource_limits.RequestScale(geom.CRS("EPSG:3857"), (25.0, 25.0),
                                                    (256, 256), 4,
                                                    total_band_size=6)
    assert pytest.approx(rs2.zoom_lvl_offset, 1e-8) == 1.0
    rs3 = datacube_ows.resource_limits.RequestScale(geom.CRS("EPSG:3857"), (25.0, 25.0),
                                                   (256, 256), 64,
                                                   total_band_size=6)
    assert pytest.approx(rs3.zoom_lvl_offset, 1e-8) == 3.0