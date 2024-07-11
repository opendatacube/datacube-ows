# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import datetime
import logging
from collections import OrderedDict
from typing import Iterable, Mapping, cast
from uuid import UUID

import datacube
import numpy
import xarray
from odc.geo.geobox import GeoBox
from odc.geo.geom import Geometry, CRS
from odc.geo.warp import Resampling

from datacube_ows.ogc_exceptions import WMSException
from datacube_ows.ows_configuration import OWSNamedLayer
from datacube_ows.startup_utils import CredentialManager
from datacube_ows.styles import StyleDef
from datacube_ows.utils import log_call
from datacube_ows.wms_utils import solar_correct_data

_LOG: logging.Logger = logging.getLogger(__name__)


class ProductBandQuery:
    def __init__(self,
                 products: list[datacube.model.Product],
                 bands: Iterable[str],
                 main: bool = False, manual_merge: bool = False, ignore_time: bool = False,
                 fuse_func: datacube.api.core.FuserFunction | None = None
    ):
        self.products = products
        self.bands = set(bands)
        self.manual_merge = manual_merge
        self.fuse_func = fuse_func
        self.ignore_time = ignore_time
        self.main = main
        self.key = (
            tuple((p.id for p in self.products)),
            tuple(bands)
        )

    def __str__(self):
        return f"Query bands {self.bands} from products {self.products}"

    def __hash__(self):
        return hash(self.key)

    @classmethod
    def style_queries(cls, style: StyleDef, resource_limited: bool = False) -> list["ProductBandQuery"]:
        queries = [
            cls.simple_layer_query(style.product, style.needed_bands,
                                   manual_merge=style.product.data_manual_merge,
                                   fuse_func=style.product.fuse_func,
                                   resource_limited=resource_limited)
        ]
        for fp in style.flag_products:
            if fp.products_match(style.product.product_names):
                for band in fp.bands:
                    assert band in style.needed_bands, "Style band not in needed bands list"
            else:
                if resource_limited:
                    pq_products = fp.low_res_products
                else:
                    pq_products = fp.products
                queries.append(cls(
                    pq_products,
                    list(fp.bands),
                    manual_merge=fp.manual_merge,
                    ignore_time=fp.ignore_time,
                    fuse_func=fp.fuse_func
                ))
        return queries

    @classmethod
    def full_layer_queries(cls,
                           layer: OWSNamedLayer,
                           main_bands: list[str] | None = None) -> list["ProductBandQuery"]:
        if main_bands:
            needed_bands: Iterable[str] = main_bands
        else:
            needed_bands = set(layer.band_idx.band_cfg.keys())
        queries = [
            cls.simple_layer_query(layer, needed_bands,
                                   manual_merge=layer.data_manual_merge,
                                   fuse_func=layer.fuse_func,
                                   resource_limited=False)
        ]
        for fpb in layer.allflag_productbands:
            if fpb.products_match(layer.product_names):
                for band in fpb.bands:
                    assert band in needed_bands, "main product band not in needed bands list"
            else:
                pq_products = fpb.products
                queries.append(cls(
                    pq_products,
                    list(fpb.bands),
                    manual_merge=fpb.manual_merge,
                    ignore_time=fpb.ignore_time,
                    fuse_func=fpb.fuse_func
                ))
        return queries

    @classmethod
    def simple_layer_query(cls, layer: OWSNamedLayer,
                           bands: Iterable[str],
                           manual_merge: bool = False,
                           fuse_func: datacube.api.core.FuserFunction | None = None,
                           resource_limited: bool = False) -> "ProductBandQuery":
        if resource_limited:
            main_products = layer.low_res_products
        else:
            main_products = layer.products
        return cls(main_products, bands, manual_merge=manual_merge, main=True, fuse_func=fuse_func)

PerPBQReturnType = xarray.DataArray | Iterable[UUID]

