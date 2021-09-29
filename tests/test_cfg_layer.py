# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import datetime
import math
from unittest.mock import MagicMock, patch

import pytest

from datacube_ows.ogc_utils import ConfigException
from datacube_ows.ows_configuration import OWSFolder, OWSLayer, parse_ows_layer
from datacube_ows.resource_limits import ResourceLimited


def test_missing_title(minimal_global_cfg):
    with pytest.raises(ConfigException) as excinfo:
        lyr = OWSFolder({
            "abstract": "The Abstract"
        },
            global_cfg=minimal_global_cfg)
    assert "Entity folder.0 has no title" in str(excinfo.value)


def test_inherit_no_abstract(minimal_global_cfg):
    lyr = OWSFolder({
            "title": "The Title",
            "layers": [],
        },
        global_cfg=minimal_global_cfg)
    assert lyr.abstract == "Global Abstract"
    assert lyr.is_inherited("abstract")

def test_inherit_parent(minimal_global_cfg, minimal_parent):
    lyr = OWSLayer({
            "title": "The Title",
    },
        object_label="foo",
        parent_layer=minimal_parent,
        global_cfg=minimal_global_cfg)
    assert lyr.abstract == "Parent Abstract"
    assert lyr.attribution.title == "Parent Attribution"
    assert "global" in lyr.keywords
    assert "parent" in lyr.keywords


def test_override_parent(minimal_global_cfg, minimal_parent):
    lyr = OWSLayer({
        "title": "The Title",
        "attribution": {},
        "abstract": "The Abstract",
        "keywords": ["merged"]
    },
        object_label="foo",
        parent_layer=minimal_parent,
        global_cfg=minimal_global_cfg)
    assert lyr.abstract == "The Abstract"
    assert lyr.attribution is None
    assert "global" in lyr.keywords
    assert "parent" in lyr.keywords
    assert "merged" in lyr.keywords
    assert lyr.local_keywords == set(["merged"])


def test_minimal_folder(minimal_global_cfg):
    lyr = OWSFolder({
        "title": "The Title",
        "abstract": "The Abstract",
        "layers": []
    }, global_cfg=minimal_global_cfg)
    assert lyr.child_layers == []
    assert lyr.layer_count() == 0
    assert lyr.unready_layer_count() == 0


def test_folder_nolayers(minimal_global_cfg):
    with pytest.raises(ConfigException) as excinfo:
        lyr = OWSFolder({
            "title": "The Title",
            "abstract": "The Abstract",
        }, global_cfg=minimal_global_cfg)
    assert "No layers section" in str(excinfo.value)
    assert "The Title" in str(excinfo.value)


def test_folder_counts(minimal_global_cfg):
    lyr = OWSFolder({
        "title": "The Title",
        "abstract": "The Abstract",
        "layers": []
    }, global_cfg=minimal_global_cfg)
    l1 = MagicMock()
    l2 = MagicMock()
    l3 = MagicMock()
    l4 = MagicMock()
    l1.layer_count.return_value = 1
    l2.layer_count.return_value = 2
    l3.layer_count.return_value = 1
    l4.layer_count.return_value = 3
    lyr.child_layers = [l1, l2]
    lyr.unready_layers = [l3, l4]
    assert lyr.layer_count() == 3
    assert lyr.unready_layer_count() == 4


def test_catch_invalid_folder_layers(minimal_global_cfg):
    lyr = OWSFolder({
        "title": "The Title",
        "abstract": "The Abstract",
        "layers": [
            {"invalid": "config"}
        ]
    }, global_cfg=minimal_global_cfg)
    assert len(lyr.unready_layers) == 0


def test_catch_folder_as_list(minimal_global_cfg):
    lyr = OWSFolder({
        "title": "The Title",
        "abstract": "The Abstract",
        "layers": [
            [{"title": "wrong", "abstract": "wrong", "layers": []}]
        ]
    }, global_cfg=minimal_global_cfg)
    assert len(lyr.unready_layers) == 0


def test_duplicate_folder_label(minimal_global_cfg):
    with pytest.raises(ConfigException) as e:
        lyr = OWSFolder({
            "title": "The Title",
            "abstract": "The Abstract",
            "label": "existing_folder",
            "layers": [
                {"invalid": "config"}
            ]
        }, global_cfg=minimal_global_cfg)
    assert "Duplicate folder label" in str(e.value)
    assert "existing_folder" in str(e.value)


