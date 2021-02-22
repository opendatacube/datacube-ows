from datacube.utils.masking import make_mask

from datacube_ows.ows_configuration import OWSConfigEntry, OWSExtensibleConfigEntry, OWSEntryNotFound
from datacube_ows.ogc_utils import ConfigException, FunctionWrapper

import logging

_LOG = logging.getLogger(__name__)


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


class StyleDefBase(OWSExtensibleConfigEntry):
    INDEX_KEYS = ["layer", "style"]
    auto_legend = False
    include_in_feature_info = False

    def __new__(cls, product=None, style_cfg=None, defer_multi_date=False):
        if product and style_cfg:
            style_cfg = cls.expand_inherit(style_cfg, global_cfg=product.global_cfg,

                               keyval_subs={
                                   "layer": {
                                       product.name: product
                                   }
                               },
                               keyval_defaults={"layer": product.name})
            subclass = cls.determine_subclass(style_cfg)
            if not subclass:
                raise ConfigException(f"Invalid style in layer {product.name} - could not determine style type")
            return super().__new__(subclass)
        return super().__new__(cls)

    def __init__(self, product, style_cfg, defer_multi_date=False):
        super().__init__(style_cfg,
                         global_cfg=product.global_cfg,
                         keyvals={
                                "layer": product.name,
                                "style": style_cfg["name"]
                         },
                         keyval_subs={
                             "layer": {
                                 product.name: product
                             }
                         },
                         keyval_defaults={
                             "layer": product.name
                         })
        style_cfg = self._raw_cfg
        self.local_band_map = style_cfg.get("band_map", {})
        self.product = product
        self.name = style_cfg["name"]
        self.title = style_cfg["title"]
        self.abstract = style_cfg["abstract"]
        self.masks = [StyleMask(mask_cfg, self) for mask_cfg in style_cfg.get("pq_masks", [])]
        self.flag_products = []
        for mask in self.masks:
            handled = False
            for fp in self.flag_products:
                if fp.products_match(mask.band.pq_names):
                    fp.add_flag_band(mask.band)
                    handled = True
                    break
            if not handled:
                self.flag_products.append(FlagProductBands(mask.band))

        self.raw_needed_bands = set()
        self.declare_unready("needed_bands")
        self.declare_unready("flag_bands")

        self.parse_legend_cfg(style_cfg.get("legend", {}))
        if not defer_multi_date:
            self.parse_multi_date(style_cfg)

    # pylint: disable=attribute-defined-outside-init
    def make_ready(self, dc, *args, **kwargs):
        self.needed_bands = set()
        self.pq_product_bands = []
        for band in self.raw_needed_bands:
            self.needed_bands.add(self.local_band(band))
        for mask in self.masks:
            fb = mask.band
            if fb.pq_names == self.product.product_names:
                self.needed_bands.add(fb.band)
                continue
            handled=False
            for pqp, pqb in self.pq_product_bands:
                if fb.pq_names == pqp:
                    pqb.add(fb.pq_band)
                    handled=True
                    continue
            if not handled:
                self.pq_product_bands.append(
                    (fb.pq_names, set([fb.pq_band]))
                )
        self.flag_bands = set()
        for pq_names, pq_bands in self.pq_product_bands:
            for band in pq_bands:
                if band in self.flag_bands:
                    raise ConfigException(f"Same flag band name {band} appears in different PQ product (sets)")
                self.flag_bands.add(band)
        for fp in self.flag_products:
            fp.make_ready(dc)
        for band in self.product.always_fetch_bands:
            self.needed_bands.add(band)
            self.flag_bands.add(band)
        super().make_ready(dc, *args, **kwargs)

    def local_band(self, band):
        if band in self.local_band_map:
            band = self.local_band_map[band]
        return self.product.band_idx.band(band)

    def parse_multi_date(self, cfg):
        self.multi_date_handlers = []
        for mb_cfg in cfg.get("multi_date", []):
            self.multi_date_handlers.append(self.MultiDateHandler(self, mb_cfg))

    def to_mask(self, data, extra_mask=None):
        def single_date_make_mask(data, mask):
            pq_data = getattr(data, mask.band_name)
            if mask.flags:
                odc_mask = make_mask(pq_data, **mask.flags)
            else:
                odc_mask = pq_data == mask.enum
            odc_mask = odc_mask.squeeze(dim="time", drop=True)
            return odc_mask

        date_count = len(data.coords["time"])
        if date_count > 1:
            # TODO multidate
            mdh = self.get_multi_date_handler(date_count)
            if extra_mask is not None:
                extra_mask = mdh.collapse_mask(extra_mask)
            mask_maker = mdh.make_mask
        else:
            if extra_mask is not None:
                extra_mask = extra_mask.squeeze(dim="time", drop=True)
            mask_maker=single_date_make_mask

        result = extra_mask
        for mask in self.masks:
            mask_data = mask_maker(data, mask)
            if mask.invert:
                mask_data = ~mask_data
            if result is None:
                result = mask_data
            else:
                result = result & mask_data
        return result

    def apply_mask(self, data, mask):
        if mask is not None:
            for band in data.data_vars:
                data[band] = data[band].where(mask)
        return data

    def transform_data(self, data, mask):
        date_count = len(data.coords["time"])
        if mask is not None:
            data = self.apply_mask(data, mask)
        if date_count == 1:
            return self.transform_single_date_data(data.squeeze(dim="time", drop=True))
        mdh = self.get_multi_date_handler(date_count)
        return mdh.transform_data(data)

    def transform_single_date_data(self, data):
        raise NotImplementedError()

    # pylint: disable=attribute-defined-outside-init
    def parse_legend_cfg(self, cfg):
        self.show_legend = cfg.get("show_legend", self.auto_legend)
        self.legend_url_override = cfg.get('url', None)
        self.legend_cfg = cfg

    def single_date_legend(self, bytesio):
        raise NotImplementedError()

    def legend_override_with_url(self):
        return self.legend_url_override

    def get_multi_date_handler(self, count):
        for mdh in self.multi_date_handlers:
            if mdh.applies_to(count):
                return mdh
        return None

    @classmethod
    def register_subclass(cls, subclass, triggers, priority=False):
        if isinstance(triggers, str):
            triggers = [triggers]
        if priority:
            style_class_priority_reg.append([subclass, triggers])
        else:
            style_class_reg.append([subclass, triggers])

    @classmethod
    def determine_subclass(cls, cfg):
        for sub, triggers in style_class_priority_reg + style_class_reg:
            for trig in triggers:
                if trig in cfg:
                    return sub
        return None

    class MultiDateHandler(OWSConfigEntry):
        auto_legend = False
        def __init__(self, style, cfg):
            super().__init__(cfg)
            cfg = self._raw_cfg
            self.style = style
            if "allowed_count_range" not in cfg:
                raise ConfigException("multi_date handler must have an allowed_count_range")
            if len(cfg["allowed_count_range"]) > 2:
                raise ConfigException("multi_date handler allowed_count_range must have 2 and only 2 members")
            self.min_count, self.max_count = cfg["allowed_count_range"]
            if self.max_count < self.min_count:
                raise ConfigException("multi_date handler allowed_count_range: minimum must be less than equal to maximum")
            if "aggregator_function" in cfg:
                self.aggregator = FunctionWrapper(style.product, cfg["aggregator_function"])
            else:
                raise ConfigException("Aggregator function is required for multi-date handlers.")
            self.parse_legend_cfg(cfg.get("legend", {}))

        def applies_to(self, count):
            return (self.min_count <= count and self.max_count >= count)

        def __repr__(self):
            if self.min_count == self.max_count:
                return str(self.min_count)
            return f"{self.min_count}-{self.max_count}"

        def range_str(self):
            return self.__repr__()

        def transform_data(self, data):
            raise NotImplementedError()

        def make_mask(self, data, mask):
            odc_mask = None
            for dt in data.coords["time"].values:
                tpqdata = getattr(data.sel(time=dt), mask.band_name)
                if odc_mask is None:
                    odc_mask = make_mask(tpqdata, **mask.flags)
                else:
                    odc_mask |= make_mask(tpqdata, **mask.flags)
            return odc_mask

        # pylint: disable=attribute-defined-outside-init
        def parse_legend_cfg(self, cfg):
            self.show_legend = cfg.get("show_legend", self.auto_legend)
            self.legend_url_override = cfg.get('url', None)
            self.legend_cfg = cfg

        def legend(self, bytesio):
            return False

        # Defaults to an "AND" over time - data only where all dates have data.
        # Override for "OR" functionality.
        def collapse_mask(self, mask):
            collapsed = None
            for dt in mask.coords["time"].values:
                m = mask.sel(time=dt)
                if collapsed is None:
                    collapsed = m
                else:
                    collapsed = collapsed & m
            return collapsed

    def lookup(self, cfg, keyvals, subs=None):
        if subs is None:
            subs = {}
        if "layer" not in keyvals and "layer" not in subs:
            keyvals["layer"] = self.product.name
        return super().lookup(cfg, keyvals, subs)

    @classmethod
    def lookup_impl(cls, cfg, keyvals, subs=None):
        if subs is None:
            subs = {}
        prod = None
        if "layer" in subs:
            prod = subs["layer"].get(keyvals["layer"])
        if not prod:
            try:
                prod = cfg.product_index[keyvals["layer"]]
            except KeyError:
                raise OWSEntryNotFound(f"No layer named {keyvals['layer']}")

        try:
            return prod.style_index[keyvals['style']]
        except KeyError:
            raise OWSEntryNotFound(f"No style named {keyvals['style']} in layer {keyvals['layer']}")


