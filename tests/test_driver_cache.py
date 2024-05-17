
def test_index_driver_cache():
    from datacube_ows.index.driver import ows_index_drivers
    assert "postgres" in ows_index_drivers()
    from datacube_ows.index.driver import ows_index_driver_by_name
    assert ows_index_driver_by_name("postgres") is not None