def test_make_ready_empty(minimal_global_cfg, minimal_dc):
    lyr = OWSFolder({
        "title": "The Title",
        "abstract": "The Abstract",
        "layers": [
        ]
    }, global_cfg=minimal_global_cfg)
    lyr.make_ready(minimal_dc)
    assert len(lyr.unready_layers) == 0
    assert lyr.ready


def test_make_ready_catch_errors(minimal_global_cfg, minimal_dc):
    lyr = OWSFolder({
        "title": "The Title",
        "abstract": "The Abstract",
        "layers": [
        ]
    }, global_cfg=minimal_global_cfg)
    testchild = MagicMock()
    testchild.make_ready.side_effect = ConfigException("KerPow!")
    lyr.unready_layers.append(testchild)
    lyr.make_ready(minimal_dc)
    assert len(lyr.unready_layers) == 1
    assert len(lyr.child_layers) == 0
    assert lyr.ready


def test_minimal_named_layer(minimal_layer_cfg, minimal_global_cfg, minimal_dc, mock_range):
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    assert lyr.name == "a_layer"
    assert not lyr.ready
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        lyr.make_ready(minimal_dc)
    assert lyr.ready
    assert not lyr.hide
    assert lyr.default_time == mock_range["times"][-1]
    assert "a_layer" in str(lyr)
    assert len(lyr.low_res_products) == 0


def test_lowres_named_layer(minimal_layer_cfg, minimal_global_cfg, minimal_dc):
    minimal_layer_cfg["low_res_product_name"] = "smol_foo"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    lyr.make_ready(minimal_dc)
    assert len(lyr.low_res_products) == 1


def test_double_underscore_product_name(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["product_name"] = "no__double__underscores"
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "double underscore" in str(excinfo.value)


def test_no_product_name(minimal_layer_cfg, minimal_global_cfg):
    del minimal_layer_cfg["product_name"]
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "product names" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_bad_product_name(minimal_layer_cfg, minimal_global_cfg, minimal_dc):
    minimal_layer_cfg["product_name"] = "foolookupfail"
    minimal_dc.index.products.get_by_name.return_value = None
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    with pytest.raises(ConfigException) as excinfo:
        lyr.make_ready(dc=minimal_dc)
    assert "Could not find product" in str(excinfo.value)
    assert "foolookupfail" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_bad_lowres_product_name(minimal_layer_cfg, minimal_global_cfg, minimal_dc):
    minimal_layer_cfg["low_res_product_name"] = "smolfoolookupfail"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    with pytest.raises(ConfigException) as excinfo:
        lyr.make_ready(dc=minimal_dc)
    assert "Could not find product" in str(excinfo.value)
    assert "smolfoolookupfail" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_plural_in_nonmultiproduct(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["low_res_product_names"] = "smolfoolookupfail"
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "a_layer" in str(excinfo.value)
    assert "'low_res_product_names' entry in non-multi-product layer" in str(excinfo.value)
    assert "use 'low_res_product_name' only" in str(excinfo.value)
    del minimal_layer_cfg["low_res_product_names"]
    minimal_layer_cfg["product_names"] = ["foo", "bar"]
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "a_layer" in str(excinfo.value)
    assert "'product_names' entry in non-multi-product layer" in str(excinfo.value)
    assert "use 'product_name' only" in str(excinfo.value)


def test_flag_plural_in_nonmultiproduct(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["flags"] = {
        "band": "foo",
        "products": ["prod1", "prod2"],
    }
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "a_layer" in str(excinfo.value)
    assert "'products' entry in flags section of non-multi-product layer" in str(excinfo.value)
    assert "use 'product' only" in str(excinfo.value)
    del minimal_layer_cfg["flags"]["products"]
    minimal_layer_cfg["flags"]["low_res_products"] = ["smolfoo", "smolbar"]
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "'low_res_products' entry in flags section of non-multi-product layer" in str(excinfo.value)
    assert "use 'low_res_product' only" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_singular_in_multiproduct(minimal_multiprod_cfg, minimal_global_cfg):
    minimal_multiprod_cfg["low_res_product_name"] = "smolfoolookupfail"
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_multiprod_cfg,
                              global_cfg=minimal_global_cfg)
    assert "'low_res_product_name' entry in multi-product layer" in str(excinfo.value)
    assert "use 'low_res_product_names' only" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)
    del minimal_multiprod_cfg["low_res_product_name"]
    minimal_multiprod_cfg["product_name"] = "foo"
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_multiprod_cfg,
                              global_cfg=minimal_global_cfg)
    assert "'product_name' entry in multi-product layer" in str(excinfo.value)
    assert "use 'product_names' only" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_flag_singular_in_multiproduct(minimal_multiprod_cfg, minimal_global_cfg):
    minimal_multiprod_cfg["flags"] = {
        "band": "foo",
        "product": "goo",
    }
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_multiprod_cfg,
                          global_cfg=minimal_global_cfg)
    assert "'product' entry in flags section of multi-product layer" in str(excinfo.value)
    assert "use 'products' only" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)
    del minimal_multiprod_cfg["flags"]["product"]
    minimal_multiprod_cfg["flags"]["low_res_product"] = "smolfoo"
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_multiprod_cfg,
                              global_cfg=minimal_global_cfg)
    assert "'low_res_product' entry in flags section of multi-product layer" in str(excinfo.value)
    assert "use 'low_res_products' only" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_noprod_multiproduct(minimal_multiprod_cfg, minimal_global_cfg, minimal_dc):
    minimal_multiprod_cfg["product_names"] = []
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_multiprod_cfg,
                          global_cfg=minimal_global_cfg)

    assert "a_layer" in str(excinfo.value)
    assert "No products declared" in str(excinfo.value)


