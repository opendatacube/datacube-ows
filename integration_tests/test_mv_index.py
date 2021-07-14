# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import pytest
from datacube.utils.geometry import box

from datacube_ows.cube_pool import cube
from datacube_ows.mv_index import MVSelectOpts, mv_search
from datacube_ows.ogc_utils import local_solar_date_range
from datacube_ows.ows_configuration import get_config


def test_full_layer():
    cfg = get_config()
    lyr = list(cfg.product_index.values())[0]
    with cube() as dc:
        sel = mv_search(dc.index, MVSelectOpts.COUNT, products=lyr.products)
        assert sel > 0


def test_select_all():
    cfg = get_config()
    lyr = list(cfg.product_index.values())[0]
    with cube() as dc:
        rows = mv_search(dc.index, MVSelectOpts.ALL, products=lyr.products)
        for row in rows:
            assert len(row) > 1


def test_no_products():
    with cube() as dc:
        with pytest.raises(Exception) as e:
            sel = mv_search(dc.index, MVSelectOpts.COUNT)
        assert "Must filter by product/layer" in str(e.value)


def test_bad_set_opt():
    cfg = get_config()
    lyr = list(cfg.product_index.values())[0]
    with cube() as dc:
        with pytest.raises(AssertionError) as e:
            sel = mv_search(dc.index, MVSelectOpts.INVALID, products=lyr.products)


class MockGeobox:
    def __init__(self, geom):
        if geom.crs != "EPSG:4326":
            geom = geom.to_crs("EPSG:4326")
        self.geographic_extent = geom


def test_time_search():
    cfg = get_config()
    lyr = list(cfg.product_index.values())[0]
    time = lyr.ranges["times"][-1]
    geom = box(
        lyr.bboxes["EPSG:4326"]["left"],
        lyr.bboxes["EPSG:4326"]["bottom"],
        lyr.bboxes["EPSG:4326"]["right"],
        lyr.bboxes["EPSG:4326"]["top"],
        "EPSG:4326",
    )

    time_rng = local_solar_date_range(MockGeobox(geom), time)
    with cube() as dc:
        sel = mv_search(
            dc.index, MVSelectOpts.COUNT, times=[time_rng], products=lyr.products
        )
        assert sel > 0


def test_count():
    cfg = get_config()
    lyr = list(cfg.product_index.values())[0]
    with cube() as dc:
        count = mv_search(dc.index, MVSelectOpts.COUNT, products=lyr.products)
        ids = mv_search(dc.index, MVSelectOpts.IDS, products=lyr.products)
        assert len(ids) == count


def test_datasets():
    cfg = get_config()
    lyr = list(cfg.product_index.values())[0]
    with cube() as dc:
        dss = mv_search(dc.index, MVSelectOpts.DATASETS, products=lyr.products)
        ids = mv_search(dc.index, MVSelectOpts.IDS, products=lyr.products)
        assert len(ids) == len(dss)
        for ds in dss:
            assert str(ds.id) in ids


def test_extent_and_spatial():
    cfg = get_config()
    lyr = list(cfg.product_index.values())[0]
    layer_ext_bbx = (
        lyr.bboxes["EPSG:4326"]["left"],
        lyr.bboxes["EPSG:4326"]["bottom"],
        lyr.bboxes["EPSG:4326"]["right"],
        lyr.bboxes["EPSG:4326"]["top"],
    )
    small_bbox = pytest.helpers.enclosed_bbox(layer_ext_bbx)
    layer_ext_geom = box(
        layer_ext_bbx[0],
        layer_ext_bbx[1],
        layer_ext_bbx[2],
        layer_ext_bbx[3],
        "EPSG:4326",
    )
    small_geom = box(
        small_bbox[0], small_bbox[1], small_bbox[2], small_bbox[3], "EPSG:4326"
    )
    with cube() as dc:
        all_ext = mv_search(
            dc.index, MVSelectOpts.EXTENT, geom=layer_ext_geom, products=lyr.products
        )
        small_ext = mv_search(
            dc.index, MVSelectOpts.EXTENT, geom=small_geom, products=lyr.products
        )
        assert layer_ext_geom.contains(all_ext)
        assert small_geom.contains(small_ext)
        assert all_ext.contains(small_ext)
        assert small_ext.area < all_ext.area

        all_count = mv_search(
            dc.index, MVSelectOpts.COUNT, geom=layer_ext_geom, products=lyr.products
        )
        small_count = mv_search(
            dc.index, MVSelectOpts.COUNT, geom=small_geom, products=lyr.products
        )
        assert small_count <= all_count
