import math
from typing import Any, Iterable, List, Mapping, Optional, Tuple, Union, cast

import affine
import numpy as np
from datacube.utils.geometry import CRS, GeoBox, polygon

from datacube_ows.config_utils import CFG_DICT, RAW_CFG, OWSConfigEntry
from datacube_ows.ogc_utils import (ConfigException, cache_control_headers,
                                    create_geobox)


def parse_cache_age(cfg, entry, section, default=0):
    try:
        val = int(cfg.get(entry, default))
    except ValueError:
        raise ConfigException(
            f"{entry} in {section} section must be an integer: {cfg[entry]}"
        )
    if val < 0:
        raise ConfigException(
            f"{entry} in {section} section cannot be negative: {cfg[entry]}"
        )
    return val


# pyre-ignore[13]
class RequestScale:
    standard_scale: "RequestScale"

    def __init__(self,
                 native_crs: CRS,
                 native_resolution: Tuple[Union[float, int], Union[float, int]],
                 geobox: GeoBox,
                 n_dates: int,
                 request_bands: Optional[Iterable[Mapping[str, Any]]] = None,
                 total_band_size: Optional[int] = None) -> None:
        self.resolution = self._metre_resolution(native_crs, native_resolution)
        self.crs = native_crs
        self.geobox = self._standardise_geobox(geobox)
        self.pixel_size = (geobox.width, geobox.height)
        self.n_dates = n_dates
        self.bands = request_bands
        assert (request_bands is not None) ^ (total_band_size is not None)
        if total_band_size is not None:
            self.total_band_size: int = total_band_size
        else:
            self.total_band_size = sum(
                np.dtype(band['dtype']).itemsize
                for band in cast(Iterable[Mapping[str, Any]], request_bands)
            )

    def _standardise_geobox(self, geobox: GeoBox) -> GeoBox:
        if geobox.crs == 'EPSG:3857':
            return geobox
        bbox = geobox.extent.to_crs('EPSG:3857').boundingbox
        return create_geobox(CRS('EPSG:3857'),
                             bbox.left, bbox.bottom,
                             bbox.right, bbox.top,
                             width=geobox.width, height=geobox.height
                             )

    def _metre_resolution(self, crs: CRS, resolution: Tuple[Union[float, int], Union[float, int]]) \
            -> Tuple[float, float]:
        # Convert native resolution to metres for ready comparison.
        if crs.units == ('metre', 'metre'):
            return cast(Tuple[float, float], tuple(abs(r) for r in resolution))
        resolution_rectangle = polygon(
                            ((0, 0), (0, resolution[1]), resolution, (0, resolution[0]), (0, 0)),
                            crs=crs)
        proj_bbox = resolution_rectangle.to_crs("EPSG:3857").boundingbox
        return (
            abs(proj_bbox.right - proj_bbox.left),
            abs(proj_bbox.top - proj_bbox.bottom),
        )

    def pixel_span(self) -> Tuple[float, float]:
        bbox = self.geobox.extent.boundingbox
        return (
            (bbox.right - bbox.left) / self.geobox.width,
            (bbox.bottom - bbox.top) / self.geobox.height
        )

    @property
    def scale_denominator(self) -> float:
        xy_denoms = [
            abs(ps / 0.00028)
            for ps in self.pixel_span()
        ]
        return sum(xy_denoms) / 2.0

    @property
    def base_zoom_level(self) -> float:
        return math.log(559082264.0287178 / self.scale_denominator, 2)

    @property
    def load_adjusted_zoom_level(self) -> float:
        return self.base_zoom_level - self.zoom_lvl_offset

    def res_xy(self) -> Union[int, float]:
        return self.resolution[0] * self.resolution[1]

    def __truediv__(self, other: "RequestScale") -> float:
        ratio = 1.0
        ratio = ratio * self.n_dates / other.n_dates
        for i in range(2):
            ratio = ratio * self.pixel_size[i] / other.pixel_size[i]
        ratio = ratio * self.total_band_size / other.total_band_size
        ratio = ratio * other.res_xy() / self.res_xy()
        return ratio

    @property
    def load_factor(self) -> float:
        return self / self.standard_scale

    @property
    def zoom_lvl_offset(self) -> float:
        return math.log(self.load_factor, 4)


