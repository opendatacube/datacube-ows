# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import click
import datetime

from threading import Lock
from typing import Any, Iterable, Type
from uuid import UUID

from odc.geo import Geometry, CRS
from datacube import Datacube
from datacube.model import Product, Dataset, Range

from datacube_ows.ows_configuration import OWSNamedLayer
from datacube_ows.index.api import OWSAbstractIndex, OWSAbstractIndexDriver, LayerSignature, LayerExtent, TimeSearchTerm
from datacube_ows.index.sql import run_sql
from .product_ranges import create_range_entry as create_range_entry_impl, get_ranges as get_ranges_impl
from ...utils import default_to_utc


class OWSPostgisIndex(OWSAbstractIndex):
    name: str = "postgis"

    # method to delete obsolete schemas etc.
    def cleanup_schema(self, dc: Datacube):
        # No obsolete schema for postgis databases to clean up.
        pass

    # Schema creation method
    def create_schema(self, dc: Datacube):
        click.echo("Creating/updating schema and tables...")
        self._run_sql(dc, "ows_schema/create")

    # Permission management method
    def grant_perms(self, dc: Datacube, role: str, read_only: bool = False):
        if read_only:
            self._run_sql(dc, "ows_schema/grants/read_only", role=role)
        else:
            self._run_sql(dc, "ows_schema/grants/read_write", role=role)

    # Spatiotemporal index update method (e.g. refresh materialised views)
    def update_geotemporal_index(self, dc: Datacube):
        # Native ODC geotemporal index used in postgis driver.
        pass

    def create_range_entry(self, layer: OWSNamedLayer, cache: dict[LayerSignature, list[str]]) -> None:
        create_range_entry_impl(layer, cache)

    def get_ranges(self, layer: OWSNamedLayer) -> LayerExtent | None:
        return get_ranges_impl(layer)

    def _query(self,
               layer: OWSNamedLayer,
               times: Iterable[TimeSearchTerm] | None = None,
               geom: Geometry | None = None,
               products: Iterable[Product] | None = None
               ) -> dict[str, Any]:
        query: dict[str, Any] = {}
        if geom:
            query["geopolygon"] = self._prep_geom(layer, geom)
        if products is not None:
            query["product"] = [p.name for p in products]
        if times is not None:
            time_args = []
            def normalise_to_dtr(unnorm: datetime.datetime | datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
                if isinstance(unnorm, datetime.datetime):
                    st: datetime.datetime = default_to_utc(unnorm)
                    tmax = st + datetime.timedelta(seconds=1)
                elif isinstance(t, datetime.date):
                    st = datetime.datetime(unnorm.year, unnorm.month, unnorm.day, tzinfo=datetime.timezone.utc)
                    tmax = st + datetime.timedelta(days=1)
                return st, tmax

            for t in times:
                if isinstance(t, (datetime.date, datetime.datetime)):
                    st, tmax = normalise_to_dtr(t)
                    time_args.append(Range(st, tmax))
                else:
                    st, et = t
                    st, _ = normalise_to_dtr(st)
                    et, _ = normalise_to_dtr(et)
                    time_args.append(Range(st, et))
            if len(time_args) > 1:
                raise ValueError("Huh?")
            query["time"] = time_args[0]
        return query

    def ds_search(self,
                  layer: OWSNamedLayer,
                  times: Iterable[TimeSearchTerm] | None = None,
                  geom: Geometry | None = None,
                  products: Iterable[Product] | None = None
                  ) -> Iterable[Dataset]:
        return layer.dc.index.datasets.search(**self._query(layer, times, geom, products))

    def dsid_search(self,
                    layer: OWSNamedLayer,
                    times: Iterable[TimeSearchTerm] | None = None,
                    geom: Geometry | None = None,
                    products: Iterable[Product] | None = None
                    ) -> Iterable[UUID]:
        for ds in layer.dc.index.datasets.search_returning(field_names=["id"],
                                                           **self._query(layer, times, geom, products)):
            yield ds.id  # type: ignore[attr-defined]

    def count(self,
              layer: OWSNamedLayer,
              times: Iterable[TimeSearchTerm] | None = None,
              geom: Geometry | None = None,
              products: Iterable[Product] | None = None
              ) -> int:
        return layer.dc.index.datasets.count(**self._query(layer, times, geom, products))

    def extent(self,
               layer: OWSNamedLayer,
               times: Iterable[TimeSearchTerm] | None = None,
               geom: Geometry | None = None,
               products: Iterable[Product] | None = None,
               crs: CRS | None = None
               ) -> Geometry | None:
        if crs is None:
            crs = CRS("epsg:4326")
        return layer.dc.index.datasets.spatial_extent(
            layer.dc.index.datasets.search(
                **self._query(layer, times, geom, products)
            ),
            crs=crs
        )

    def _run_sql(self, dc: Datacube, path: str, **params: str) -> bool:
        return run_sql(dc, self.name, path, **params)


pgisdriverlock = Lock()


class OWSPostgisIndexDriver(OWSAbstractIndexDriver):
    _driver = None
    @classmethod
    def ows_index_class(cls) -> Type[OWSAbstractIndex]:
        return OWSPostgisIndex

    @classmethod
    def ows_index(cls) -> OWSAbstractIndex:
        with pgisdriverlock:
            if cls._driver is None:
                cls._driver = OWSPostgisIndex()
        return cls._driver


def ows_index_driver_init():
    return OWSPostgisIndexDriver()
