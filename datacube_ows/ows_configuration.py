# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

#
#  Note this is NOT the configuration file!
#
#  This is a Python module containing the classes and functions used to load and parse configuration files.
#
#  Refer to the documentation for information on how to configure datacube_ows.
#
import datetime
import json
import logging
import math
import os
from collections.abc import Mapping
from importlib import import_module
from typing import Optional

import numpy
from babel.messages.catalog import Catalog
from babel.messages.pofile import read_po
from datacube.utils import geometry
from ows import Version
from slugify import slugify

from datacube_ows.config_utils import (FlagProductBands, OWSConfigEntry,
                                       OWSEntryNotFound,
                                       OWSExtensibleConfigEntry, OWSFlagBand,
                                       OWSMetadataConfig, cfg_expand,
                                       get_file_loc, import_python_obj,
                                       load_json_obj)
from datacube_ows.cube_pool import ODCInitException, cube, get_cube
from datacube_ows.ogc_utils import (ConfigException, FunctionWrapper,
                                    create_geobox, day_summary_date_range,
                                    local_solar_date_range, month_date_range,
                                    year_date_range)
from datacube_ows.resource_limits import (OWSResourceManagementRules,
                                          parse_cache_age)
from datacube_ows.styles import StyleDef
from datacube_ows.tile_matrix_sets import TileMatrixSet
from datacube_ows.utils import group_by_solar, group_by_statistical

_LOG = logging.getLogger(__name__)


def read_config(path=None):
    cwd = None
    if path:
        cfg_env = path
    else:
        cfg_env = os.environ.get("DATACUBE_OWS_CFG")
    if not cfg_env:
        from datacube_ows.ows_cfg import ows_cfg as cfg
    elif "/" in cfg_env or cfg_env.endswith(".json"):
        cfg = load_json_obj(cfg_env)
        cwd = get_file_loc(cfg_env)
    elif "." in cfg_env:
        cfg = import_python_obj(cfg_env)
    elif cfg_env.startswith("{"):
        cfg = json.loads(cfg_env)
        abs_path = os.path.abspath(cfg_env)
        cwd = os.path.dirname(abs_path)
    else:
        mod = import_module("datacube_ows.ows_cfg")
        cfg = getattr(mod, cfg_env)
    return cfg_expand(cfg, cwd=cwd)


class BandIndex(OWSMetadataConfig):
    METADATA_DEFAULT_BANDS = True
    METADATA_TITLE = False
    METADATA_ABSTRACT = False

    def __init__(self, layer, band_cfg):
        if band_cfg is None:
            band_cfg = {}
        super().__init__(band_cfg)
        self.band_cfg = band_cfg
        self.product = layer
        self.product_name = layer.name
        self.parse_metadata(band_cfg)
        self._idx = {}
        self.add_aliases(self.band_cfg)
        self.declare_unready("_nodata_vals")
        self.declare_unready("measurements")
        self.declare_unready("_dtypes")

    def global_config(self):
        return self.product.global_config()

    def get_obj_label(self):
        return self.product.get_obj_label() + ".bands"

    def add_aliases(self, cfg):
        for b, aliases in cfg.items():
            if b in self._idx:
                raise ConfigException(f"Duplicate band name/alias: {b} in layer {self.product_name}")
            self._idx[b] = b
            for a in aliases:
                if a != b and a in self._idx:
                    raise ConfigException(f"Duplicate band name/alias: {a} in layer {self.product_name}")
                self._idx[a] = b

    def make_ready(self, dc, *args, **kwargs):
        def floatify_nans(inp):
            if isinstance(inp, str) and inp == "nan":
                return float(inp)
            else:
                return inp
        default_to_all = not bool(self._raw_cfg)
        # pylint: disable=attribute-defined-outside-init
        self.measurements = {}
        self._nodata_vals = {}
        self._dtypes = {}
        first_product = True
        for product in self.product.products:
            if first_product and default_to_all:
                native_bands = dc.list_measurements().loc[product.name]
                for b in native_bands.index:
                    self.band_cfg[b] = [b]
                self.add_aliases(self.band_cfg)
            try:
                prod_measurements = product.lookup_measurements(list(self.band_cfg.keys()))
                if first_product:
                    self.measurements = prod_measurements
                    self._nodata_vals = {name: floatify_nans(model.nodata) for name, model in self.measurements.items()}
                    self._dtypes = {name: numpy.dtype(model.dtype) for name, model in self.measurements.items()}
                else:
                    for k in prod_measurements:
                        nodata = self._nodata_vals[k]
                        if ((numpy.isnan(nodata) and not numpy.isnan(floatify_nans(prod_measurements[k].nodata)))
                                or (not numpy.isnan(nodata) and prod_measurements[k].nodata != nodata)):
                            raise ConfigException(
                                f"Nodata value mismatch between products for band {k} in multiproduct layer {self.product.name}")
                        if prod_measurements[k].dtype != self._dtypes[k]:
                            raise ConfigException(
                                f"Data type mismatch between products for band {k} in multiproduct layer {self.product.name}")
            except KeyError as e:
                raise ConfigException(f"Product {product.name} in layer {self.product.name} is missing band {e}")
            first_product = False
        super().make_ready(dc, *args, **kwargs)

    def band(self, name_alias):
        if name_alias in self._idx:
            return self._idx[name_alias]
        raise ConfigException(f"Unknown band name/alias: {name_alias} in layer {self.product.name}")

    def locale_band(self, name_alias):
        try:
            return self.band(name_alias)
        except ConfigException:
            pass
        for b in self.band_cfg.keys():
            if name_alias == self.band_label(b):
                return b
        raise ConfigException(f"Unknown band: {name_alias} in layer {self.product.name}")

    def band_label(self, name_alias):
        canonical_name = self.band(name_alias)
        return self.read_local_metadata(canonical_name)

    def nodata_val(self, name_alias):
        name = self.band(name_alias)
        return self._nodata_vals[name]

    def dtype_val(self, name_alias):
        name = self.band(name_alias)
        return self._dtypes[name]

    def dtype_size(self, name_alias):
        return self.dtype_val(name_alias).itemsize

    def band_labels(self):
        return [self.band_label(b) for b in self.band_cfg]

    def band_nodata_vals(self):
        return [self.nodata_val(b) for b in self.band_cfg if b in self.band_cfg]