class DataStacker:
    @log_call
    def __init__(self,
                 layer: OWSNamedLayer,
                 geobox: GeoBox,
                 times: list[datetime.datetime],
                 resampling: Resampling | None = None,
                 style: StyleDef | None = None,
                 bands: list[str] | None = None):
        self._layer = layer
        self.cfg = layer.global_cfg
        self._geobox = geobox
        self._resampling = resampling if resampling is not None else "nearest"
        self.style = style
        if style:
            self._needed_bands = list(style.needed_bands)
        elif bands:
            self._needed_bands = [self._layer.band_idx.locale_band(b) for b in bands]
        else:
            self._needed_bands = list(self._layer.band_idx.measurements.keys())

        for band in self._layer.always_fetch_bands:
            if band not in self._needed_bands:
                self._needed_bands.append(band)
        self.raw_times = times
        if self._layer.mosaic_date_func:
            self._times = [self._layer.mosaic_date_func(layer.ranges.times)]
        else:
            self._times = [
                    self._layer.search_times(
                            t, self._geobox)
                    for t in times
            ]
        self.group_by = self._layer.dataset_groupby()
        self.resource_limited = False

    def needed_bands(self) -> list[str]:
        return self._needed_bands

    def n_datasets(self) -> int:
        if self.style:
            # we have a style - lets go with that.
            queries = ProductBandQuery.style_queries(self.style)
        else:
            # Just take needed bands.
            queries = [ProductBandQuery.simple_layer_query(self._layer, self.needed_bands())]
        geom = self._geobox.extent
        for query in queries:
            if query.ignore_time:
                qry_times = None
            else:
                qry_times = self._times
            return self._layer.ows_index().count(self._layer, times=qry_times, geom=geom, products=query.products)
        return 0

    def extent(self, crs: CRS | None = None) -> Geometry | None:
        query = ProductBandQuery.simple_layer_query(
                self._layer,
                self.needed_bands(),
                self.resource_limited
        )
        geom = self._geobox.extent
        if query.ignore_time:
            times = None
        else:
            times = self._times
        return self._layer.ows_index().extent(self._layer, times=times, geom=geom, products=query.products, crs=crs)

    def dsids(self) -> dict[ProductBandQuery, Iterable[UUID]]:
        if self.style:
            # we have a style - lets go with that.
            queries = ProductBandQuery.style_queries(self.style)
        else:
            # Just take needed bands.
            queries = [ProductBandQuery.simple_layer_query(self._layer, self.needed_bands())]
        results: list[tuple[ProductBandQuery, Iterable[UUID]]] = []
        for query in queries:
            if query.ignore_time:
                qry_times = None
            else:
                qry_times = self._times
            result = self._layer.ows_index().dsid_search(self._layer, times=qry_times, geom=self._geobox.extent,
                                                         products=query.products)
            results.append((query, result))
        return OrderedDict(results)

    def datasets_all_time(self, point: Geometry | None = None) -> xarray.DataArray:
        query = ProductBandQuery.simple_layer_query(
                    self._layer,
                    self.needed_bands(),
                    self.resource_limited)
        if point:
            geom = point
        else:
            geom = self._geobox.extent
        result = self._layer.ows_index().ds_search(
            layer=self._layer,
            geom=geom,
            products=query.products)
        grpd_result = datacube.Datacube.group_datasets(
            cast(Iterable[datacube.model.Dataset], result),
            self.group_by
        )
        return grpd_result

    def datasets(self,
                 all_flag_bands: bool = False,
                 point: Geometry | None = None,
                 ) -> dict[ProductBandQuery, xarray.DataArray]:
        if self.style:
            # we have a style - lets go with that.
            queries = ProductBandQuery.style_queries(self.style)
        elif all_flag_bands:
            queries = ProductBandQuery.full_layer_queries(self._layer, self.needed_bands())
        else:
            # Just take needed bands.
            queries = [ProductBandQuery.simple_layer_query(self._layer, self.needed_bands())]

        if point:
            geom = point
        else:
            geom = self._geobox.extent
        results: list[tuple[ProductBandQuery, xarray.DataArray]] = []
        for query in queries:
            if query.ignore_time:
                qry_times = None
            else:
                qry_times = self._times
            result = self._layer.ows_index().ds_search(
                               layer=self._layer,
                               times=qry_times,
                               geom=geom,
                               products=query.products)
            grpd_result = datacube.Datacube.group_datasets(
                cast(Iterable[datacube.model.Dataset], result),
                self.group_by
            )
            results.append((query, grpd_result))
        return OrderedDict(results)

    def create_nodata_filled_flag_bands(self, data: xarray.Dataset, pbq: ProductBandQuery) -> xarray.Dataset:
        var = None
        for var in data.data_vars.variables.keys():
            break
        if var is None:
            raise WMSException("Cannot add default flag data as there is no non-flag data available")
        template = cast(xarray.DataArray, getattr(data, cast(str, var)))
        data_new_bands = {}
        for band in pbq.bands:
            default_value = pbq.products[0].measurements[band].nodata
            new_data: numpy.ndarray = numpy.ndarray(template.shape, dtype="uint8")
            new_data.fill(default_value)
            qry_result = template.copy(data=new_data)
            data_new_bands[band] = qry_result
        data = data.assign(data_new_bands)
        for band in pbq.bands:
            data[band].attrs["flags_definition"] = pbq.products[0].measurements[band].flags_definition
        return data

    @log_call
    def data(self,
             datasets_by_query: dict[ProductBandQuery, xarray.DataArray],
             skip_corrections=False) -> xarray.Dataset | None:
        # pylint: disable=too-many-locals, consider-using-enumerate
        # datasets is an XArray DataArray of datasets grouped by time.
        data: xarray.Dataset | None = None
        for pbq, datasets in datasets_by_query.items():
            if data is not None and len(data.time) == 0:
                # No data, so no need for masking data.
                continue
            measurements = pbq.products[0].lookup_measurements(pbq.bands)
            fuse_func = pbq.fuse_func
            if pbq.manual_merge:
                qry_result = self.manual_data_stack(datasets, measurements, pbq.bands, skip_corrections, fuse_func=fuse_func)
            else:
                qry_result = self.read_data(datasets, measurements, self._geobox, resampling=self._resampling, fuse_func=fuse_func)
            if qry_result is None:
                continue
            if data is None:
                data = qry_result
                continue
            if len(data.time) == 0:
                # No data, so no need for masking data.
                continue
            if pbq.ignore_time:
                # regularise time dimension:
                if len(qry_result.time) > 1:
                    raise WMSException("Cannot ignore time on PQ (flag) bands from a time-aware product")
                elif len(qry_result.time) == len(data.time):
                    qry_result["time"] = data.time
                else:
                    if len(qry_result.time) == 0:
                        data = self.create_nodata_filled_flag_bands(data, pbq)
                        continue
                    else:
                        data_new_bands = {}
                        for band in pbq.bands:
                            band_data = qry_result[band]
                            timeless_band_data = band_data.sel(time=qry_result.time.values[0])
                            band_time_slices = []
                            for dt in data.time.values:
                                band_time_slices.append(timeless_band_data)
                            timed_band_data = xarray.concat(band_time_slices, data.time)
                            data_new_bands[band] = timed_band_data
                    data = data.assign(data_new_bands)
                    continue
            elif len(qry_result.time) == 0:
                # Time-aware mask product has no data, but main product does.
                data = self.create_nodata_filled_flag_bands(data, pbq)
                continue
            assert data is not None
            qry_result.coords["time"] = data.coords["time"]
            data = cast(xarray.Dataset, xarray.combine_by_coords([data, qry_result], join="exact"))

        return data

    @log_call
    def manual_data_stack(self,
                          datasets: xarray.DataArray,
                          measurements: Mapping[str, datacube.model.Measurement],
                          bands: set[str],
                          skip_corrections: bool,
                          fuse_func: datacube.api.core.FuserFunction | None) -> xarray.Dataset | None:
        # pylint: disable=too-many-locals, too-many-branches
        # manual merge
        if self.style:
            flag_bands: Iterable[str] = set(filter(lambda b: b in self.style.flag_bands, bands))  # type: ignore[arg-type]
            non_flag_bands: Iterable[str] = set(filter(lambda b: b not in self.style.flag_bands, bands))  #type: ignore[arg-type]
        else:
            non_flag_bands = bands
            flag_bands = set()
        time_slices = []
        for dt in datasets.time.values:
            tds = datasets.sel(time=dt)
            merged = None
            for ds in tds.values.item():
                d = self.read_data_for_single_dataset(ds, measurements, self._geobox, fuse_func=fuse_func)
                extent_mask = None
                for band in non_flag_bands:
                    for f in self._layer.extent_mask_func:
                        if extent_mask is None:
                            extent_mask = f(d, band)
                        else:
                            extent_mask &= f(d, band)
                if extent_mask is not None:
                    d = d.where(extent_mask)
                if self._layer.solar_correction and not skip_corrections:
                    for band in non_flag_bands:
                        d[band] = solar_correct_data(d[band], ds)
                if merged is None:
                    merged = d
                else:
                    merged = merged.combine_first(d)
            if merged is None:
                continue
            for band in flag_bands:
                # REVISIT: not sure about type converting one band like this?
                merged[band] = merged[band].astype('uint16', copy=True)
                merged[band].attrs = d[band].attrs
            time_slices.append(merged)

        if not time_slices:
            return None
        result = xarray.concat(time_slices, datasets.time)
        return result

    # Read data for given datasets and measurements per the output_geobox
    # TODO: Make skip_broken passed in via config
    @log_call
    def read_data(self,
                  datasets: xarray.DataArray,
                  measurements: Mapping[str, datacube.model.Measurement],
                  geobox: GeoBox,
                  skip_broken: bool = True,
                  resampling: Resampling = "nearest",
                  fuse_func: datacube.api.core.FuserFunction | None = None) -> xarray.Dataset:
        CredentialManager.check_cred()
        try:
            return datacube.Datacube.load_data(
                    datasets,
                    geobox,
                    measurements=measurements,
                    fuse_func=fuse_func,
                    skip_broken_datasets=skip_broken,
                    patch_url=self._layer.patch_url,
                    resampling=resampling)
        except Exception as e:
            _LOG.error("Error (%s) in load_data: %s", e.__class__.__name__, str(e))
            raise

    # TODO: Make skip_broken passed in via config
    @log_call
    def read_data_for_single_dataset(self,
                                     dataset: datacube.model.Dataset,
                                     measurements: Mapping[str, datacube.model.Measurement],
                                     geobox: GeoBox,
                                     skip_broken: bool = True,
                                     resampling: Resampling = "nearest",
                                     fuse_func: datacube.api.core.FuserFunction | None = None) -> xarray.Dataset:
        datasets = [dataset]
        dc_datasets = datacube.Datacube.group_datasets(datasets, self._layer.time_resolution.dataset_groupby())
        CredentialManager.check_cred()
        try:
            return datacube.Datacube.load_data(
                dc_datasets,
                geobox,
                measurements=measurements,
                fuse_func=fuse_func,
                skip_broken_datasets=skip_broken,
                patch_url=self._layer.patch_url,
                resampling=resampling)
        except Exception as e:
            _LOG.error("Error (%s) in load_data: %s", e.__class__.__name__, str(e))
            raise