def test_minimal_multiproduct(minimal_multiprod_cfg, minimal_global_cfg, minimal_dc, mock_range):
    lyr = parse_ows_layer(minimal_multiprod_cfg,
                          global_cfg=minimal_global_cfg)
    assert lyr.name == "a_layer"
    assert not lyr.ready
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        lyr.make_ready(minimal_dc)
    assert lyr.ready
    assert not lyr.hide
    assert "a_layer" in str(lyr)


def test_multi_product_lowres(minimal_multiprod_cfg, minimal_global_cfg, minimal_dc):
    minimal_multiprod_cfg["low_res_product_names"] = ["smol_foo", "smol_bar"]
    lyr = parse_ows_layer(minimal_multiprod_cfg,
                          global_cfg=minimal_global_cfg)
    lyr.make_ready(minimal_dc)
    assert len(lyr.products) == 2
    assert len(lyr.low_res_products) == 2


def test_multi_product_pq(minimal_multiprod_cfg, minimal_global_cfg, minimal_dc):
    minimal_multiprod_cfg["flags"] = [
        {
            "products": ["flag_foo", "flag_bar"],
            "band": "band4",
        }
    ]
    lyr = parse_ows_layer(minimal_multiprod_cfg,
                          global_cfg=minimal_global_cfg)
    lyr.make_ready(minimal_dc)
    assert len(lyr.products) == 2
    assert len(lyr.flag_bands["band4"].pq_products) == 2


def test_multi_product_lrpq(minimal_multiprod_cfg, minimal_global_cfg, minimal_dc):
    minimal_multiprod_cfg["flags"] = [
        {
            "products": ["flag_foo", "flag_bar"],
            "low_res_products": ["smol_flag_foo", "smol_flag_bar"],
            "band": "band4",
        }
    ]
    lyr = parse_ows_layer(minimal_multiprod_cfg,
                              global_cfg=minimal_global_cfg)
    lyr.make_ready(minimal_dc)
    assert len(lyr.products) == 2
    assert len(lyr.flag_bands["band4"].pq_products) == 2
    assert len(lyr.flag_bands["band4"].pq_low_res_products) == 2