class AttributionCfg(OWSConfigEntry):
    def __init__(self, cfg, owner):
        super().__init__(cfg)
        self.owner = owner
        self.url = cfg.get("url")
        logo = cfg.get("logo")
        if not self.title and not self.url and not logo:
            raise ConfigException("At least one of title, url and logo is required in an attribution definition")
        if not logo:
            self.logo_width = None
            self.logo_height = None
            self.logo_url = None
            self.logo_fmt = None
        else:
            self.logo_width = logo.get("width")
            self.logo_height = logo.get("height")
            self.logo_url = logo.get("url")
            self.logo_fmt = logo.get("format")
            if not self.logo_url or not self.logo_fmt:
                raise ConfigException("url and format must both be specified in an attribution logo.")

    @property
    def title(self):
        return self.owner.attribution_title

    @classmethod
    def parse(cls, cfg, owner):
        if not cfg:
            return None
        else:
            return cls(cfg, owner)


class SuppURL(OWSConfigEntry):
    @classmethod
    def parse_list(cls, cfg):
        if not cfg:
            return []
        return [cls(u) for u in cfg]

    def __init__(self, cfg):
        super().__init__(cfg)
        self.url = cfg["url"]
        self.format = cfg["format"]


class OWSLayer(OWSMetadataConfig):
    METADATA_KEYWORDS = True
    METADATA_ATTRIBUTION = True

    named = False
    def __init__(self, cfg, object_label, parent_layer=None, **kwargs):
        super().__init__(cfg, **kwargs)
        self.object_label = object_label
        self.global_cfg = kwargs["global_cfg"]
        self.parent_layer = parent_layer

        self.parse_metadata(cfg)
        # Inherit or override attribution
        if "attribution" in cfg:
            self.attribution = AttributionCfg.parse(cfg.get("attribution"), self)
        elif parent_layer:
            self.attribution = self.parent_layer.attribution
        else:
            self.attribution = self.global_cfg.attribution

    def global_config(self):
        return self.global_cfg

    def can_inherit_from(self):
        if self.parent_layer:
            return self.parent_layer
        else:
            return self.global_cfg

    def get_obj_label(self):
        return self.object_label

    def layer_count(self):
        return 0

    def unready_layer_count(self):
        return 0

    def __str__(self):
        return "OWSLayer Config: %s" % self.title


class OWSFolder(OWSLayer):
    def __init__(self, cfg, global_cfg, parent_layer=None, sibling=0, **kwargs):
        if "label" in cfg:
            obj_lbl = f"folder.{cfg['label']}"
        elif parent_layer:
            obj_lbl = f"{parent_layer.object_label}.{sibling}"
        else:
            obj_lbl = f"folder.{sibling}"
        if obj_lbl in global_cfg.folder_index:
            raise ConfigException(f"Duplicate folder label: {obj_lbl}")
        super().__init__(cfg, parent_layer=parent_layer, object_label=obj_lbl, global_cfg=global_cfg, **kwargs)
        self.slug_name = slugify(self.title, separator="_")
        self.unready_layers = []
        self.child_layers = []
        if "layers" not in cfg:
            raise ConfigException("No layers section in folder layer %s" % self.title)
        child = 0
        for lyr_cfg in cfg["layers"]:
            if isinstance(lyr_cfg, Mapping):
                try:
                    lyr = parse_ows_layer(lyr_cfg, global_cfg=global_cfg, parent_layer=self, sibling=child)
                    self.unready_layers.append(lyr)
                except ConfigException as e:
                    _LOG.error("Could not parse layer (%s): %s",
                               lyr_cfg.get("name", lyr_cfg.get("title", "??")),
                               str(e))
                child += 1
            else:
                _LOG.error("Non-dictionary where dictionary expected - check for trailing comma? %s...", repr(lyr_cfg)[0:50])
        global_cfg.folder_index[obj_lbl] = self

    def unready_layer_count(self):
        return sum([l.layer_count() for l in self.unready_layers])

    def layer_count(self):
        return sum([l.layer_count() for l in self.child_layers])

    def make_ready(self, dc, *args, **kwargs):
        still_unready = []
        for lyr in self.unready_layers:
            try:
                lyr.make_ready(dc, *args, **kwargs)
                self.child_layers.append(lyr)
            except ConfigException as e:
                _LOG.error("Could not load layer %s: %s", lyr.title, str(e))
                still_unready.append(lyr)
        self.unready_layers = still_unready
        super().make_ready(dc, *args, **kwargs)


TIMERES_RAW = "raw"
TIMERES_DAY = "day"
TIMERES_MON = "month"
TIMERES_YR  = "year"

TIMERES_VALS = [TIMERES_RAW, TIMERES_DAY, TIMERES_MON, TIMERES_YR]

DEF_TIME_LATEST = "latest"
DEF_TIME_EARLIEST = "earliest"


