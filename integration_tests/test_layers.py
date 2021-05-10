import os

from datacube_ows.ows_configuration import get_config, read_config, OWSConfig

src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_metadata_export():
    cfg = get_config(refresh=True)

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


def test_metadata_read(monkeypatch):
    cached_cfg = OWSConfig._instance
    monkeypatch.chdir(src_dir)
    try:
        OWSConfig._instance = None
        raw_cfg = read_config()
        raw_cfg["global"]["message_file"] = "integration_tests/cfg/message.po"
        cfg = OWSConfig(refresh=True, cfg=raw_cfg)

        assert "Over-ridden" in cfg.title
        assert "aardvark" in cfg.title

        folder = cfg.folder_index["landsat"]
        assert "Over-ridden" in folder.title
        assert "bunny-rabbit" in folder.title

        lyr = cfg.product_index["ls8_usgs-level1_scene_layer"]
        assert "Over-ridden" in lyr.title
        assert "chook" in lyr.title

        styl = lyr.style_index["simple_rgb"]
        assert "Over-ridden" in styl.title
        assert "donkey" in styl.title

        styl = lyr.style_index["blue"]
        assert "Over-ridden" not in styl.title
    finally:
        OWSConfig._instance = cached_cfg

