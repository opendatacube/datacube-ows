# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import io
import logging
from typing import (Any, Iterable, List, Mapping, MutableMapping, Optional,
                    Set, Sized, Tuple, Type, Union, cast)

import datacube.model
import numpy as np
import xarray as xr
from PIL import Image

import datacube_ows.band_utils
from datacube_ows.config_utils import (CFG_DICT, AbstractMaskRule, FlagBand,
                                       FlagProductBands, OWSConfigEntry,
                                       OWSEntryNotFound,
                                       OWSExtensibleConfigEntry,
                                       OWSFlagBandStandalone,
                                       OWSIndexedConfigEntry,
                                       OWSMetadataConfig)
from datacube_ows.legend_utils import get_image_from_url
from datacube_ows.ogc_exceptions import WMSException
from datacube_ows.ogc_utils import ConfigException, FunctionWrapper

_LOG: logging.Logger = logging.getLogger(__name__)


class StyleDefBase(OWSExtensibleConfigEntry, OWSMetadataConfig):
    """"
    Base Class from which all style classes are extended.

    The base class also holds a register of subclasses.  Instantiating the base
    class returns the appropriate subclass based on the supplied configuration.

    Style config entries can be extended with inheritance, and support Title and Abstract metadata
    """
    # For OWSExtensibleConfigEntry
    INDEX_KEYS = ["layer", "style"]

    # For OWSMetaDataConfig
    default_title = "Stand-Alone Style"
    default_abstract = "Stand-Alone Style"

    # Over-ridden by subclasses that support auto-legends
    auto_legend: bool = False
    # Used by Ramp subclass to expose index values to GetFeatureInfo
    include_in_feature_info: bool = False

    def __new__(cls, product: Optional["datacube_ows.ows_configuration.OWSNamedLayer"] = None,
                style_cfg: Optional[CFG_DICT] = None,
                stand_alone: bool = False,
                defer_multi_date: bool = False,
                user_defined: bool = False) -> "StyleDefBase":
        """"
        Determine appropriate subclass to instantiate and initialise.
        """
        if product and style_cfg:
            expanded_cfg = cast(CFG_DICT,
                                cls.expand_inherit(style_cfg,
                               global_cfg=product.global_cfg,
                               keyval_subs={
                                   "layer": {
                                       product.name: product
                                   }
                               },
                               keyval_defaults={"layer": product.name}))
            subclass = cls.determine_subclass(expanded_cfg)
            if not subclass:
                raise ConfigException(f"Invalid style in layer {product.name} - could not determine style type")
            return super().__new__(subclass)
        return super().__new__(cls)

    def __init__(self, product: "datacube_ows.ows_configuration.OWSNamedLayer",
                 style_cfg: CFG_DICT,
                 stand_alone: bool = False,
                 defer_multi_date: bool = False,
                 user_defined: bool = False) -> None:
        """
        Handle first stage initialisation of elements common to all style subclasses.

        :param product: A named layer
        :param style_cfg: The configuration of the style.
        :param stand_alone: If true, style is dynamically created independent from the global layer/style hierarchy.
        :param defer_multi_date: If True, defer certain aspects of configuration - mostly used for testing.
        :param user_defined: True if elements of the style were provided by the user in an extended request.
        """
        super().__init__(style_cfg,
                         global_cfg=product.global_cfg,
                         keyvals={
                                "layer": product.name,
                                "style": style_cfg.get("name", "stand_alone")
                         },
                         keyval_subs={
                             "layer": {
                                 product.name: product
                             }
                         },
                         keyval_defaults={
                             "layer": product.name
                         })
        raw_cfg = cast(CFG_DICT, self._raw_cfg)
        self.stand_alone: bool = stand_alone
        if self.stand_alone:
            self._metadata_registry: MutableMapping[str, str] = {}
        self.user_defined: bool = user_defined
        self.local_band_map = cast(MutableMapping[str, List[str]], raw_cfg.get("band_map", {}))
        self.product: "datacube_ows.ows_configuration.OWSNamedLayer" = product
        if self.stand_alone:
            self.name = cast(str, raw_cfg.get("name", "stand_alone"))
        else:
            self.name = cast(str, raw_cfg["name"])
        self.parse_metadata(raw_cfg)
        self.masks: List[StyleMask] = [
            StyleMask(mask_cfg, self)
            for mask_cfg in cast(List[CFG_DICT], raw_cfg.get("pq_masks", []))
        ]
        if self.stand_alone:
            self.flag_products: List[FlagProductBands] = []
        else:
            self.flag_products: List[FlagProductBands] = FlagProductBands.build_list_from_masks(self.masks,
                                                                                                self.product)

        self.raw_needed_bands: Set[str] = set()
        self.raw_flag_bands: Set[str] = set()
        self.declare_unready("needed_bands")
        self.declare_unready("flag_bands")

        self.parse_legend_cfg(cast(CFG_DICT, raw_cfg.get("legend", {})))
        if not defer_multi_date:
            self.parse_multi_date(raw_cfg)

    # Over-ridden methods
    def global_config(self) -> "datacube_ows.ows_configuration.OWSConfig":
        """"Global config object"""
        return self.product.global_cfg

    def get_obj_label(self) -> str:
        """Object label for metadata management"""
        return f"style.{self.product.name}.{self.name}"

    # pylint: disable=attribute-defined-outside-init
    def make_ready(self, dc: "datacube.Datacube", *args, **kwargs) -> None:
        """
        Second-phase (db aware) initialisation

        Mostly sorting out bands, esp flag bands.

        :param dc: A datacube object
        """
        # pyre-ignore[16]
        self.needed_bands: Set[str] = set()
        # pyre-ignore[16]
        self.pq_product_bands: List[FlagProductBands] = []
        # pyre-ignore[16]
        self.flag_bands: Set[str] = set()
        for band in self.raw_needed_bands:
            self.needed_bands.add(self.local_band(band))
        if not self.stand_alone:
            for mask in self.masks:
                fb = mask.flag_band
                # TODO: Should be able to remove this pyre-ignore after ows_configuration is typed.
                # pyre-ignore[16]
                if fb.pq_names == self.product.product_names:
                    self.needed_bands.add(self.local_band(fb.pq_band))
                    self.flag_bands.add(fb.pq_band)
                    continue
                handled = False
                for pqp, pqb in self.pq_product_bands:
                    if fb.pq_names == pqp:
                        pqb.add(fb.pq_band)
                        handled = True
                        continue
                if not handled:
                    self.pq_product_bands.append(
                        (fb.pq_names, set([fb.pq_band]))
                    )
        for pq_names, pq_bands in self.pq_product_bands:
            for band in pq_bands:
                if band in self.flag_bands:
                    raise ConfigException(f"Same flag band name {band} appears in different PQ product (sets)")
                self.flag_bands.add(band)
        for fp in self.flag_products:
            fp.make_ready(dc)
        if not self.stand_alone:
            # TODO: Should be able to remove this pyre-ignore after ows_configuration is typed.
            # pyre-ignore[16]
            for band in self.product.always_fetch_bands:
                if band not in self.needed_bands:
                    self.needed_bands.add(band)
                    self.flag_bands.add(band)
        super().make_ready(dc, *args, **kwargs)

    def odc_needed_bands(self) -> Iterable[datacube.model.Measurement]:
        # pyre-ignore[16]
        return [self.product.band_idx.native_bands.loc[b] for b in self.needed_bands]

    def local_band(self, band: str) -> str:
        """
        Local band alias handling.

        :param band: band name or alias
        :return: canonical band name
        """
        if self.stand_alone:
            return band
        if band in self.local_band_map:
            band = self.local_band_map[band]
        return self.product.band_idx.band(band)

    def parse_multi_date(self, cfg: CFG_DICT) -> None:
        """Used by __init__()"""
        self.multi_date_handlers: List["StyleDefBase.MultiDateHandler"] = []
        for mb_cfg in cast(List[CFG_DICT], cfg.get("multi_date", [])):
            self.multi_date_handlers.append(self.MultiDateHandler(self, mb_cfg))

    def to_mask(self, data: xr.Dataset, extra_mask: Optional[xr.DataArray] = None) -> Optional[xr.DataArray]:
        """
        Generate a mask for some data.

        :param data: Dataset with all flag bands.
        :param extra_mask: Extra mask. (e.g. extent mask)
        :return: A spatial mask with same dimensions and coordinates as data (including time).
        """

        def render_mask(data: xr.Dataset, mask: StyleMask) -> xr.DataArray:
            """
            Calculate a style mask.
            :param data: Raw Data
            :param mask: A StyleMask object to calculate
            :return: A DataArray boolean mask with no time dimension
            """
            pq_data = getattr(data, mask.band)
            odc_mask = mask.create_mask(pq_data)
            return odc_mask

        result = extra_mask
        for mask in self.masks:
            mask_data = render_mask(data, mask)
            if result is None:
                result = mask_data
            else:
                result = result & mask_data
        return result

    def apply_mask_to_image(self, img_data: xr.Dataset, mask: Optional[xr.DataArray],
                            input_date_count: int, output_date_count: int) -> xr.Dataset:
        """
        Apply a mask to an image xarray.

        :param img_data: XArray with uint8 bands red, green and blue - and optionally alpha.
        :param mask: Optional mask, as returned by to_mask()
        :param input_date_count: Number of timeslices in raw data (and therefore in the mask if supplied)
        :param output_date_count: Number of timeslices in img_data
        :return: XArray with uint8
        """

        if "alpha" not in img_data.data_vars.keys():
            nda_alpha = np.ndarray(img_data["red"].shape, dtype='uint8')
            nda_alpha.fill(255)
            alpha = xr.DataArray(nda_alpha,
                                coords=img_data["red"].coords,
                                dims=img_data["red"].dims,
                                name="alpha"
            )
        else:
            alpha = img_data.alpha
        if mask is not None:
            if output_date_count == 1 and input_date_count > 1:
                flat_mask: Optional[xr.DataArray] = None
                for coord in mask.coords["time"].values:
                    mask_slice = mask.sel(time=coord)
                    if flat_mask is None:
                        flat_mask = mask_slice
                    else:
                        flat_mask &= mask_slice
                mask = cast(xr.DataArray, flat_mask)
            alpha = alpha.where(mask, other=0)
        img_data = img_data.assign({"alpha": alpha})
        return img_data

    def transform_data(self, data: xr.Dataset, mask: Optional[xr.DataArray]) -> xr.Dataset:
        """
        Apply style to raw data to make an RGBA image xarray (time aware-ish)

        :param data: Raw ODC data, with all required data bands and flag bands.
        :param mask: Optional additional mask to apply.
        :return: Xarray dataset with RGBA uint8 bands. (time MAY be collapsed)
        """
        input_date_count = self.count_dates(data)
        mdh = self.get_multi_date_handler(input_date_count)
        if mdh is None:
            img_data = self.transform_single_date_data(data)
        else:
            img_data = mdh.transform_data(data)
        if "time" not in img_data.coords or not img_data.time.shape:
            output_date_count = 1
        else:
            output_date_count = len(data.coords["time"])
            if output_date_count == 1:
                img_data = img_data.squeeze(dim="time", drop=True)
        img_data = self.apply_mask_to_image(img_data, mask, input_date_count, output_date_count)
        return img_data

    def transform_single_date_data(self, data: xr.Dataset) -> xr.Dataset:
        """
        Apply style to raw data to make an RGBA image xarray (single time slice only)
        Over-ridden by subclasses.

        :param data: Raw data, all bands.
        :return: RGBA uint8 xarray
        """
        raise NotImplementedError()

    # pylint: disable=attribute-defined-outside-init
    def parse_legend_cfg(self, cfg: CFG_DICT) -> None:
        """Used by __init__()"""
        self.show_legend = cast(bool, cfg.get("show_legend", self.auto_legend))
        self.legend_url_override = cast(Optional[str], cfg.get('url', None))
        self.legend_cfg = cfg

    def render_legend(self, dates: Union[int, List[Any]]) -> Optional["PIL.Image.Image"]:
        """
        Render legend, if possible
        :param dates: The number of dates to render the legend for (e.g. for delta)
        :return: A PIL Image object, or None.
        """
        mdh = self.get_multi_date_handler(dates)
        url = self.legend_override_with_url(mdh)
        if url:
            return get_image_from_url(url)
        if not self.auto_legend:
            return None
        bytesio = io.BytesIO()
        if mdh:
            mdh.legend(bytesio)
        else:
            self.single_date_legend(bytesio)
        bytesio.seek(0)
        return Image.open(bytesio)

    def single_date_legend(self, bytesio: io.BytesIO) -> None:
        """
        Write a legend into a bytes buffer as a PNG image.

        Overridden by subclasses.

        :param bytesio:  io.BytesIO byte buffer.
        """
        raise NotImplementedError()

    def legend_override_with_url(self, mdh: Optional["StyleDefBase.MultiDateHandler"] = None) -> Optional[str]:
        """
        Find appropriate overide URL
        :param mdh: Optional multidatehandler.  If None, use default single date override url.
        :return: A URL string, or None
        """
        if mdh:
            return mdh.legend_url_override
        return self.legend_url_override

    @staticmethod
    def count_dates(count_or_sized_or_ds: Union[int, Sized, xr.Dataset]) -> int:
        if isinstance(count_or_sized_or_ds, int):
            return count_or_sized_or_ds
        elif isinstance(count_or_sized_or_ds, xr.Dataset):
            data = count_or_sized_or_ds
            if not data.time.shape:
                return 1
            else:
                return len(data.coords["time"])
        else:
            return len(count_or_sized_or_ds)

    def get_multi_date_handler(self, count_or_sized_or_ds: Union[int, Sized, xr.Dataset]
                               ) -> Optional["StyleDefBase.MultiDateHandler"]:
        """
        Get the appropriate multidate handler.

        :param count: The number of dates in the query
        :return: A multidate handler object, or None, for the default single-date case.
        """
        count = self.count_dates(count_or_sized_or_ds)
        for mdh in self.multi_date_handlers:
            if mdh.applies_to(count):
                return mdh
        if count in [0, 1]:
            return None
        raise WMSException(f"Style {self.name} does not support requests with {count} dates")

    @classmethod
    def register_subclass(cls, subclass: Type["StyleDefBase"], triggers: Iterable[str], priority: bool = False) -> None:
        """
        Register a subclass with the base class

        :param subclass: A Sub-class of StyleDefBase
        :param triggers: dictionary keys, the presence of any of which in the configuration will indicate the subclass
        :param priority: Priority triggers are checked before non-priority triggers.
        """
        if isinstance(triggers, str):
            triggers = [triggers]
        if priority:
            style_class_priority_reg.append([subclass, triggers])
        else:
            style_class_reg.append([subclass, triggers])

    @classmethod
    def determine_subclass(cls, cfg: CFG_DICT) -> Optional[Type["StyleDefBase"]]:
        """
        Determine the subclass to use from a raw configuration
        :param cfg: The configuration for some StyleDef subclass
        :return: The StyleDef subclass, or None if no match found
        """
        for sub, triggers in style_class_priority_reg + style_class_reg:
            for trig in triggers:
                if trig in cfg:
                    return sub
        return None

    class MultiDateHandler(OWSConfigEntry):
        """
        MultiDateHandler base class.

        Should be overridden by style subclasses wishing to support multidate requests.

        (TODO: Shares code with style base class inefficiently.)
        """
        auto_legend: bool = False

        non_animate_requires_aggregator = True

        def __init__(self, style: "StyleDefBase", cfg: CFG_DICT) -> None:
            """
            First stage initialisation

            :param style: The parent style object
            :param cfg: The multidate handler configuration
            """
            super().__init__(cfg)
            raw_cfg = cast(CFG_DICT, self._raw_cfg)
            self.style = style
            if "allowed_count_range" not in raw_cfg:
                raise ConfigException("multi_date handler must have an allowed_count_range")
            if len(cast(List[int], cfg["allowed_count_range"])) > 2:
                raise ConfigException("multi_date handler allowed_count_range must have 2 and only 2 members")
            self.min_count, self.max_count = cast(List[int], cfg["allowed_count_range"])
            if self.max_count < self.min_count:
                raise ConfigException("multi_date handler allowed_count_range: minimum must be less than equal to maximum")

            self.animate = cast(bool, cfg.get("animate", False))
            self.frame_duration: int = 1000
            if "aggregator_function" in cfg:
                self.aggregator: Optional[FunctionWrapper] = FunctionWrapper(style.product,
                                                  cast(CFG_DICT, cfg["aggregator_function"]),
                                                                             stand_alone=self.style.stand_alone)
            elif self.animate:
                self.aggregator = FunctionWrapper(style.product, lambda x: x, stand_alone=True)
                self.frame_duration = cast(int, cfg.get("frame_duration", 1000))
            else:
                self.aggregator = None
                if self.non_animate_requires_aggregator:
                    raise ConfigException("Aggregator function is required for non-animated multi-date handlers.")
            self.parse_legend_cfg(cast(CFG_DICT, cfg.get("legend", {})))
            self.preserve_user_date_order = cast(bool, cfg.get("preserve_user_date_order", False))

        def applies_to(self, count: int) -> bool:
            """Does this multidate handler apply to a request with this number of dates?"""
            return self.min_count <= count and self.max_count >= count

        def __repr__(self) -> str:
            if self.min_count == self.max_count:
                return str(self.min_count)
            return f"{self.min_count}-{self.max_count}"

        def range_str(self) -> str:
            return self.__repr__()

        def transform_data(self, data: xr.Dataset) -> xr.Dataset:
            """
            Apply image transformation

            For implementation by subclasses.

            :param data: Raw data
            :return: RGBA image xarray.  May have a time dimension
            """
            return self.style.transform_single_date_data(data)

        # pylint: disable=attribute-defined-outside-init
        def parse_legend_cfg(self, cfg: CFG_DICT) -> None:
            self.show_legend = cast(bool, cfg.get("show_legend", self.auto_legend))
            self.legend_url_override = cast(Optional[str], cfg.get('url', None))
            self.legend_cfg = cfg

        def legend(self, bytesio: io.BytesIO) -> None:
            """
            Write a legend as a png to a bytesio buffer.
            
            :param bytesio: 
            """


    @classmethod
    def lookup_impl(cls,
                    cfg: "datacube_ows.ows_configuration.OWSConfig",
                    keyvals: Mapping[str, Any],
                    subs: Optional[Mapping[str, Any]] = None) -> OWSIndexedConfigEntry:
        """
        Lookup a config entry of this type by identifying label(s)

        :param cfg:  The global config object that the desired object lives under.
        :param keyvals: Keyword dictionary of identifying label(s)
        :param subs:  Dictionary of keyword substitutions.  Used for e.g. looking up a style from a different layer.
        :return: The desired config object
        :raises: OWSEntryNotFound exception if no matching object found.
        """
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