class OWSNamedLayer(OWSExtensibleConfigEntry, OWSLayer):
    INDEX_KEYS = ["layer"]
    named = True

    def __init__(self, cfg, global_cfg, parent_layer=None, **kwargs):
        name = cfg["name"]
        super().__init__(cfg, object_label=f"layer.{name}", global_cfg=global_cfg, parent_layer=parent_layer,
                         keyvals={"layer": name},
                         **kwargs)
        self.name = name
        cfg = self._raw_cfg
        self.hide = False
        try:
            self.parse_product_names(cfg)
            if len(self.low_res_product_names) not in (0, len(self.product_names)):
                raise ConfigException(f"Lengths of product_names and low_res_product_names do not match in layer {self.name}")
            for prod_name in self.product_names:
                if "__" in prod_name:
                    # I think this was for subproducts which are currently broken
                    raise ConfigException("Product names cannot contain a double underscore '__'.")
        except IndexError:
            raise ConfigException(f"No products declared in layer {self.name}")
        except KeyError:
            raise ConfigException("Required product names entry missing in named layer %s" % self.name)
        self.declare_unready("products")
        self.declare_unready("low_res_products")
        self.declare_unready("product")
        self.declare_unready("definition")

        if global_cfg.user_band_math_extension:
            self.user_band_math = cfg.get("user_band_math", False)
        else:
            self.user_band_math = False

        self.time_resolution = cfg.get("time_resolution", TIMERES_RAW)
        if self.time_resolution not in TIMERES_VALS:
            raise ConfigException(
                "Invalid time resolution value %s in named layer %s" % (self.time_resolution, self.name))
        self.default_time_rule = cfg.get("default_time", DEF_TIME_LATEST)
        if self.default_time_rule not in (DEF_TIME_LATEST, DEF_TIME_EARLIEST):
            try:
                self.default_time_rule = datetime.date.fromisoformat(self.default_time_rule)
            except ValueError:
                raise ConfigException(
                    f"Invalid default_time value in named layer {self.name} ({self.default_time_rule})"
                )
        self.time_axis = cfg.get("time_axis")
        if self.time_axis:
            self.regular_time_axis = True
            if "time_interval" not in self.time_axis:
                raise ConfigException("No time_interval supplied in time_axis")
            self.time_axis_interval = self.time_axis["time_interval"]
            if not isinstance(self.time_axis_interval, int):
                raise ConfigException("time_interval must be an integer")
            if self.time_axis_interval <= 0:
                raise ConfigException("time_interval must be greater than zero")
            self.time_axis_start = self.time_axis.get("start_date")
            self.time_axis_end = self.time_axis.get("end_date")
            if self.time_axis_start is not None:
                try:
                    self.time_axis_start = datetime.date.fromisoformat(self.time_axis_start)
                except ValueError:
                    raise ConfigException("time_axis start_date is not a valid ISO format date string")
            if self.time_axis_end is not None:
                try:
                    self.time_axis_end = datetime.date.fromisoformat(self.time_axis_end)
                except ValueError:
                    raise ConfigException("time_axis end_date is not a valid ISO format date string")
            if (self.time_axis_end is not None
                    and self.time_axis_start is not None
                    and self.time_axis_end < self.time_axis_start):
                raise ConfigException("time_axis end_date must be greater than or equal to the start_date if both are provided")
        else:
            self.regular_time_axis = False
            self.time_axis_interval = 0
            self.time_axis_start = None
            self.time_axis_end = None

        self.dynamic = cfg.get("dynamic", False)

        self.declare_unready("default_time")
        self.declare_unready("_ranges")
        self.declare_unready("bboxes")
        # TODO: sub-ranges
        self.band_idx = BandIndex(self, cfg.get("bands"))
        self.cfg_native_resolution = cfg.get("native_resolution")
        self.cfg_native_crs = cfg.get("native_crs")
        self.declare_unready("resolution_x")
        self.declare_unready("resolution_y")
        self.resource_limits = OWSResourceManagementRules(self.global_cfg, cfg.get("resource_limits", {}), f"Layer {self.name}")
        try:
            self.parse_flags(cfg.get("flags", {}))
            self.declare_unready("all_flag_band_names")
        except KeyError as e:
            raise ConfigException(f"Missing required config ({str(e)}) in flags section for layer {self.name}")
        try:
            self.parse_image_processing(cfg["image_processing"])
        except KeyError as e:
            raise ConfigException(f"Missing required config ({str(e)}) in image processing section for layer {self.name}")
        self.identifiers = cfg.get("identifiers", {})
        for auth in self.identifiers.keys():
            if auth not in self.global_cfg.authorities:
                raise ConfigException(f"Identifier with non-declared authority: {auth} in layer {self.name}")
        self.parse_urls(cfg.get("urls", {}))
        self.parse_feature_info(cfg.get("feature_info", {}))
        self.feature_info_include_utc_dates = cfg.get("feature_info_url_dates", False)
        if "patch_url_function" in cfg:
            self.patch_url = FunctionWrapper(self, cfg["patch_url_function"])
        else:
            self.patch_url = None
        try:
            self.parse_styling(cfg["styling"])
        except KeyError as e:
            raise ConfigException(f"Missing required config item {e} in styling section for layer {self.name}")

        if self.global_cfg.wcs:
            try:
                self.parse_wcs(cfg.get("wcs", {}))
            except KeyError as e:
                raise ConfigException(f"Missing required config item {e} in wcs section for layer {self.name}")

