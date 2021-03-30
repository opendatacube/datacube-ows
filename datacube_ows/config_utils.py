import json
import os
from importlib import import_module
from typing import Mapping, Sequence

from datacube_ows.config_toolkit import deepinherit
from datacube_ows.ogc_utils import ConfigException, FunctionWrapper


# pylint: disable=dangerous-default-value
def cfg_expand(cfg_unexpanded, cwd=None, inclusions=[]):
    # inclusions defaulting to an empty list is dangerous, but note that it is never modified.
    # If modification of inclusions is a required, a copy (ninclusions) is made and modified instead.
    if cwd is None:
        cwd = os.getcwd()
    if isinstance(cfg_unexpanded, Mapping):
        if "include" in cfg_unexpanded:
            if cfg_unexpanded["include"] in inclusions:
                raise ConfigException("Cyclic inclusion: %s" % cfg_unexpanded["include"])
            ninclusions = inclusions.copy()
            ninclusions.append(cfg_unexpanded["include"])
            # Perform expansion
            if "type" not in cfg_unexpanded or cfg_unexpanded["type"] == "json":
                # JSON Expansion
                raw_path = cfg_unexpanded["include"]
                try:
                    # Try in actual working directory
                    json_obj = load_json_obj(raw_path)
                    abs_path = os.path.abspath(cfg_unexpanded["include"])
                    cwd = os.path.dirname(abs_path)
                # pylint: disable=broad-except
                except Exception:
                    json_obj = None
                if json_obj is None:
                    path = os.path.join(cwd, raw_path)
                    try:
                        # Try in inherited working directory
                        json_obj = load_json_obj(path)
                        abs_path = os.path.abspath(path)
                        cwd = os.path.dirname(abs_path)
                    # pylint: disable=broad-except
                    except Exception:
                        json_obj = None
                if json_obj is None:
                    raise ConfigException("Could not find json file %s" % raw_path)
                return cfg_expand(load_json_obj(abs_path), cwd=cwd, inclusions=ninclusions)
            elif cfg_unexpanded["type"] == "python":
                # Python Expansion
                return cfg_expand(import_python_obj(cfg_unexpanded["include"]), cwd=cwd, inclusions=ninclusions)
            else:
                raise ConfigException("Unsupported inclusion type: %s" % str(cfg_unexpanded["type"]))
        else:
            return {k: cfg_expand(v, cwd=cwd, inclusions=inclusions) for k,v in cfg_unexpanded.items()}
    elif isinstance(cfg_unexpanded, Sequence) and not isinstance(cfg_unexpanded, str):
        return list([cfg_expand(elem, cwd=cwd, inclusions=inclusions) for elem in cfg_unexpanded])
    else:
        return cfg_unexpanded


def load_json_obj(path):
    with open(path) as json_file:
        return json.load(json_file)


def import_python_obj(path):
    """Imports a python dictionary by fully-qualified path

    :return: a Callable object, or None
    """
    mod_name, obj_name = path.rsplit('.', 1)
    mod = import_module(mod_name)
    obj = getattr(mod, obj_name)
    return obj


class OWSConfigNotReady(ConfigException):
    pass


# Base classes for configuration objects
class OWSConfigEntry:
    # Parse and validate the json but don't access the database.
    def __init__(self, cfg, *args, **kwargs):
        self._unready_attributes = set()
        self._raw_cfg = cfg
        self.ready = False

    def declare_unready(self, name):
        if self.ready:
            raise ConfigException(f"Cannot declare {name} as unready on a ready object")
        self._unready_attributes.add(name)

    def __getattribute__(self, name):
        if name == "_unready_attributes":
            pass
        elif hasattr(self, "_unready_attributes") and name in self._unready_attributes:
            raise OWSConfigNotReady(f"The following parameters have not been initialised: {self._unready_attributes}")
        return object.__getattribute__(self, name)

    def __setattr__(self, name, val):
        if name == "_unready_attributes":
            pass
        elif hasattr(self, "_unready_attributes") and name in self._unready_attributes:
            self._unready_attributes.remove(name)
        super().__setattr__(name, val)

    # Validate against database and prepare for use.
    def make_ready(self, dc, *args, **kwargs):
        if self._unready_attributes:
            raise OWSConfigNotReady(f"The following parameters have not been initialised: {self._unready_attributes}")
        self.ready = True


class OWSEntryNotFound(ConfigException):
    pass


class OWSIndexedConfigEntry(OWSConfigEntry):
    INDEX_KEYS = []

    def __init__(self, cfg, keyvals, *args, **kwargs):
        super().__init__(cfg, *args, **kwargs)

        for k in self.INDEX_KEYS:
            if k not in keyvals:
                raise ConfigException(f"Key value {k} missing from keyvals: {keyvals!r}")
        self.keyvals = keyvals

    def lookup(self, cfg, keyvals, subs=None):
        if subs is None:
            subs = {}
        for k in self.INDEX_KEYS:
            if k not in keyvals:
                raise ConfigException(f"Key value {k} missing from keyvals: {keyvals!r}")
        return self.lookup_impl(cfg, keyvals, subs)

    @classmethod
    def lookup_impl(cls, cfg, keyvals, subs=None):
        raise NotImplementedError()