def test_multi_product_name_mismatch(minimal_multiprod_cfg, minimal_global_cfg):
    minimal_multiprod_cfg["low_res_product_names"] = ["smol_foo"]
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_multiprod_cfg,
                              global_cfg=minimal_global_cfg)
    assert "low_res_product_names" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_resource_limit_zoomfill(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["resource_limits"] = {
        "wms": {"zoomed_out_fill_colour": [128, 128, 128]}
    }
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    assert len(lyr.resource_limits.zoom_fill) == 4
    assert lyr.resource_limits.zoom_fill[3] == 255
    minimal_layer_cfg["resource_limits"]["wms"]["zoomed_out_fill_colour"] = [13, 254]
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "zoomed_out_fill_colour must have 3 or 4 elements" in str(excinfo.value)


def test_resource_limit_checks(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["resource_limits"] = {
        "wms": {"min_zoom_factor": 300.0, "max_datasets": 8},
        "wcs": {"max_datasets": 8, "max_image_size": 100 * 100 * 32},
    }
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    mock_req_scale = MagicMock()
    mock_req_scale.load_adjusted_zoom_level = 4.8
    with pytest.raises(ResourceLimited) as e:
        lyr.resource_limits.check_wms(n_datasets=9, zoom_factor=400.0, request_scale=mock_req_scale)
    assert "too much data" not in str(e.value)
    assert "too many datasets" in str(e.value)
    assert "zoomed out too far" not in str(e.value)
    assert "too much projected resource requirements" not in str(e.value)
    with pytest.raises(ResourceLimited) as e:
        lyr.resource_limits.check_wcs(n_datasets=9, width=640, height=480, pixel_size=64)
    assert "too much data" in str(e.value)
    assert "too many datasets" in str(e.value)
    assert "zoomed out too far" not in str(e.value)
    assert "too much projected resource requirements" not in str(e.value)
    assert e.value.wcs_hard
    minimal_layer_cfg["resource_limits"]["wms"]["min_zoom_level"] = 5
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    with pytest.raises(ResourceLimited) as e:
        lyr.resource_limits.check_wms(n_datasets=9, zoom_factor=100.0, request_scale=mock_req_scale)
    assert "too many datasets" in str(e.value)
    assert "zoomed out too far" in str(e.value)
    assert "too much projected resource requirements" in str(e.value)



def test_manual_merge(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["image_processing"]["manual_merge"] = True
    minimal_layer_cfg["image_processing"]["apply_solar_corrections"] = False
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    assert not lyr.ready
    minimal_layer_cfg["image_processing"]["manual_merge"] = False
    minimal_layer_cfg["image_processing"]["apply_solar_corrections"] = True
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "Solar correction requires manual_merge" in str(excinfo.value)


def test_bad_timeres(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["time_resolution"] = "prime_ministers"
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "Invalid time resolution" in str(excinfo.value)
    assert "prime_ministers" in str(excinfo.value)


def test_flag_no_band(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["flags"] = {
        "external": {
            "product": "foo",
        }
    }

    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "required" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)
    assert "band" in str(excinfo.value)


def test_flag_bad_prod(minimal_layer_cfg, minimal_global_cfg, minimal_dc):
    minimal_layer_cfg["flags"] = [
        {
            "product": "foolookupfail",
            "band": "band1"
        }
    ]
    lyr = parse_ows_layer(minimal_layer_cfg, global_cfg=minimal_global_cfg)
    with pytest.raises(ConfigException) as excinfo:
        lyr.make_ready(dc=minimal_dc)
    assert "foolookupfail" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_flag_bad_lrprod(minimal_layer_cfg, minimal_global_cfg, minimal_dc):
    minimal_layer_cfg["flags"] = [
        {
            "product": "foo",
            "low_res_product": "foolookupfail",
            "band": "band1"
        }
    ]
    lyr = parse_ows_layer(minimal_layer_cfg, global_cfg=minimal_global_cfg)
    with pytest.raises(ConfigException) as excinfo:
        lyr.make_ready(dc=minimal_dc)
    assert "foolookupfail" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_flag_info_mask(minimal_layer_cfg, minimal_global_cfg, minimal_dc):
    minimal_layer_cfg["flags"] = [
        {
            "product": "foo",
            "band": "band4",
            "ignore_info_flags": ["moo", "blat", "zap"]
        }
    ]
    lyr = parse_ows_layer(minimal_layer_cfg, global_cfg=minimal_global_cfg)
    lyr.make_ready(dc=minimal_dc)
    assert not 1 & lyr.flag_bands["band4"].info_mask
    assert 2 & lyr.flag_bands["band4"].info_mask
    assert not 4 & lyr.flag_bands["band4"].info_mask
    assert 8 & lyr.flag_bands["band4"].info_mask
    assert not 16 & lyr.flag_bands["band4"].info_mask
    assert 32 & lyr.flag_bands["band4"].info_mask


def test_img_proc_no_extent_func(minimal_layer_cfg, minimal_global_cfg):
    del minimal_layer_cfg["image_processing"]["extent_mask_func"]
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "required" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)
    assert "extent_mask_func" in str(excinfo.value)


def test_id_badauth(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["identifiers"] = {
        "auth0": "5318008",
        "authn": "mnnnmnnh"
    }
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "non-declared authority" in str(excinfo.value)
    assert "authn" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_no_styles(minimal_layer_cfg, minimal_global_cfg):
    del minimal_layer_cfg["styling"]["styles"]
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "Missing required" in str(excinfo.value)
    assert "styles" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_bad_default_style(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["styling"]["default_style"] = "nonexistent"
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "not in the 'styles'" in str(excinfo.value)
    assert "nonexistent" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)


def test_no_default_style(minimal_layer_cfg, minimal_global_cfg):
    del minimal_layer_cfg["styling"]["default_style"]
    lyr = parse_ows_layer(minimal_layer_cfg,
                      global_cfg=minimal_global_cfg)
    assert lyr.default_style.name == 'band1'


def test_invalid_native_format(minimal_layer_cfg, minimal_global_cfg):
    minimal_global_cfg.wcs = True
    minimal_layer_cfg["wcs"] = {
        "native_format": "geosplunge"
    }
    with pytest.raises(ConfigException) as excinfo:
        lyr = parse_ows_layer(minimal_layer_cfg,
                              global_cfg=minimal_global_cfg)
    assert "a_layer" in str(excinfo.value)
    assert "geosplunge" in str(excinfo.value)


def test_time_range_irreg(minimal_layer_cfg, minimal_global_cfg):
    lyr = parse_ows_layer(minimal_layer_cfg, global_cfg=minimal_global_cfg)
    ranges = {
        "times": [
            datetime.date(2021, 1, 5),
            datetime.date(2021, 1, 6),
            datetime.date(2021, 1, 7),
            datetime.date(2021, 1, 8),
        ]
    }
    start, end = lyr.time_range(ranges)
    assert start == datetime.date(2021, 1, 5)
    assert end == datetime.date(2021, 1, 8)


def test_time_range_reg_default(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["time_axis"] = {
        "time_interval": 1
    }
    lyr = parse_ows_layer(minimal_layer_cfg, global_cfg=minimal_global_cfg)
    ranges = {
        "times": [
            datetime.date(2021, 1, 5),
            datetime.date(2021, 1, 6),
            datetime.date(2021, 1, 7),
            datetime.date(2021, 1, 8),
        ]
    }
    start, end = lyr.time_range(ranges)
    assert start == datetime.date(2021, 1, 5)
    assert end == datetime.date(2021, 1, 8)


def test_time_range_reg_custom(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["time_axis"] = {
        "time_interval": 1,
        "start_date": "2021-01-01",
        "end_date": "2021-01-10",
    }
    lyr = parse_ows_layer(minimal_layer_cfg, global_cfg=minimal_global_cfg)
    lyr._ranges = {
        "times": [
            datetime.date(2021, 1, 5),
            datetime.date(2021, 1, 6),
            datetime.date(2021, 1, 7),
            datetime.date(2021, 1, 8),
        ]
    }
    start, end = lyr.time_range()
    assert start == datetime.date(2021, 1, 1)
    assert end == datetime.date(2021, 1, 10)


def test_time_axis_representation_irreg(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["time_axis"] = {
        "time_interval": 1,
        "start_date": "2021-01-01",
        "end_date": "2021-01-10",
    }
    lyr = parse_ows_layer(minimal_layer_cfg, global_cfg=minimal_global_cfg)
    lyr._ranges = {
        "times": [
            datetime.date(2021, 1, 7),
            datetime.date(2021, 1, 8),
        ]
    }
    assert lyr.time_axis_representation() == "2021-01-01/2021-01-10/P1D"


def test_time_axis_representation_reg(minimal_layer_cfg, minimal_global_cfg):
    lyr = parse_ows_layer(minimal_layer_cfg, global_cfg=minimal_global_cfg)
    assert lyr.time_axis_representation() == ""


def test_time_axis_errors(minimal_layer_cfg, minimal_global_cfg):
    minimal_layer_cfg["time_axis"] = {"start_date": "2010-11-22"}
    with pytest.raises(ConfigException) as e:
        lyr = parse_ows_layer(minimal_layer_cfg, global_cfg=minimal_global_cfg)
    assert "No time_interval supplied in time_axis" in str(e.value)
    minimal_layer_cfg["time_axis"] = {"time_interval": 0.6}
    with pytest.raises(ConfigException) as e:
        lyr = parse_ows_layer(minimal_layer_cfg, global_cfg=minimal_global_cfg)
    assert "time_interval must be an integer" in str(e.value)
    minimal_layer_cfg["time_axis"] = {"time_interval": 0}
    with pytest.raises(ConfigException) as e:
        lyr = parse_ows_layer(minimal_layer_cfg, global_cfg=minimal_global_cfg)
    assert "time_interval must be greater than zero" in str(e.value)
    minimal_layer_cfg["time_axis"] = {
        "time_interval": 7,
        "start_date": "exactly one year before Thursday week",
        "end_date": "2010-11-22",
    }
    with pytest.raises(ConfigException) as e:
        lyr = parse_ows_layer(minimal_layer_cfg, global_cfg=minimal_global_cfg)
    assert "time_axis start_date is not a valid ISO format date string" in str(e.value)
    minimal_layer_cfg["time_axis"] = {
        "time_interval": 7,
        "start_date": "2010-11-22",
        "end_date": "seven fortnights before the last full moon",
    }
    with pytest.raises(ConfigException) as e:
        lyr = parse_ows_layer(minimal_layer_cfg, global_cfg=minimal_global_cfg)
    assert "time_axis end_date is not a valid ISO format date string" in str(e.value)
    minimal_layer_cfg["time_axis"] = {
        "time_interval": 7,
        "start_date": "2010-11-22",
        "end_date": "1999-12-31",
    }
    with pytest.raises(ConfigException) as e:
        lyr = parse_ows_layer(minimal_layer_cfg, global_cfg=minimal_global_cfg)
    assert "time_axis end_date must be greater than or equal to the start_date if both are provided" in str(e.value)


def test_earliest_default_time(minimal_layer_cfg, minimal_global_cfg, minimal_dc, mock_range):
    minimal_layer_cfg["default_time"] = "earliest"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    assert lyr.name == "a_layer"
    assert not lyr.ready
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        lyr.make_ready(minimal_dc)
    assert lyr.ready
    assert not lyr.hide
    assert lyr.default_time == mock_range["times"][0]
    assert "a_layer" in str(lyr)
    assert len(lyr.low_res_products) == 0

def test_latest_default_time(minimal_layer_cfg, minimal_global_cfg, minimal_dc, mock_range):
    minimal_layer_cfg["default_time"] = "latest"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    assert lyr.name == "a_layer"
    assert not lyr.ready
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        lyr.make_ready(minimal_dc)
    assert lyr.ready
    assert not lyr.hide
    assert lyr.default_time == mock_range["times"][-1]
    assert "a_layer" in str(lyr)
    assert len(lyr.low_res_products) == 0

def test_valid_default_time(minimal_layer_cfg, minimal_global_cfg, minimal_dc, mock_range):
    minimal_layer_cfg["default_time"] = "2010-01-02"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    assert lyr.name == "a_layer"
    assert not lyr.ready
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        lyr.make_ready(minimal_dc)
    assert lyr.ready
    assert not lyr.hide
    assert lyr.default_time == datetime.date(2010, 1, 2)
    assert "a_layer" in str(lyr)
    assert len(lyr.low_res_products) == 0

def test_missing_default_time(minimal_layer_cfg, minimal_global_cfg, minimal_dc, mock_range):
    minimal_layer_cfg["default_time"] = "2020-01-22"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    assert lyr.name == "a_layer"
    assert not lyr.ready
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        lyr.make_ready(minimal_dc)
    assert lyr.ready
    assert not lyr.hide
    assert lyr.default_time == mock_range["times"][-1]
    assert "a_layer" in str(lyr)
    assert len(lyr.low_res_products) == 0

def test_invalid_default_time(minimal_layer_cfg, minimal_global_cfg, minimal_dc, mock_range):
    minimal_layer_cfg["default_time"] = "Not-a-date"
    with pytest.raises(ConfigException) as e:
        lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    assert "a_layer" in str(e.value)
    assert "Not-a-date" in str(e.value)
    assert "Invalid default_time value" in str(e.value)


def test_native_crs_mismatch(minimal_global_cfg, minimal_layer_cfg, minimal_dc):
    minimal_layer_cfg["native_crs"] = "EPSG:1234"
    minimal_layer_cfg["product_name"] = "foo_nativecrs"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    lyr.extract_bboxes = MagicMock()
    lyr.extract_bboxes.return_value = {
        "EPSG": {
            "top": 1,
            "bottom": -1,
            "left": -1,
            "right": 1,
        }
    }
    lyr.make_ready(minimal_dc)
    assert lyr.native_CRS == "EPSG:4326"

# NOTE: retire when native res/crs in wcs section support removed.
def test_native_crs_res_wcs_mismatch(minimal_global_cfg, minimal_layer_cfg, minimal_dc):
    minimal_layer_cfg["native_crs"] = "EPSG:4326"
    minimal_layer_cfg["product_name"] = "foo_nativecrs"
    minimal_global_cfg.wcs = True
    minimal_layer_cfg["wcs"] = {
        "native_crs": "EPSG:1234",
        "native_resolution": [0.123, 0.123],
    }

    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    lyr.extract_bboxes = MagicMock()
    lyr.extract_bboxes.return_value = {
        "EPSG": {
            "top": 1,
            "bottom": -1,
            "left": -1,
            "right": 1,
        }
    }
    lyr.make_ready(minimal_dc)
    assert lyr.native_CRS == "EPSG:4326"


def test_native_crs_none(minimal_global_cfg, minimal_layer_cfg, minimal_dc, mock_range):
    minimal_layer_cfg["product_name"] = "foo_nonativecrs"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        with pytest.raises(ConfigException) as excinfo:
            lyr.make_ready(minimal_dc)
    assert "a_layer" in str(excinfo.value)
    assert "No native CRS" in str(excinfo.value)


def test_native_crs_unpublished(minimal_global_cfg, minimal_layer_cfg, minimal_dc):
    minimal_layer_cfg["product_name"] = "foo_badnativecrs"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    lyr.extract_bboxes = MagicMock()
    lyr.extract_bboxes.return_value = {
        "EPSG": {
            "top": 1,
            "bottom": -1,
            "left": -1,
            "right": 1,
        }
    }
    with pytest.raises(ConfigException) as excinfo:
        lyr.make_ready(minimal_dc)
    assert "EPSG:9999" in str(excinfo.value)
    assert "a_layer" in str(excinfo.value)
    assert "not in published CRSs" in str(excinfo.value)


def test_no_native_resolution(minimal_global_cfg, minimal_layer_cfg, minimal_dc, mock_range):
    minimal_layer_cfg["native_crs"] = "EPSG:4326",
    minimal_layer_cfg["product_name"] = "foo_nonativeres"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        with pytest.raises(ConfigException) as excinfo:
            lyr.make_ready(minimal_dc)
    assert "a_layer" in str(excinfo.value)
    assert "No native resolution" in str(excinfo.value)


def test_no_native_resolution_noniter(minimal_global_cfg, minimal_layer_cfg, minimal_dc, mock_range):
    minimal_layer_cfg["native_crs"] = "EPSG:4326"
    minimal_layer_cfg["native_resolution"] = 45
    minimal_layer_cfg["product_name"] = "foo_nonativeres"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        with pytest.raises(ConfigException) as excinfo:
            lyr.make_ready(minimal_dc)
    assert "a_layer" in str(excinfo.value)
    assert "Invalid native resolution" in str(excinfo.value)


def test_no_native_resolution_badlen(minimal_global_cfg, minimal_layer_cfg, minimal_dc, mock_range):
    minimal_layer_cfg["native_crs"] = "EPSG:4326",
    minimal_layer_cfg["native_resolution"] = [33, 45, 2234]
    minimal_layer_cfg["product_name"] = "foo_nonativeres"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        with pytest.raises(ConfigException) as excinfo:
            lyr.make_ready(minimal_dc)
    assert "a_layer" in str(excinfo.value)
    assert "Invalid native resolution" in str(excinfo.value)


def test_native_resolution_mismatch(minimal_global_cfg, minimal_layer_cfg, minimal_dc, mock_range):
    minimal_layer_cfg["native_crs"] = "EPSG:4326"
    minimal_layer_cfg["native_resolution"] = [0.1, 0.1]
    minimal_layer_cfg["product_name"] = "foo_nativeres"
    lyr = parse_ows_layer(minimal_layer_cfg,
                          global_cfg=minimal_global_cfg)
    with patch("datacube_ows.product_ranges.get_ranges") as get_rng:
        get_rng.return_value = mock_range
        lyr.make_ready(minimal_dc)
    assert not lyr.hide
    assert lyr.ready
    assert math.isclose(lyr.resolution_x, 0.001, rel_tol=1e-8)
    assert math.isclose(lyr.resolution_y, 0.001, rel_tol=1e-8)