#       Sub-products have been broken for some time.
#        sub_prod_cfg = cfg.get("sub_products", {})
#        self.sub_product_label = sub_prod_cfg.get("label")
#        if "extractor" in sub_prod_cfg:
#            self.sub_product_extractor = FunctionWrapper(self, sub_prod_cfg["extractor"])
#        else:
#            self.sub_product_extractor = None
        # And finally, add to the global product index.
        existing = self.global_cfg.product_index.get(self.name)
        if existing and existing != self:
            raise ConfigException(f"Duplicate layer name: {self.name}")
        self.global_cfg.product_index[self.name] = self

    def time_axis_representation(self):
        if self.regular_time_axis:
            start, end = self.time_range(self.ranges)
            return f"{start.isoformat()}/{end.isoformat()}/P{self.time_axis_interval}D"
        return ""

    # pylint: disable=attribute-defined-outside-init
    def make_ready(self, dc, *args, **kwargs):
        self.products = []
        self.low_res_products = []
        for i, prod_name in enumerate(self.product_names):
            if self.low_res_product_names:
                low_res_prod_name = self.low_res_product_names[i]
            else:
                low_res_prod_name = None
            product = dc.index.products.get_by_name(prod_name)
            if not product:
                raise ConfigException(f"Could not find product {prod_name} in datacube for layer {self.name}")
            self.products.append(product)
            if low_res_prod_name:
                product = dc.index.products.get_by_name(low_res_prod_name)
                if not product:
                    raise ConfigException(f"Could not find product {low_res_prod_name} in datacube for layer {self.name}")
                self.low_res_products.append(product)
        self.product = self.products[0]
        self.definition = self.product.definition
        self.force_range_update(dc)
        self.band_idx.make_ready(dc)
        self.resource_limits.make_ready(dc)
        self.all_flag_band_names = set()
        for fb in self.flag_bands.values():
            fb.make_ready(dc)
            if fb.pq_band in self.all_flag_band_names:
                raise ConfigException(f"Duplicate flag band name: {fb.pq_band}")
            self.all_flag_band_names.add(fb.pq_band)
        self.ready_image_processing(dc)
        self.ready_native_specs()
        if self.global_cfg.wcs:
            self.ready_wcs(dc)
        for style in self.styles:
            style.make_ready(dc, *args, **kwargs)
        for fpb in self.allflag_productbands:
            fpb.make_ready(dc, *args, **kwargs)
        if not self.multi_product:
            self.global_cfg.native_product_index[self.product_name] = self

        if not self.hide:
            super().make_ready(dc, *args, **kwargs)

    # pylint: disable=attribute-defined-outside-init
    def parse_image_processing(self, cfg):
        emf_cfg = cfg["extent_mask_func"]
        if isinstance(emf_cfg, Mapping) or isinstance(emf_cfg, str):
            self.extent_mask_func = [FunctionWrapper(self, emf_cfg)]
        else:
            self.extent_mask_func = list([FunctionWrapper(self, emf) for emf in emf_cfg])
        self.raw_afb = cfg.get("always_fetch_bands", [])
        self.declare_unready("always_fetch_bands")
        self.solar_correction = cfg.get("apply_solar_corrections", False)
        self.data_manual_merge = cfg.get("manual_merge", False)
        if self.solar_correction and not self.data_manual_merge:
            raise ConfigException("Solar correction requires manual_merge.")
        if self.data_manual_merge and not self.solar_correction and not self.multi_product:
            _LOG.warning("Manual merge is only recommended where solar correction is required and for multi-product layers.")

        if cfg.get("fuse_func"):
            self.fuse_func = FunctionWrapper(self, cfg["fuse_func"])
        else:
            self.fuse_func = None

    # pylint: disable=attribute-defined-outside-init
    def ready_image_processing(self, dc):
        self.always_fetch_bands = list([self.band_idx.band(b) for b in self.raw_afb])

    # pylint: disable=attribute-defined-outside-init
    def parse_feature_info(self, cfg):
        self.feature_info_include_utc_dates = cfg.get("include_utc_dates", False)
        custom = cfg.get("include_custom", {})
        self.feature_info_custom_includes = {k: FunctionWrapper(self, v) for k, v in custom.items()}

    # pylint: disable=attribute-defined-outside-init
    def parse_flags(self, cfg):
        self.flag_bands = {}
        if cfg:
            if isinstance(cfg, dict):
                fb = OWSFlagBand(cfg, self)
                self.flag_bands[fb.pq_band] = fb
                _LOG.warning("Single flag bands not in a list is deprecated. Please refer to the documentation for the new format (layer %s)", self.name)
            else:
                for fb_cfg in cfg:
                    fb = OWSFlagBand(fb_cfg, self)
                    self.flag_bands[fb.pq_band] = fb
        pq_names_to_lowres_names = {}
        for fb in self.flag_bands.values():
            pns = fb.pq_names
            lrpns = fb.pq_low_res_names
            if pns in pq_names_to_lowres_names and pq_names_to_lowres_names[pns] != lrpns:
                raise ConfigException(f"Product name mismatch in flags section for layer {self.name}: product_names {pns} has multiple distinct low-res product names")
            pq_names_to_lowres_names[pns] = lrpns
        # pylint: disable=dict-values-not-iterating
        self.allflag_productbands = FlagProductBands.build_list_from_flagbands(self.flag_bands.values(), self)

    # pylint: disable=attribute-defined-outside-init
    def parse_urls(self, cfg):
        self.feature_list_urls = SuppURL.parse_list(cfg.get("features", []))
        self.data_urls = SuppURL.parse_list(cfg.get("data", []))

    # pylint: disable=attribute-defined-outside-init
    def parse_styling(self, cfg):
        self.styles = []
        self.style_index = {}
        for scfg in cfg["styles"]:
            style = StyleDef(self, scfg)
            self.styles.append(style)
            self.style_index[style.name] = style
        if "default_style" in cfg:
            if cfg["default_style"] not in self.style_index:
                raise ConfigException(f"Default style {cfg['default_style']} is not in the 'styles' for layer {self.name}")
            self.default_style = self.style_index[cfg["default_style"]]
        else:
            self.default_style = self.styles[0]

    # pylint: disable=attribute-defined-outside-init
    def parse_wcs(self, cfg):
        if cfg == False:
            self.wcs = False
        elif not self.global_cfg.wcs:
            self.wcs = False
        else:
            self.wcs = not cfg.get("disable", False)
        if not self.wcs:
            return

        if "native_resolution" in cfg:
            if not self.cfg_native_resolution:
                _LOG.warning(
                    "Specifying native_resolution in wcs section of layer %s is now deprecated, please move to "
                    "main layer section if required.", self.name)
                self.cfg_native_resolution = cfg.get("native_resolution")
            else:
                _LOG.warning(
                    "Native_resolution in wcs section of layer %s ignored in favour of value in "
                    "main layer section.", self.name)

        # Native CRS
        if "native_crs" in cfg:
            if not self.cfg_native_crs:
                _LOG.warning("Specifying native_crs in wcs section of layer %s is now deprecated, pleas move to "
                             "main layer section if required", self.name)
                self.cfg_native_crs = cfg["native_crs"]
            else:
                _LOG.warning(
                    "native_crs in wcs section of layer %s ignored in favour of value in "
                    "main layer section.", self.name)

        self.declare_unready("native_CRS")
        self.declare_unready("native_CRS_def")

        # Rectified Grids
        self.declare_unready("origin_x")
        self.declare_unready("origin_y")
        self.declare_unready("grid_high_x")
        self.declare_unready("grid_high_y")
        self.declare_unready("grids")
        # Band management
        if cfg.get("default_bands"):
            _LOG.warning(
                "wcs section contains a 'default_bands' list.  WCS default_bands list is no longer supported. "
                "Functionally, the default behaviour is now to return all available bands (as mandated by "
                "the WCS2.x spec). "
            )

        # Native format
        if "native_format" in cfg:
            self.native_format = cfg["native_format"]
            if self.native_format not in self.global_cfg.wcs_formats_by_name:
                raise ConfigException(f"WCS native format {self.native_format} for layer {self.name} is not in supported formats list")
        else:
            self.native_format = self.global_cfg.native_wcs_format

    # pylint: disable=attribute-defined-outside-init
    def ready_native_specs(self):
        # Native CRS
        try:
            self.native_CRS = self.product.definition["storage"]["crs"]
            if self.cfg_native_crs == self.native_CRS:
                _LOG.debug(
                    "Native crs for layer %s is specified in ODC metadata and does not need to be specified in configuration",
                    self.name)
            else:
                _LOG.warning("Native crs for layer %s is specified in config as %s - overridden to %s by ODC metadata",
                             self.name, self.cfg_native_crs, self.native_CRS)
        except KeyError:
            self.native_CRS = self.cfg_native_crs

        if not self.native_CRS:
            raise ConfigException(f"No native CRS could be found for layer {self.name}")
        if self.native_CRS not in self.global_cfg.published_CRSs:
            raise ConfigException(
                f"Native CRS for product {self.product_name} in layer {self.name} ({self.native_CRS}) not in published CRSs")
        self.native_CRS_def = self.global_cfg.published_CRSs[self.native_CRS]

        try:
            # Native CRS
            self.resolution_x = self.product.definition["storage"]["resolution"][
                self.native_CRS_def["horizontal_coord"]]
            self.resolution_y = self.product.definition["storage"]["resolution"][self.native_CRS_def["vertical_coord"]]
        except KeyError:
            self.resolution_x = None
            self.resolution_y = None

        if self.resolution_x is None:
            try:
                if self.cfg_native_resolution is None:
                    raise KeyError
                self.resolution_x, self.resolution_y = self.cfg_native_resolution
            except KeyError:
                raise ConfigException(
                    f"No native resolution supplied for layer {self.name} with no product-native resolution defined in ODC."
                )
            except ValueError:
                raise ConfigException(f"Invalid native resolution supplied for layer {self.name}")
            except TypeError:
                raise ConfigException(f"Invalid native resolution supplied for layer {self.name}")
        elif self.cfg_native_resolution:
            config_x, config_y = (float(r) for r in self.cfg_native_resolution)
            if (
                    math.isclose(config_x, float(self.resolution_x), rel_tol=1e-8)
                    and math.isclose(config_y, float(self.resolution_y), rel_tol=1e-8)
            ):
                _LOG.debug(
                    "Native resolution for layer %s is specified in ODC metadata and does not need to be specified in configuration",
                    self.name)
            else:
                _LOG.warning(
                    "Native resolution for layer %s is specified in config as %s - overridden to (%.15f, %.15f) by ODC metadata",
                    self.name, repr(self.cfg_native_resolution), self.resolution_x, self.resolution_y)

    # pylint: disable=attribute-defined-outside-init
    def ready_wcs(self, dc):
        if self.global_cfg.wcs and self.wcs:

            # Prepare Rectified Grids
            try:
                native_bounding_box = self.bboxes[self.native_CRS]
            except KeyError:
                if not self.global_cfg.called_from_update_ranges:
                    _LOG.warning("Layer: %s No bounding box in ranges for native CRS %s - rerun update_ranges.py",
                                 self.name,
                                 self.native_CRS)
                self.hide = True
                return
            self.origin_x = native_bounding_box["left"]
            self.origin_y = native_bounding_box["bottom"]


            if (native_bounding_box["right"] - native_bounding_box["left"]) < self.resolution_x:
                ConfigException(
                    "Native (%s) bounding box on layer %s has left %.8f, right %.8f (diff %d), but horizontal resolution is %.8f"
                    % (
                        self.native_CRS,
                        self.name,
                        native_bounding_box["left"],
                        native_bounding_box["right"],
                        native_bounding_box["right"] - native_bounding_box["left"],
                        self.resolution_x
                    ))
            if (native_bounding_box["top"] - native_bounding_box["bottom"]) < self.resolution_x:
                ConfigException(
                    "Native (%s) bounding box on layer %s has bottom %f, top %f (diff %d), but vertical resolution is %f"
                    % (
                        self.native_CRS,
                        self.name,
                        native_bounding_box["bottom"],
                        native_bounding_box["top"],
                        native_bounding_box["top"] - native_bounding_box["bottom"],
                        self.resolution_y

                    ))
            self.grid_high_x = abs(int((native_bounding_box["right"] - native_bounding_box["left"]) / self.resolution_x))
            self.grid_high_y = int((native_bounding_box["bottom"] - native_bounding_box["top"]) / self.resolution_y)

            if self.grid_high_x <= 0:
                err_str = f"Grid High x is non-positive on layer {self.name}: native ({self.native_CRS}) extent: {native_bounding_box['left']},{native_bounding_box['right']}: x_res={self.resolution_x}"
                raise ConfigException(err_str)
            if self.grid_high_y <= 0:
                err_str = f"Grid High y is non-positive on layer {self.name}: native ({self.native_CRS}) extent: {native_bounding_box['bottom']},{native_bounding_box['top']}: y_res={self.resolution_y}"
                raise ConfigException(err_str)
            self.grids = {}
            for crs, crs_def in self.global_cfg.published_CRSs.items():
                if crs == self.native_CRS:
                    self.grids[crs] = {
                        "origin": (self.origin_x, self.origin_y),
                        "resolution": (self.resolution_x, self.resolution_y),
                    }
                else:
                    try:
                        bbox = self.bboxes[crs]
                    except KeyError:
                        continue
                    self.grids[crs] = {
                        "origin": (bbox["left"], bbox["bottom"]),
                        "resolution": (
                            (bbox["right"] - bbox["left"]) / self.grid_high_x,
                            (bbox["top"] - bbox["bottom"]) / self.grid_high_y
                        )
                    }

    def parse_product_names(self, cfg):
        raise NotImplementedError()

    def parse_pq_names(self, cfg):
        raise NotImplementedError()

    def force_range_update(self, ext_dc=None):
        if ext_dc:
            dc = ext_dc
        else:
            dc = get_cube()
        self.hide = False
        self._ranges = None
        try:
            from datacube_ows.product_ranges import get_ranges
            self._ranges = get_ranges(dc, self)
            if self._ranges is None:
                raise Exception("Null product range")
            self.bboxes = self.extract_bboxes()
            if self.default_time_rule == DEF_TIME_EARLIEST:
                self.default_time = self._ranges["start_time"]
            elif isinstance(self.default_time_rule,
                            datetime.date) and self.default_time_rule in self._ranges["time_set"]:
                self.default_time = self.default_time_rule
            elif isinstance(self.default_time_rule, datetime.date):
                _LOG.warning("default_time for named_layer %s is explicit date (%s) that is "
                             " not available for the layer. Using most recent available date instead.",
                                    self.name,
                                    self.default_time_rule.isoformat()
                )
                self.default_time = self._ranges["end_time"]
            else:
                self.default_time = self._ranges["end_time"]

        # pylint: disable=broad-except
        except Exception as a:
            if not self.global_cfg.called_from_update_ranges:
                _LOG.warning("get_ranges failed for layer %s: %s", self.name, str(a))
            self.hide = True
            self.bboxes = {}

    def time_range(self, ranges=None):
        if ranges is None:
            ranges = self.ranges
        if self.regular_time_axis and self.time_axis_start:
            start = self.time_axis_start
        else:
            start = ranges["times"][0]
        if self.regular_time_axis and self.time_axis_end:
            end = self.time_axis_end
        else:
            end = ranges["times"][-1]
        return (start, end)

    @property
    def ranges(self):
        if self.dynamic:
            self.force_range_update()
        return self._ranges

    def extract_bboxes(self):
        if self._ranges is None:
            return {}
        bboxes = {}
        for crs_id, bbox in self._ranges["bboxes"].items():
            if crs_id in self.global_cfg.published_CRSs:
                # Assume we've already handled coordinate swapping for
                # Vertical-coord first CRSs.   Top is top, left is left.
                bboxes[crs_id] = {
                    "right": bbox["right"],
                    "left": bbox["left"],
                    "top": bbox["top"],
                    "bottom": bbox["bottom"],
                    "vertical_coord_first": self.global_cfg.published_CRSs[crs_id]["vertical_coord_first"]
                }
        return bboxes

    def layer_count(self):
        return 1

    @property
    def is_raw_time_res(self):
        return self.time_resolution == TIMERES_RAW

    @property
    def is_day_time_res(self):
        return self.time_resolution == TIMERES_DAY

    @property
    def is_month_time_res(self):
        return self.time_resolution == TIMERES_MON

    @property
    def is_year_time_res(self):
        return self.time_resolution == TIMERES_YR

    def search_times(self, t, geobox=None):
        if self.is_month_time_res:
            return month_date_range(t)
        elif self.is_year_time_res:
            return year_date_range(t)
        elif self.is_day_time_res:
            return day_summary_date_range(t)
        else:
            if not geobox:
                bbox = self.ranges["bboxes"][self.native_CRS]
                geobox = create_geobox(
                    self.native_CRS,
                    bbox["left"], bbox["bottom"], bbox["right"], bbox["top"],
                    1, 1
                )
            return local_solar_date_range(geobox, t)

    def dataset_groupby(self):
        if self.is_raw_time_res:
            return "solar_day"
        else:
            return group_by_statistical()

    def __str__(self):
        return "Named OWSLayer: %s" % self.name

    @classmethod
    def lookup_impl(cls, cfg, keyvals, subs=None):
        try:
            return cfg.product_index[keyvals["layer"]]
        except KeyError:
            raise OWSEntryNotFound(f"Layer {keyvals['layer']} not found")


