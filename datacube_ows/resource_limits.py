from datacube_ows.config_utils import OWSConfigEntry
from datacube_ows.ogc_utils import ConfigException


class CacheControlRules(OWSConfigEntry):
    def __init__(self, cfg, context, max_datasets):
        super().__init__(cfg)
        self.rules = cfg
        self.use_caching = self.rules is not None
        self.max_datasets = max_datasets
        if not self.use_caching:
            return
        min_so_far = 0
        max_max_age_so_far = 0
        for rule in self.rules:
            if "min_datasets" not in rule:
                raise ConfigException(f"Dataset cache rule does not contain a 'min_datasets' element in {context}")
            if "max_age" not in rule:
                raise ConfigException(f"Dataset cache rule does not contain a 'max_age' element in {context}")
            min_datasets = rule["min_datasets"]
            max_age = rule["max_age"]
            if not isinstance(min_datasets, int):
                raise ConfigException(f"Dataset cache rule has non-integer 'min_datasets' element in {context}")
            if not isinstance(max_age, int):
                raise ConfigException(f"Dataset cache rule has non-integer 'max_age' element in {context}")
            if min_datasets <= 0:
                raise ConfigException(f"Invalid dataset cache rule in {context}: min_datasets must be greater than zero.")
            if min_datasets <= min_so_far:
                raise ConfigException(f"Dataset cache rules must be sorted by ascending min_datasets values.  In layer {context}.")
            if max_datasets > 0 and min_datasets > max_datasets:
                raise ConfigException(f"Dataset cache rule min_datasets value exceeds the max_datasets limit in layer {context}.")
            min_so_far = min_datasets
            if max_age <= 0:
                raise ConfigException(f"Dataset cache rule max_age value must be greater than zero in layer {context}.")
            if max_age <= max_max_age_so_far:
                raise ConfigException(f"max_age values in dataset cache rules must increase monotonically in layer {context}.")
            max_max_age_so_far = max_age

    def cache_headers(self, n_datasets):
        if not self.use_caching:
            return {}
        assert n_datasets >= 0
        if n_datasets == 0 or n_datasets > self.max_datasets:
            return {"cache-control": "no-cache"}
        rule = None
        for r in self.rules:
            if n_datasets < r["min_datasets"]:
                break
            rule = r
        if rule:
            return {"cache-control": f"max-age={rule['max_age']}"}
        else:
            return {"cache-control": "no-cache"}


class OWSResourceManagementRules(OWSConfigEntry):
    # pylint: disable=attribute-defined-outside-init
    def __init__(self, cfg, context):
        super().__init__(cfg)
        cfg = self._raw_cfg
        wms_cfg = cfg.get("wms", {})
        wcs_cfg = cfg.get("wcs", {})
        self.zoom_fill = wms_cfg.get("zoomed_out_fill_colour", [150, 180, 200, 160])
        if len(self.zoom_fill) == 3:
            self.zoom_fill += [255]
        if len(self.zoom_fill) != 4:
            raise ConfigException(f"zoomed_out_fill_colour must have 3 or 4 elements in {context}")
        self.min_zoom = wms_cfg.get("min_zoom_factor", 300.0)
        self.max_datasets_wms = wms_cfg.get("max_datasets", 0)
        self.max_datasets_wcs = wcs_cfg.get("max_datasets", 0)
        self.wms_cache_rules = CacheControlRules(wms_cfg.get("dataset_cache_rules"), context, self.max_datasets_wms)
        self.wcs_cache_rules = CacheControlRules(wcs_cfg.get("dataset_cache_rules"), context, self.max_datasets_wcs)