RequestScale.standard_scale = RequestScale(CRS("EPSG:3857"), (25.0, 25.0),
                                           GeoBox(width=256, height=256, affine=affine.identity, crs="EPSG:3857"),
                                           1, total_band_size=(3 * 2))



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
            return cache_control_headers(0)
        rule = None
        for r in self.rules:
            if n_datasets < r["min_datasets"]:
                break
            rule = r
        if rule:
            return cache_control_headers(rule['max_age'])
        else:
            return cache_control_headers(0)


class ResourceLimited(Exception):
    def __init__(self, reasons: List[str], wcs_hard=False):
        self.reasons = reasons
        self.wcs_hard = wcs_hard
        super().__init__(f"Resource limit(s) exceeded: {','.join(reasons)}")


class OWSResourceManagementRules(OWSConfigEntry):
    # pylint: disable=attribute-defined-outside-init
    def __init__(self,
                 global_cfg: "datacube_ows.ows_configuration.OWSConfig",
                 cfg: CFG_DICT,
                 context: str
                 ) -> None:
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
        self.min_zoom = cast(Optional[float], wms_cfg.get("min_zoom_factor"))
        self.min_zoom_lvl = cast(Optional[Union[int, float]], wms_cfg.get("min_zoom_level"))
        self.max_datasets_wms = cast(int, wms_cfg.get("max_datasets", 0))
        self.max_datasets_wcs = cast(int, wcs_cfg.get("max_datasets", 0))
        self.max_image_size_wcs = cast(int, wcs_cfg.get("max_image_size", 0))
        self.wms_cache_rules = CacheControlRules(wms_cfg.get("dataset_cache_rules"), context, self.max_datasets_wms)
        self.wcs_cache_rules = CacheControlRules(wcs_cfg.get("dataset_cache_rules"), context, self.max_datasets_wcs)
        self.wcs_desc_cache_rule = parse_cache_age(
            cfg,
            "describe_cache_max_age",
            f"resource_limits for {context}",
            default=global_cfg.wcs_default_descov_age
        )

    def check_wms(self, n_datasets: int, zoom_factor: float, request_scale: RequestScale) -> None:
        """
        Check whether a WMS requests exceeds the configured resource limits.

        :param n_datasets: The number of datasets for the query
        :param zoom_factor: The zoom factor of the query
        :param request_scale: Model of the resource-intensiveness of the query
        :raises: ResourceLimited if any limits are exceeded.
        """
        limits_exceeded: List[str] = []
        if self.max_datasets_wms > 0 and n_datasets > self.max_datasets_wms:
            limits_exceeded.append("too many datasets")
        if self.min_zoom is not None:
            if zoom_factor < self.min_zoom:
                limits_exceeded.append("zoomed out too far")
        if self.min_zoom_lvl is not None:
            fuzz_factor = 0.01
            if request_scale.load_adjusted_zoom_level < self.min_zoom_lvl - fuzz_factor:
                limits_exceeded.append("too much projected resource requirements")
        if limits_exceeded:
            raise ResourceLimited(limits_exceeded)

    def check_wcs(self, n_datasets: int,
                  height: int, width: int,
                  pixel_size: int,
                  n_dates: int
                 ) -> None:
        """
        Check whether a WCS requests exceeds the configured resource limits.

        :param n_datasets: The number of datasets for the query
        :raises: ResourceLimited if any limits are exceeded.
        """
        limits_exceeded: List[str] = []
        hard = False
        if self.max_datasets_wcs > 0 and n_datasets > self.max_datasets_wcs:
            limits_exceeded.append(f"too many datasets ({n_datasets}: maximum={self.max_datasets_wcs}")
        pixel_count = height * width
        if self.max_image_size_wcs > 0 and n_dates * pixel_count * pixel_size > self.max_image_size_wcs:
            limits_exceeded.append(f"too much data for a single request - try selecting fewer pixels or less bands")
            hard = True
        if limits_exceeded:
            raise ResourceLimited(limits_exceeded, wcs_hard=hard)