class OWSProductLayer(OWSNamedLayer):
    multi_product = False

    def parse_product_names(self, cfg):
        self.product_name = cfg["product_name"]
        self.product_names = (self.product_name,)

        self.low_res_product_name  = cfg.get("low_res_product_name")
        if self.low_res_product_name:
            self.low_res_product_names = (self.low_res_product_name,)
        else:
            self.low_res_product_names = tuple()
        if "product_names" in cfg:
            raise ConfigException(f"'product_names' entry in non-multi-product layer {self.name} - use 'product_name' only")
        if "low_res_product_names" in cfg:
            raise ConfigException(f"'low_res_product_names' entry in non-multi-product layer {self.name} - use 'low_res_product_name' only")

    def parse_pq_names(self, cfg):
        main_product = False
        if "dataset" in cfg:
            raise ConfigException(f"The 'dataset' entry in the flags section is no longer supported.  Please refer to the documentation for the correct format (layer {self.name})")
        if "product" in cfg:
            pq_names = (cfg["product"],)
        else:
            pq_names = (self.product_name,)
            main_product = (pq_names[0] == self.product_name)

        if "low_res_product" in cfg:
            pq_low_res_names = (cfg.get("low_res_product"),)
        elif main_product:
            pq_low_res_names = self.low_res_product_names
        else:
            pq_low_res_names = pq_names

        if "products" in cfg:
            raise ConfigException(f"'products' entry in flags section of non-multi-product layer {self.name} - use 'product' only")
        if "low_res_products" in cfg:
            raise ConfigException(f"'low_res_products' entry in flags section of non-multi-product layer {self.name}- use 'low_res_product' only")
        return {
            "pq_names": pq_names,
            "pq_low_res_names": pq_low_res_names,
            "main_products": main_product
        }


