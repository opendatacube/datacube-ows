from datacube.utils.masking import make_mask

from datacube_ows.ows_configuration import OWSConfigEntry, OWSExtensibleConfigEntry, OWSEntryNotFound
from datacube_ows.ogc_utils import ConfigException, FunctionWrapper


class StyleDefBase(OWSExtensibleConfigEntry):
    INDEX_KEYS = ["layer", "style"]
    auto_legend = False
    include_in_feature_info = False

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
                         })
        style_cfg = self._raw_cfg
        self.local_band_map = style_cfg.get("band_map", {})
        self.product = product
        self.name = style_cfg["name"]
        self.title = style_cfg["title"]
        self.abstract = style_cfg["abstract"]
        self.masks = [StyleMask(**mask_cfg) for mask_cfg in style_cfg.get("pq_masks", [])]
        self.needed_bands = set()
        for band in self.product.always_fetch_bands:
            self.needed_bands.add(self.local_band(band))

        if self.masks:
            for i, product_name in enumerate(product.product_names):
                if not self.product.pq_names or self.product.pq_names[i] == product_name:
                    self.needed_bands.add(self.product.pq_band)
                    break

        self.parse_legend_cfg(style_cfg.get("legend", {}))
        if not defer_multi_date:
            self.parse_multi_date(style_cfg)

    def local_band(self, band):
        if band in self.local_band_map:
            return self.local_band_map[band]
        return band

    def parse_multi_date(self, cfg):
        self.multi_date_handlers = []
        for mb_cfg in cfg.get("multi_date", []):
            self.multi_date_handlers.append(self.MultiDateHandler(self, mb_cfg))

    def apply_masks(self, data, pq_data):
        if pq_data is not None:
            net_mask = None
            for mask in self.masks:
                odc_mask = make_mask(pq_data, **mask.flags)
                mask_data = getattr(odc_mask, self.product.pq_band)
                if mask.invert:
                    mask_data = ~mask_data
                for band in data.data_vars:
                    data[band] = data[band].where(mask_data)
        return data

    def transform_data(self, data, pq_data, extent_mask, *masks):
        date_count = len(data.coords["time"])
        if date_count == 1:
            if pq_data is not None:
                pq_data = pq_data.squeeze(dim="time", drop=True)
            if extent_mask is not None:
                extent_mask = extent_mask.squeeze(dim="time", drop=True)
            return self.transform_single_date_data(data.squeeze(dim="time", drop=True),
                                                   pq_data,
                                                   extent_mask,
                                                   *masks)
        mdh = self.get_multi_date_handler(date_count)
        return mdh.transform_data(data, pq_data, extent_mask, *masks)

    def transform_single_date_data(self, data, pq_data, extent_mask, *masks):
        pass

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

        def range_str(self):
            if self.min_count == self.max_count:
                return str(self.min_count)
            return f"{self.min_count}-{self.max_count}"
        def transform_data(self, data, pq_data, extent_mask, *masks):
            raise NotImplementedError()

        def parse_legend_cfg(self, cfg):
            self.show_legend = cfg.get("show_legend", self.auto_legend)
            self.legend_url_override = cfg.get('url', None)
            self.legend_cfg = cfg

        def legend(self, bytesio):
            return False

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


class StyleMask(object):
    def __init__(self, flags, invert=False):
        self.flags = flags
        self.invert = invert