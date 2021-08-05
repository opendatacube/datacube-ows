from typing import List, Mapping, Optional, cast

from datacube_ows.config_utils import CFG_DICT, RAW_CFG, OWSConfigEntry
from datacube_ows.ogc_utils import ConfigException


class CacheControlRules(OWSConfigEntry):
    def __init__(self, cfg: RAW_CFG, context: str, max_datasets: int) -> None:
        """
        Class constructor. stores and validates rule dictionaries

        :param cfg: None, or a list of progressive CCR configurations.
        :param context: Context label (e.g. owning layer name), used for reporting validation errors
        :param max_datasets: Over-arching maximum dataset limit in context.
        """
        super().__init__(cfg)
        self.rules = cast(Optional[List[CFG_DICT]], self._raw_cfg)
        self.use_caching: bool = self.rules is not None
        self.max_datasets = max_datasets
        if not self.use_caching:
            return

        # Validate rules
        min_so_far: int = 0
        max_max_age_so_far: int = 0
        for rule in cast(List[CFG_DICT], self.rules):
            if "min_datasets" not in rule:
                raise ConfigException(f"Dataset cache rule does not contain a 'min_datasets' element in {context}")
            if "max_age" not in rule:
                raise ConfigException(f"Dataset cache rule does not contain a 'max_age' element in {context}")
            if not isinstance(rule["min_datasets"], int):
                raise ConfigException(f"Dataset cache rule has non-integer 'min_datasets' element in {context}")
            min_datasets =  cast(int, rule["min_datasets"])
            if not isinstance(rule["max_age"], int):
                raise ConfigException(f"Dataset cache rule has non-integer 'max_age' element in {context}")
            max_age = cast(int, rule["max_age"])
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

    def cache_headers(self, n_datasets: int) -> Mapping[str, str]:
        """
        Generate Cache Control headers for a request accessing a number of datasets.

        :param n_datasets: number of datasets
        :return: Dictionary containing the appropriate HTTP cache control response headers.
        """
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


class ResourceLimited(Exception):
    def __init__(self, reasons: List[str]):
        self.reasons = reasons
        super().__init__(f"Resource limit(s) exceeded: {','.join(reasons)}")


class OWSResourceManagementRules(OWSConfigEntry):
    # pylint: disable=attribute-defined-outside-init
    def __init__(self, cfg: CFG_DICT, context: str) -> None:
        """
        Class constructor.

        :param cfg: A resource limit configuration dictionary.
        :param context: The context (e.g. layer name) for reporting validation errors.
        """
        super().__init__(cfg)
        cfg = cast(CFG_DICT, self._raw_cfg)
        wms_cfg = cast(CFG_DICT, cfg.get("wms", {}))
        wcs_cfg = cast(CFG_DICT, cfg.get("wcs", {}))
        self.zoom_fill = cast(List[int], wms_cfg.get("zoomed_out_fill_colour", [150, 180, 200, 160]))
        if len(self.zoom_fill) == 3:
            self.zoom_fill += [255]
        if len(self.zoom_fill) != 4:
            raise ConfigException(f"zoomed_out_fill_colour must have 3 or 4 elements in {context}")
        self.min_zoom = cast(float, wms_cfg.get("min_zoom_factor", 300.0))
        self.max_datasets_wms = cast(int, wms_cfg.get("max_datasets", 0))
        self.max_datasets_wcs = cast(int, wcs_cfg.get("max_datasets", 0))
        self.wms_cache_rules = CacheControlRules(wms_cfg.get("dataset_cache_rules"), context, self.max_datasets_wms)
        self.wcs_cache_rules = CacheControlRules(wcs_cfg.get("dataset_cache_rules"), context, self.max_datasets_wcs)

    def check_wms(self, n_datasets: int, zoom_factor: float) -> None:
        """
        Check whether a WMS requests exceeds the configured resource limits.

        :param n_datasets: The number of datasets for the query
        :param zoom_factor: The zoom factor of the query
        :raises: ResourceLimited if any limits are exceeded.
        """
        limits_exceeded: List[str] = []
        if self.max_datasets_wms > 0 and n_datasets > self.max_datasets_wms:
            limits_exceeded.append("too many datasets")
        if zoom_factor < self.min_zoom:
            limits_exceeded.append("zoomed out too far")
        if limits_exceeded:
            raise ResourceLimited(limits_exceeded)

    def check_wcs(self, n_datasets: int) -> None:
        """
        Check whether a WCS requests exceeds the configured resource limits.

        :param n_datasets: The number of datasets for the query
        :raises: ResourceLimited if any limits are exceeded.
        """
        limits_exceeded: List[str] = []
        if self.max_datasets_wcs > 0 and n_datasets > self.max_datasets_wcs:
            limits_exceeded.append("too many datasets")
        if limits_exceeded:
            raise ResourceLimited(limits_exceeded)