class OWSMultiProductLayer(OWSNamedLayer):
    multi_product = True

    def parse_product_names(self, cfg):
        self.product_names = tuple(cfg["product_names"])
        self.product_name = self.product_names[0]
        self.low_res_product_names = tuple(cfg.get("low_res_product_names", []))
        if self.low_res_product_names:
            self.low_res_product_name = self.low_res_product_names[0]
        else:
            self.low_res_product_name = None
        if "product_name" in cfg:
            raise ConfigException(f"'product_name' entry in multi-product layer {self.name} - use 'product_names' only")
        if "low_res_product_name" in cfg:
            raise ConfigException(f"'low_res_product_name' entry in multi-product layer {self.name} - use 'low_res_product_names' only")

    def parse_pq_names(self, cfg):
        main_products = False
        if "datasets" in cfg:
            raise ConfigException(f"The 'datasets' entry in the flags section is no longer supported. Please refer to the documentation for the correct format (layer {self.name})")
        if "products" in cfg:
            pq_names = tuple(cfg["products"])
            main_products = pq_names == self.product_names
        else:
            main_products = True
            pq_names = self.product_names

        if "low_res_products" in cfg:
            pq_low_res_names = tuple(cfg["low_res_products"])
        else:
            pq_low_res_names = self.low_res_product_names
        if "product" in cfg:
            raise ConfigException(f"'product' entry in flags section of multi-product layer {self.name} - use 'products' only")
        if "low_res_product" in cfg:
            raise ConfigException(f"'low_res_product' entry in flags section of multi-product layer {self.name} - use 'low_res_products' only")
        return {
            "pq_names": pq_names,
            "pq_low_res_names": pq_low_res_names,
            "main_products": main_products,
        }

    def dataset_groupby(self):
        if self.is_raw_time_res:
            return group_by_solar(self.product_names)
        else:
            return group_by_statistical(self.product_names)


def parse_ows_layer(cfg, global_cfg, parent_layer=None, sibling=0):
    if cfg.get("name", None):
        if cfg.get("multi_product", False):
            return OWSMultiProductLayer(cfg, global_cfg, parent_layer)
        else:
            return OWSProductLayer(cfg, global_cfg, parent_layer)
    else:
        return OWSFolder(cfg, global_cfg, parent_layer=parent_layer, sibling=sibling)


class WCSFormat:
    @staticmethod
    def from_cfg(cfg):
        renderers = []
        for name, fmt in cfg.items():
            if "renderers" in fmt:
                renderers.append(
                    WCSFormat(
                        name,
                        fmt["mime"],
                        fmt["extension"],
                        fmt["renderers"],
                        fmt.get("multi-time", False)
                    )
                )
            elif "renderer" in fmt:
                _LOG.warning("'renderer' in WCS format declarations is "
                      "deprecated. Please review the latest example config "
                      "file and update your config file accordingly. Format %s "
                      "will be WCS 1 only.", name)
                renderers.append(
                    WCSFormat(
                        name,
                        fmt["mime"],
                        fmt["extension"],
                        {"1": fmt["renderer"]},
                        fmt.get("multi-time", False)
                    )
                )
        return renderers

    def __init__(self, name, mime, extension, renderers,
                 multi_time):
        self.name = name
        self.mime = mime
        self.extension = extension
        self.multi_time = multi_time
        self.renderers = {
            int(ver): FunctionWrapper(None, renderer)
            for ver, renderer in renderers.items()
        }
        if 1 not in self.renderers:
            _LOG.warning("No renderer supplied for WCS 1.x for format %s", self.name)
        if 2 not in self.renderers:
            _LOG.warning("Warning: No renderer supplied for WCS 2.x for format %s", self.name)

    def renderer(self, version):
        if isinstance(version, str):
            version = int(version.split(".")[0])
        elif isinstance(version, Version):
            version = version.major
        return self.renderers[version]