# pylint: disable=abstract-method
class OWSExtensibleConfigEntry(OWSIndexedConfigEntry):
    def __init__(self, cfg, keyvals, global_cfg, *args,
                 keyval_subs=None, keyval_defaults=None, expanded=False, **kwargs):
        if not expanded:
            cfg = self.expand_inherit(cfg, global_cfg,
                                      keyval_subs=keyval_subs, keyval_defaults=keyval_defaults)

        super().__init__(cfg, keyvals, global_cfg=global_cfg, *args, **kwargs)

    @classmethod
    def expand_inherit(cls, cfg, global_cfg, keyval_subs=None, keyval_defaults=None):
        if "inherits" in cfg:
            lookup = True
            # Precludes e.g. defaulting style lookup to current layer.
            lookup_keys = {}
            for k in cls.INDEX_KEYS:
                if k not in cfg["inherits"] and k not in keyval_defaults:
                    lookup = False
                    break
                if k in cfg["inherits"]:
                    lookup_keys[k] = cfg["inherits"][k]
                else:
                    lookup_keys[k] = keyval_defaults[k]
            if lookup:
                parent = cls.lookup_impl(global_cfg, keyvals=lookup_keys, subs=keyval_subs)
                # pylint: disable=protected-access
                parent_cfg = parent._raw_cfg
            else:
                parent_cfg = cfg["inherits"]
            cfg = deepinherit(parent_cfg, cfg)
            cfg["inheritance_expanded"] = True
        return cfg


class OWSFlagBandStandalone:
    def __init__(self, band):
        self.pq_band = band


class OWSFlagBand(OWSConfigEntry):
    def __init__(self, cfg, product_cfg, **kwargs):
        super().__init__(cfg, **kwargs)
        cfg = self._raw_cfg
        self.product = product_cfg
        pq_names = self.product.parse_pq_names(cfg)
        self.pq_names = pq_names["pq_names"]
        self.pq_low_res_names = pq_names["pq_low_res_names"]
        self.pq_band = cfg["band"]
        if "fuse_func" in cfg:
            self.pq_fuse_func = FunctionWrapper(self, cfg["fuse_func"])
        else:
            self.pq_fuse_func = None
        self.pq_ignore_time = cfg.get("ignore_time", False)
        self.ignore_info_flags = cfg.get("ignore_info_flags", [])
        self.pq_manual_merge = cfg.get("manual_merge", False)
        self.declare_unready("pq_products")
        self.declare_unready("flags_def")
        self.declare_unready("info_mask")

    # pylint: disable=attribute-defined-outside-init
    def make_ready(self, dc, *args, **kwargs):
        self.pq_products = []
        self.pq_low_res_products = []
        for pqn in self.pq_names:
            if pqn is not None:
                pq_product = dc.index.products.get_by_name(pqn)
                if pq_product is None:
                    raise ConfigException(f"Could not find flags product {pqn} for layer {self.product.name} in datacube")
                self.pq_products.append(pq_product)
        for pqn in self.pq_low_res_names:
            if pqn is not None:
                pq_product = dc.index.products.get_by_name(pqn)
                if pq_product is None:
                    raise ConfigException(f"Could not find flags low_res product {pqn} for layer {self.product.name} in datacube")
                self.pq_low_res_products.append(pq_product)

        self.info_mask = ~0
        # A (hopefully) representative product
        product = self.pq_products[0]
        meas = product.lookup_measurements([self.pq_band])
        self.flags_def = meas[self.pq_band]["flags_definition"]
        for bitname in self.ignore_info_flags:
            bit = self.flags_def[bitname]["bits"]
            if not isinstance(bit, int):
                continue
            flag = 1 << bit
            self.info_mask &= ~flag
        super().make_ready(dc)


class FlagProductBands(OWSConfigEntry):
    def __init__(self, flag_band):
        super().__init__({})
        self.bands = set()
        self.bands.add(flag_band.pq_band)
        self.flag_bands = {flag_band.pq_band: flag_band}
        self.product_names = tuple(flag_band.pq_names)
        self.ignore_time = flag_band.pq_ignore_time
        self.declare_unready("products")
        self.declare_unready("low_res_products")
        self.manual_merge = flag_band.pq_manual_merge
        self.fuse_func = flag_band.pq_fuse_func

    def products_match(self, product_names):
        return tuple(product_names) == self.product_names

    def add_flag_band(self, fb):
        self.flag_bands[fb.pq_band] = fb
        self.bands.add(fb.pq_band)
        if fb.pq_manual_merge:
            fb.pq_manual_merge = True
        if fb.pq_fuse_func and self.fuse_func and fb.pq_fuse_func != self.fuse_func:
            raise ConfigException(f"Fuse functions for flag bands in product set {self.product_names} do not match")
        if fb.pq_ignore_time != self.ignore_time:
            raise ConfigException(f"ignore_time option for flag bands in product set {self.product_names} do not match")
        elif fb.pq_fuse_func and not self.fuse_func:
            self.fuse_func = fb.pq_fuse_func
        self.declare_unready("products")
        self.declare_unready("low_res_products")

    # pylint: disable=attribute-defined-outside-init
    def make_ready(self, dc, *args, **kwargs):
        for fb in self.flag_bands.values():
            self.products = fb.pq_products
            self.low_res_products = fb.pq_low_res_products
            break
        super().make_ready(dc, *args, **kwargs)

    @classmethod
    def build_list_from_masks(cls, masks):
        flag_products = []
        for mask in masks:
            handled = False
            for fp in flag_products:
                if fp.products_match(mask.band.pq_names):
                    fp.add_flag_band(mask.band)
                    handled = True
                    break
            if not handled:
                flag_products.append(cls(mask.band))
        return flag_products

    @classmethod
    def build_list_from_flagbands(cls, flagbands):
        flag_products = []
        for fb in flagbands:
            handled = False
            for fp in flag_products:
                if fp.products_match(fb.pq_names):
                    fp.add_flag_band(fb)
                handled = True
                break
            if not handled:
                flag_products.append(cls(fb))
        return flag_products
