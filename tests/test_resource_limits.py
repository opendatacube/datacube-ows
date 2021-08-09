import pytest

from datacube.utils import geometry as geom
import datacube_ows.resource_limits

def test_reequest_scale():
    band = {'dtype': 'float64'}
    rs = datacube_ows.resource_limits.RequestScale(
                                                    geom.CRS("EPSG:3857"), (10.0, 10.0),
                                                    (512, 512), 2,
                                                    request_bands=[band])
    assert pytest.approx(rs.scale_factor * 3 / 200) == rs.standard_scale.scale_factor
