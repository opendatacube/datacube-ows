# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import os

from datacube_ows.ows_configuration import OWSConfig, get_config, read_config

src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_metadata_export():
    cfg = get_config(refresh=True)

    export = cfg.export_metadata()
    assert "folder.0.title" not in export
    assert "folder.sentinel2.title" in export

    # assert layers.platforms
    # for p in layers:
    #     assert p.products
    #     for prd in p.products:
    #         assert prd.styles
    #        assert layers.product_index[prd.name] == prd
    #        assert prd.title


def test_missing_metadata_file(monkeypatch):
    cached_cfg = OWSConfig._instance
    cached_reg = OWSConfig._metadata_registry
    cached_inh_reg = OWSConfig._inheritance_registry
    cached_catalog = OWSConfig._msg_src

    monkeypatch.chdir(src_dir)
    try:
        OWSConfig._instance = None
        OWSConfig._metadata_registry = {}
        OWSConfig._inheritance_registry = {}
        OWSConfig._msg_src = None
        raw_cfg = read_config()
        raw_cfg["global"]["message_file"] = "integration_tests/cfg/non-existent.po"
        raw_cfg["global"]["translations_directory"] = None
        raw_cfg["global"]["languages"] = ["en"]
        cfg = OWSConfig(refresh=True, cfg=raw_cfg)
        cfg.make_ready()

        assert "Over-ridden" not in cfg.title
        assert "aardvark" not in cfg.title
    finally:
        OWSConfig._instance = cached_cfg
        OWSConfig._metadata_registry = cached_reg
        OWSConfig._inheritance_registry = cached_inh_reg
        OWSConfig._msg_src = cached_catalog


def test_metadata_file_ignore(monkeypatch):
    cached_cfg = OWSConfig._instance
    cached_reg = OWSConfig._metadata_registry
    cached_inh_reg = OWSConfig._inheritance_registry
    cached_catalog = OWSConfig._msg_src
    monkeypatch.chdir(src_dir)
    try:
        OWSConfig._instance = None
        OWSConfig._metadata_registry = {}
        OWSConfig._inheritance_registry = {}
        OWSConfig._msg_src = None
        raw_cfg = read_config()
        raw_cfg["global"]["message_file"] = "integration_tests/cfg/message.po"
        cfg = OWSConfig(refresh=True, cfg=raw_cfg, ignore_msgfile=True)
        cfg.make_ready()

        assert "Over-ridden" not in cfg.title
        assert "aardvark" not in cfg.title
    finally:
        OWSConfig._instance = cached_cfg
        OWSConfig._metadata_registry = cached_reg
        OWSConfig._inheritance_registry = cached_inh_reg
        OWSConfig._msg_src = cached_catalog


def test_metadata_read(monkeypatch, product_name):
    cached_cfg = OWSConfig._instance
    monkeypatch.chdir(src_dir)
    try:
        OWSConfig._instance = None
        raw_cfg = read_config()
        raw_cfg["global"]["message_file"] = "integration_tests/cfg/message.po"
        cfg = OWSConfig(refresh=True, cfg=raw_cfg)
        cfg.make_ready()

        assert "Over-ridden" in cfg.title
        assert "aardvark" in cfg.title

        folder = cfg.folder_index["folder.sentinel2"]
        assert "Over-ridden" not in folder.title
        assert "Over-ridden" in folder.abstract
        assert "bunny-rabbit" in folder.abstract

        lyr = cfg.layer_index[product_name]
        assert "Over-ridden" in lyr.title
        assert "chook" in lyr.title

        styl = lyr.style_index["simple_rgb"]
        assert "Over-ridden" in styl.title
        assert "donkey" in styl.title

        styl = lyr.style_index["blue"]
        assert "Over-ridden" not in styl.title
    finally:
        OWSConfig._instance = cached_cfg
