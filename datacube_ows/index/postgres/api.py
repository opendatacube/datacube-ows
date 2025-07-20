# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Iterable
from threading import Lock
from typing import cast
from uuid import UUID

import click
from datacube import Datacube
from datacube.model import Dataset, Product
from odc.geo import CRS, Geometry
from sqlalchemy import text
from typing_extensions import override

from datacube_ows.index.api import (
    LayerExtent,
    LayerSignature,
    OWSAbstractIndex,
    OWSAbstractIndexDriver,
    TimeSearchTerm,
)
from datacube_ows.index.sql import run_sql
from datacube_ows.ows_configuration import OWSNamedLayer

from .mv_index import MVSelectOpts, mv_search
from .product_ranges import create_range_entry as create_range_entry_impl
from .product_ranges import get_ranges as get_ranges_impl


class OWSPostgresIndex(OWSAbstractIndex):
    name: str = "postgres"

    # method to check database access (for ping op)
    @override
    def check_db_access(self, dc: Datacube) -> bool:
        db_ok = False
        try:
            with dc.index._db.give_me_a_connection() as conn:  # type: ignore[attr-defined]
                results = conn.execute(text("""
                    SELECT *
                    FROM ows.layer_ranges
                    LIMIT 1""")
                )
                for _ in results:
                    db_ok = True
        except Exception:
            pass
        return db_ok

    # method to delete obsolete schemas etc.
    @override
    def cleanup_schema(self, dc: Datacube) -> None:
        self._run_sql(dc, "ows_schema/cleanup")

    # Schema creation method
    @override
    def create_schema(self, dc: Datacube) -> None:
        click.echo("Creating/updating schema and tables...")
        self._run_sql(dc, "ows_schema/create")
        click.echo("Creating/updating materialised views...")
        self._run_sql(dc, "extent_views/create")
        click.echo("Setting ownership of materialised views...")
        self._run_sql(dc, "extent_views/grants/refresh_owner")

    # Permission management method
    @override
    def grant_perms(self, dc: Datacube, role: str, read_only: bool = False) -> None:
        if read_only:
            self._run_sql(dc, "ows_schema/grants/read_only", role=role)
            self._run_sql(dc, "extent_views/grants/read_only", role=role)
        else:
            self._run_sql(dc, "ows_schema/grants/read_write", role=role)
            self._run_sql(dc, "extent_views/grants/write_refresh", role=role)

    # Spatiotemporal index update method (e.g. refresh materialised views)
    @override
    def update_geotemporal_index(self, dc: Datacube) -> None:
        self._run_sql(dc, "extent_views/refresh")

    @override
    def create_range_entry(self, layer: OWSNamedLayer, cache: dict[LayerSignature, list[str]]) -> None:
        create_range_entry_impl(layer, cache)

    @override
    def get_ranges(self, layer: OWSNamedLayer) -> LayerExtent | None:
        return get_ranges_impl(layer)

    @override
    def ds_search(self,
                  layer: OWSNamedLayer,
                  times: Iterable[TimeSearchTerm] | None = None,
                  geom: Geometry | None = None,
                  products: Iterable[Product] | None = None
                  ) -> Iterable[Dataset]:
        return cast(Iterable[Dataset], mv_search(layer.dc.index, MVSelectOpts.DATASETS,
                                                 times=times, geom=geom, products=products))

    @override
    def dsid_search(self,
                    layer: OWSNamedLayer,
                    times: Iterable[TimeSearchTerm] | None = None,
                    geom: Geometry | None = None,
                    products: Iterable[Product] | None = None
                    ) -> Iterable[UUID]:
        return cast(Iterable[UUID], mv_search(layer.dc.index, MVSelectOpts.IDS,
                                              times=times, geom=geom, products=products))

    @override
    def count(self,
              layer: OWSNamedLayer,
              times: Iterable[TimeSearchTerm] | None = None,
              geom: Geometry | None = None,
              products: Iterable[Product] | None = None
              ) -> int:
        return cast(int, mv_search(layer.dc.index, MVSelectOpts.COUNT,
                                   times=times, geom=geom, products=products))

    @override
    def extent(self,
               layer: OWSNamedLayer,
               times: Iterable[TimeSearchTerm] | None = None,
               geom: Geometry | None = None,
               products: Iterable[Product] | None = None,
               crs: CRS | None = None
               ) -> Geometry | None:
        extent = cast(Geometry | None, mv_search(layer.dc.index, MVSelectOpts.EXTENT,
                                                 times=times, geom=geom, products=products))
        if extent is None or crs is None or crs == extent.crs:
            return extent
        return extent.to_crs(crs)

    def _run_sql(self, dc: Datacube, path: str, **params: str) -> bool:
        return run_sql(dc, self.name, path, **params)


pgdriverlock = Lock()


class OWSPostgresIndexDriver(OWSAbstractIndexDriver):
    _driver = None
    @classmethod
    @override
    def ows_index_class(cls) -> type[OWSAbstractIndex]:
        return OWSPostgresIndex

    @classmethod
    @override
    def ows_index(cls) -> OWSAbstractIndex:
        with pgdriverlock:
            if cls._driver is None:
                cls._driver = OWSPostgresIndex()
        return cls._driver


def ows_index_driver_init() -> OWSPostgresIndexDriver:
    return OWSPostgresIndexDriver()
