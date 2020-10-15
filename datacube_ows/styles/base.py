from datacube.utils.masking import make_mask

from datacube_ows.ows_configuration import OWSConfigEntry, OWSExtensibleConfigEntry, OWSEntryNotFound
from datacube_ows.ogc_utils import ConfigException, FunctionWrapper


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
        self.masks = [StyleMask(**mask_cfg) for mask_cfg in style_cfg.get("pq_masks", [])]
        self.raw_needed_bands = set()
        self.declare_unready("needed_bands")

        self.parse_legend_cfg(style_cfg.get("legend", {}))
        if not defer_multi_date:
            self.parse_multi_date(style_cfg)

    # pylint: disable=attribute-defined-outside-init
    def make_ready(self, dc, *args, **kwargs):
        self.needed_bands = set()
        for band in self.raw_needed_bands:
            self.needed_bands.add(self.local_band(band))
        for band in self.product.always_fetch_bands:
            self.needed_bands.add(band)
        if self.masks:
            for i, product_name in enumerate(self.product.product_names):
                if not self.product.pq_names or self.product.pq_names[i] == product_name:
                    self.needed_bands.add(self.product.pq_band)
                    break
        super().make_ready(dc, *args, **kwargs)

    def local_band(self, band):
        if band in self.local_band_map:
            return self.local_band_map[band]
        return band

    def parse_multi_date(self, cfg):
        self.multi_date_handlers = []
        for mb_cfg in cfg.get("multi_date", []):
            self.multi_date_handlers.append(self.MultiDateHandler(self, mb_cfg))

    def to_mask(self, data, pq_data, extra_mask=None):
        date_count = len(data.coords["time"])
        if date_count > 1:
            mdh = self.get_multi_date_handler(date_count)
            if extra_mask is not None:
                extra_mask = mdh.collapse_mask(extra_mask)
            if pq_data is not None:
                pq_data = mdh.collapse_mask(pq_data)
        else:
            if extra_mask is not None:
                extra_mask = extra_mask.squeeze(dim="time", drop=True)
            if pq_data is not None:
                pq_data = pq_data.squeeze(dim="time", drop=True)

        result = extra_mask
        if pq_data is not None:
            for mask in self.masks:
                odc_mask = make_mask(pq_data, **mask.flags)
                mask_data = getattr(odc_mask, self.product.pq_band)
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

class StyleMask(object):
    def __init__(self, flags, invert=False):
        self.flags = flags
        self.invert = invert