style_class_priority_reg = []
style_class_reg = []

class StyleMask(OWSConfigEntry):
    def __init__(self, cfg, style):
        super().__init__(cfg)
        cfg = self._raw_cfg
        self.style = style
        if not self.style.product.flag_bands:
            raise ConfigException(f"Style {self.style.name} in layer {self.style.product.name} contains a mask, but the layer has no flag bands")
        if "band" in cfg:
            self.band_name = cfg["band"]
            if self.band_name not in self.style.product.flag_bands:
                raise ConfigException(
                    f"Style {self.style.name} has a mask that references flag band {self.band_name} which is not defined for the layer")
        else:
            self.band_name = list(self.style.product.flag_bands.keys())[0]
            _LOG.warning("Style %s in layer %s uses a deprecated pq_masks format. Refer to the documentation for the new format",
                         self.style.name,
                         self.style.product.name)
        if self.band_name not in self.style.product.flag_bands:
            raise ConfigException(f"Style {self.style.name} has a mask that references flag band {self.band_name} which is not defined for the layer")
        self.band = self.style.product.flag_bands[self.band_name]
        self.invert = cfg.get("invert", False)
        if "flags" in cfg:
            self.flags = cfg["flags"]
            self.enum = None
            if "enum" in cfg:
                raise ConfigException(
                    f"mask definition in layer {self.style.product.name}, style {self.style.name} has both an enum section and a flags section - please split into two masks.")
            if len(self.flags) == 0:
                raise ConfigException(
                    f"mask definition in layer {self.style.product.name}, style {self.style.name} has empty enum section.")
        elif "enum" in cfg:
            self.enum = cfg["enum"]
            self.flags = None
        else:
            raise ConfigException(f"mask definition in layer {self.style.product.name}, style {self.style.name} has no flags or enum section - nothing to mask on.")