# Style class registries
style_class_priority_reg: List[Tuple[Type[StyleDefBase], Iterable[str]]] = []
style_class_reg: List[Tuple[Type[StyleDefBase], Iterable[str]]] = []


class StyleMask(AbstractMaskRule):
    VALUES_LABEL = "enum"
    def __init__(self, cfg: CFG_DICT, style: StyleDefBase) -> None:
        band = cast(str, cfg["band"])
        super().__init__(band, cfg)
        self.stand_alone = style.stand_alone
        self.style = style
        self.stand_alone = style.stand_alone
        if not self.stand_alone:
            if not self.style.product.flag_bands:
                raise ConfigException(f"Style {self.style.name} in layer {self.style.product.name} contains a mask, but the layer has no flag bands")

            if band not in self.style.product.flag_bands:
                raise ConfigException(f"Style {self.style.name} has a mask that references flag band {band} which is not defined for the layer")
        if self.stand_alone:
            self.flag_band: FlagBand = OWSFlagBandStandalone(self.band)
        else:
            self.flag_band = cast(FlagBand, self.style.product.flag_bands[self.band])

    def create_mask(self, data: xr.DataArray) -> xr.DataArray:
        mask = super().create_mask(data)
        return mask

# Minimum Viable Proxy Objects, for standalone API

class StandaloneGlobalProxy:
    pass

class BandIdxProxy:
    def band(self, band):
        return band


class GlobalCfgProxy:
    internationalised = False


class StandaloneProductProxy:
    name = "standalone"
    global_cfg = GlobalCfgProxy()
    band_idx = BandIdxProxy()