class ContactInfo(OWSConfigEntry):
    def __init__(self, cfg, global_cfg):
        super().__init__(cfg)
        self.global_cfg = global_cfg
        self.person = cfg.get("person")

        class Address(OWSConfigEntry):
            def __init__(self, cfg):
                super().__init__(cfg)
                self.type = cfg.get("type")
                self.address = cfg.get("address")
                self.city = cfg.get("city")
                self.state = cfg.get("state")
                self.postcode = cfg.get("postcode")
                self.country = cfg.get("country")

            @classmethod
            def parse(cls, cfg):
                if not cfg:
                    return None
                else:
                    return cls(cfg)

        self.address = Address.parse(cfg.get("address"))
        self.telephone = cfg.get("telephone")
        self.fax = cfg.get("fax")
        self.email = cfg.get("email")

    @property
    def organisation(self):
        return self.global_cfg.contact_org

    @property
    def position(self):
        return self.global_cfg.contact_position

    @classmethod
    def parse(cls, cfg, global_cfg):
        if cfg:
            return cls(cfg, global_cfg)
        else:
            return None


class OWSConfig(OWSMetadataConfig):
    _instance = None
    initialised = False

    def __new__(cls, *args, **kwargs):
        if not cls._instance or kwargs.get("refresh"):
            cls._instance = super().__new__(cls)
        return cls._instance

    METADATA_KEYWORDS = True
    METADATA_ATTRIBUTIONS = True
    METADATA_FEES = True
    METADATA_ACCESS_CONSTRAINTS = True
    METADATA_CONTACT_INFO = True

    @property
    def default_abstract(self) -> Optional[str]:
        return ""

    @property
    def active_products(self):
        return filter(lambda x: not x.hide, self.product_index.values())

    @property
    def active_product_index(self):
        return {prod.name: prod for prod in self.active_products}

    def __init__(self, refresh=False, cfg=None, ignore_msgfile=False, called_from_update_ranges=False):
        self.called_from_update_ranges = called_from_update_ranges
        if not self.initialised or refresh:
            self.msgfile = None
            if not cfg:
                cfg = read_config()
            super().__init__(cfg)
            try:
                self.parse_global(cfg["global"], ignore_msgfile)
            except KeyError as e:
                raise ConfigException(
                    "Missing required config entry in 'global' section: %s" % str(e)
                )

            if self.wms or self.wmts:
                self.parse_wms(cfg.get("wms", {}))
            else:
                self.parse_wms({})

            if self.wcs:
                try:
                    self.parse_wcs(cfg.get("wcs"))
                except KeyError as e:
                    raise ConfigException(
                        "Missing required config entry in 'wcs' section (with WCS enabled): %s" % str(e)
                    )
            else:
                self.parse_wcs(None)
            try:
                self.parse_layers(cfg["layers"])
            except KeyError as e:
                raise ConfigException("Missing required config entry in 'layers' section")

            try:
                if self.wmts:
                    self.parse_wmts(cfg.get("wmts", {}))
                else:
                    self.parse_wmts({})
            except KeyError as e:
                raise ConfigException(
                    "Missing required config entry in 'wmts' section (with WCS enabled): %s" % str(e)
                )
            self.catalog = None
            self.initialised = True

    #pylint: disable=attribute-defined-outside-init
    def make_ready(self, dc, *args, **kwargs):
        if self.msg_file_name:
            try:
                with open(self.msg_file_name, "rb") as fp:
                    self.set_msg_src(read_po(fp, locale=self.default_locale, domain=self.message_domain))
            except FileNotFoundError:
                _LOG.warning("Message file %s does not exist - using metadata from config file", self.msg_file_name)
        else:
            self.set_msg_src(None)
        self.native_product_index = {}
        self.root_layer_folder.make_ready(dc, *args, **kwargs)
        super().make_ready(dc, *args, **kwargs)

    def export_metadata(self):
        if self.catalog is None:
            now = datetime.datetime.now()
            self.catalog = Catalog(locale=self.default_locale,
                                   domain=self.message_domain,
                                   header_comment=f"""# Translations for datacube-ows metadata instance:
#      {self.title}
#
# {self.contact_info.organisation} {now.isoformat()}
#""",
                                   project=self.title,
                                   version=f"{now.isoformat()}",
                                   copyright_holder=self.contact_info.organisation,
                                   msgid_bugs_address=self.contact_info.email,
                                   creation_date=now,
                                   revision_date=now,
                                   fuzzy=False)
            for k, v in self._metadata_registry.items():
                if self._inheritance_registry[k]:
                    continue
                if k in [
                        "folder.ows_root_hidden.title",
                        "folder.ows_root_hidden.abstract",
                        "folder.ows_root_hidden.local_keywords",
                 ]:
                    continue
                self.catalog.add(id=k, string=v, auto_comments=[v])
        return self.catalog

    def parse_global(self, cfg, ignore_msgfile):
        self._response_headers = cfg.get("response_headers", {})
        self.wms = cfg.get("services", {}).get("wms", True)
        self.wmts = cfg.get("services", {}).get("wmts", True)
        self.wcs = cfg.get("services", {}).get("wcs", False)
        if not self.wms and not self.wmts and not self.wcs:
            raise ConfigException("At least one service must be active.")
        self.locales = cfg.get("supported_languages", ["en"])
        if len(self.locales) < 1:
            raise ConfigException("You must support at least one language.")
        self.default_locale = self.locales[0]
        self.message_domain = cfg.get("message_domain", "ows_cfg")
        self.translations_dir = cfg.get("translations_directory")
        self.internationalised = self.translations_dir and len(self.locales) > 1
        if self.internationalised:
            _LOG.info("Internationalisation enabled.")
        if ignore_msgfile:
            self.msg_file_name = None
        else:
            self.msg_file_name = cfg.get("message_file")
        self.parse_metadata(cfg)
        self.allowed_urls = cfg["allowed_urls"]
        self.info_url = cfg["info_url"]
        self.contact_info = ContactInfo.parse(cfg.get("contact_info"), self)
        self.attribution = AttributionCfg.parse(cfg.get("attribution"), self)

        def make_gml_name(name):
            if name.startswith("EPSG:"):
                return f"http://www.opengis.net/def/crs/EPSG/0/{name[5:]}"
            else:
                return name

        self.published_CRSs = {}
        self.internal_CRSs = {}
        CRS_aliases = {}
        geographic_CRSs = []
        for crs_str, crsdef in cfg["published_CRSs"].items():
            if "alias" in crsdef:
                CRS_aliases[crs_str] = crsdef
                continue
            self.internal_CRSs[crs_str] = {
                "geographic": crsdef["geographic"],
                "horizontal_coord": crsdef.get("horizontal_coord", "longitude"),
                "vertical_coord": crsdef.get("vertical_coord", "latitude"),
                "vertical_coord_first": crsdef.get("vertical_coord_first", False),
                "gml_name": make_gml_name(crs_str),
                "alias_of": None
            }
            if crsdef["geographic"]:
                geographic_CRSs.append(crs_str)
            self.published_CRSs[crs_str] = self.internal_CRSs[crs_str]
            if self.published_CRSs[crs_str]["geographic"]:
                if self.published_CRSs[crs_str]["horizontal_coord"] != "longitude":
                    raise ConfigException(f"Published CRS {crs_str} is geographic"
                                    "but has a horizontal coordinate that is not 'longitude'")
                if self.published_CRSs[crs_str]["vertical_coord"] != "latitude":
                    raise ConfigException(f"Published CRS {crs_str} is geographic"
                                    "but has a vertical coordinate that is not 'latitude'")
        # default_geographic_CRS is used by WCS1
        if not self.wcs:
            self.default_geographic_CRS = ""
        elif not geographic_CRSs:
            raise ConfigException(f"At least one geographic CRS must be supplied")
        elif "EPSG:4326" in geographic_CRSs or "WGS-84" in geographic_CRSs:
            self.default_geographic_CRS = "urn:ogc:def:crs:OGC:1.3:CRS84"
        else:
            self.default_geographic_CRS = geographic_CRSs[0]

        for alias, alias_def in CRS_aliases.items():
            target_crs = alias_def["alias"]
            if target_crs not in self.published_CRSs:
                _LOG.warning("CRS %s defined as alias for %s, which is not a published CRS - skipping",
                             alias, target_crs)
                continue
            target_def = self.published_CRSs[target_crs]
            self.published_CRSs[alias] = target_def.copy()
            self.published_CRSs[alias]["gml_name"] = make_gml_name(alias)
            self.published_CRSs[alias]["alias_of"] = target_crs

    def parse_wms(self, cfg):
        if not self.wms and not self.wmts:
            cfg = {}
        self.s3_bucket = cfg.get("s3_bucket", "")
        self.s3_url = cfg.get("s3_url", "")
        self.s3_aws_zone = cfg.get("s3_aws_zone", "")
        try:
            self.wms_max_width = int(cfg.get("max_width", 256))
            self.wms_max_height = int(cfg.get("max_height", 256))
        except ValueError:
            raise ConfigException(
                f"max_width and max_height in wms section must be integers: {cfg.get('max_width', 256)},{cfg.get('max_height', 256)}"
            )
        if self.wms_max_width < 1 or self.wms_max_height < 1:
            raise ConfigException(
                f"max_width and max_height in wms section must be positive integers: {cfg.get('max_width', 256)},{cfg.get('max_height', 256)}"
            )
        self.authorities = cfg.get("authorities", {})
        self.user_band_math_extension = cfg.get("user_band_math_extension", False)
        self.wms_cap_cache_age = parse_cache_age(cfg, "caps_cache_maxage", "wms")
        if "attribution" in cfg:
            _LOG.warning("Attribution entry in top level 'wms' section will be ignored. Attribution should be moved to the 'global' section")

    def parse_wcs(self, cfg):
        if self.wcs:
            if not isinstance(cfg, Mapping):
                raise ConfigException("WCS section missing (and WCS is enabled)")
            self.wcs_formats = WCSFormat.from_cfg(cfg["formats"])
            self.wcs_formats_by_name = {
                fmt.name: fmt
                for fmt in self.wcs_formats
            }
            self.wcs_formats_by_mime = {
                fmt.mime: fmt
                for fmt in self.wcs_formats
            }
            if not self.wcs_formats:
                raise ConfigException("Must configure at least one wcs format to support WCS.")

            self.native_wcs_format = cfg["native_format"]
            if self.native_wcs_format not in self.wcs_formats_by_name:
                raise ConfigException(f"Configured native WCS format ({self.native_wcs_format}) not a supported format.")
            self.wcs_tiff_statistics = cfg.get("calculate_tiff_statistics", True)
            self.wcs_cap_cache_age = parse_cache_age(cfg, "caps_cache_maxage", "wcs")
            self.wcs_default_descov_age = parse_cache_age(cfg, "default_desc_cache_maxage", "wcs")
        else:
            self.wcs_formats = []
            self.wcs_formats_by_name = {}
            self.wcs_formats_by_mime = {}
            self.native_wcs_format = None
            self.wcs_tiff_statistics = False
            self.wcs_cap_cache_age = 0
            self.wcs_default_descov_age = 0

    def parse_wmts(self, cfg):
        tms_cfgs = TileMatrixSet.default_tm_sets.copy()
        if "tile_matrix_sets" in cfg:
            for identifier, tms in cfg["tile_matrix_sets"].items():
                tms_cfgs[identifier] = tms
        self.tile_matrix_sets = {}
        for identifier, tms in tms_cfgs.items():
            if len(identifier.split()) != 1:
                raise ConfigException(f"Invalid identifier: {identifier}")
            if identifier in self.tile_matrix_sets:
                raise ConfigException(f"Tile matrix set identifiers must be unique: {identifier}")
            self.tile_matrix_sets[identifier] = TileMatrixSet(identifier, tms, self)

    def parse_layers(self, cfg):
        self.folder_index = {}
        self.product_index = {}
        self.declare_unready("native_product_index")
        self.root_layer_folder = OWSFolder({
            "title": "Root Folder (hidden)",
            "label": "ows_root_hidden",
            "layers": cfg
        }, global_cfg=self, parent_layer=None)

    @property
    def layers(self):
        return self.root_layer_folder.child_layers

    def alias_bboxes(self, bboxes):
        out = {}
        for crsid, crsdef in self.published_CRSs.items():
            a_crsid = crsdef["alias_of"]
            if a_crsid:
                if a_crsid in bboxes:
                    out[crsid] = bboxes[a_crsid]
            else:
                if crsid in bboxes:
                    out[crsid] = bboxes[crsid]
        return out

    def crs(self, crsid):
        if crsid not in self.published_CRSs:
            raise ConfigException(f"CRS {crsid} is not published")
        crs_def = self.published_CRSs[crsid]
        crs_alias = crs_def["alias_of"]
        if crs_alias:
            use_crs = crs_alias
        else:
            use_crs = crsid
        return geometry.CRS(use_crs)

    def response_headers(self, d):
        hdrs = self._response_headers.copy()
        hdrs.update(d)
        return hdrs


def get_config(refresh=False, called_from_update_ranges=False):
    cfg = OWSConfig(refresh=refresh, called_from_update_ranges=called_from_update_ranges)
    if not cfg.ready:
        try:
            with cube() as dc:
                cfg.make_ready(dc)
        except ODCInitException:
            pass
    return cfg
