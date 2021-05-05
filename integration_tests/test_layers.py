from datacube_ows.ows_configuration import get_config


def test_get_layers():
    cfg = get_config()

    export = dict(cfg.export_metadata())
    assert "folder.0.title" not in export
    assert "folder.landsat.title" in export

    # assert layers.platforms
    # for p in layers:
    #     assert p.products
    #     for prd in p.products:
    #         assert prd.styles
    #        assert layers.product_index[prd.name] == prd
    #        assert prd.title
