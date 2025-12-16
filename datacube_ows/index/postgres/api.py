# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

from collections.abc import Iterable
from threading import Lock
from typing import Literal, cast
from uuid import UUID

import click
from datacube import Datacube
from datacube.model import Dataset, Product
from odc.geo import CRS, Geometry
from sqlalchemy import text
from typing_extensions import override

from datacube_ows.index.api import (
    InsufficientDbPrivileges,
    LayerExtent,
    LayerSignature,
    OWSAbstractIndex,
    OWSAbstractIndexDriver,
    TimeSearchTerm,
    check_perms,
)
from datacube_ows.index.sql import run_sql
from datacube_ows.ows_configuration import OWSNamedLayer
from datacube_ows.utils import get_driver_name, get_sqlconn

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
            with get_sqlconn(dc) as conn:
                results = conn.execute(
                    text("""
                    SELECT *
                    FROM ows.layer_ranges
                    LIMIT 1""")
                )
                for _ in results:
                    db_ok = True
        except Exception:
            pass
        return db_ok

    @override
    def _check_perms(self, dc: Datacube, group: Literal["manage", "admin"]) -> None:
        if get_driver_name(dc.index) == "psycopg":
            from psycopg.errors import ProgrammingError
        else:
            from psycopg2.errors import ProgrammingError
        try:
            with get_sqlconn(dc) as conn:
                conn.execute(text(f"set role agdc_{group}"))
        except ProgrammingError as e:
            raise InsufficientDbPrivileges(
                f"db user {dc.index.environment.db_username} does not have agdc_{group} privileges: {e}"
            ) from None

    # method to delete obsolete schemas etc.
    @override
    @check_perms("admin")
    def cleanup_schema(self, dc: Datacube) -> None:
        self._run_sql(dc, "ows_schema/cleanup")

    # Schema creation method
    @override
    @check_perms("admin")
    def create_schema(self, dc: Datacube) -> None:
        click.echo("Creating schema and postgis extension...")
        self._run_sql(dc, "ows_schema/bootstrap")
        click.echo("Creating/updating tables...")
        self._run_sql(dc, "ows_schema/create")
        click.echo("Creating/updating materialised views...")
        self._run_sql(dc, "extent_views/create")
        click.echo("Granting tables permissions to agdc roles.")
        self._run_sql(dc, "ows_schema/grants")
        click.echo("Granting views permissions to agdc roles.")
        self._run_sql(dc, "extent_views/grants")

    # Spatiotemporal index update method (e.g. refresh materialised views)
    @override
    @check_perms("manage")
    def update_geotemporal_index(self, dc: Datacube) -> None:
        self._run_sql(dc, "extent_views/refresh")

    @override
    @check_perms("manage")
    def create_range_entry(
        self, layer: OWSNamedLayer, cache: dict[LayerSignature, list[str]]
    ) -> None:
        create_range_entry_impl(layer, cache)

    @override
    def get_ranges(self, layer: OWSNamedLayer) -> LayerExtent | None:
        return get_ranges_impl(layer)

    @override
    def ds_search(
        self,
        layer: OWSNamedLayer,
        times: Iterable[TimeSearchTerm] | None = None,
        geom: Geometry | None = None,
        products: Iterable[Product] | None = None,
    ) -> Iterable[Dataset]:
        return cast(
            Iterable[Dataset],
            mv_search(
                layer.dc,
                MVSelectOpts.DATASETS,
                times=times,
                geom=geom,
                products=products,
            ),
        )

    @override
    def dsid_search(
        self,
        layer: OWSNamedLayer,
        times: Iterable[TimeSearchTerm] | None = None,
        geom: Geometry | None = None,
        products: Iterable[Product] | None = None,
    ) -> Iterable[UUID]:
        return cast(
            Iterable[UUID],
            mv_search(
                layer.dc,
                MVSelectOpts.IDS,
                times=times,
                geom=geom,
                products=products,
            ),
        )

    @override
    def count(
        self,
        layer: OWSNamedLayer,
        times: Iterable[TimeSearchTerm] | None = None,
        geom: Geometry | None = None,
        products: Iterable[Product] | None = None,
    ) -> int:
        return cast(
            int,
            mv_search(
                layer.dc,
                MVSelectOpts.COUNT,
                times=times,
                geom=geom,
                products=products,
            ),
        )

    @override
    def extent(
        self,
        layer: OWSNamedLayer,
        times: Iterable[TimeSearchTerm] | None = None,
        geom: Geometry | None = None,
        products: Iterable[Product] | None = None,
        crs: CRS | None = None,
    ) -> Geometry | None:
        extent = cast(
            Geometry | None,
            mv_search(
                layer.dc,
                MVSelectOpts.EXTENT,
                times=times,
                geom=geom,
                products=products,
            ),
        )
        if extent is None or crs is None or crs == extent.crs:
            return extent
        return extent.to_crs(crs)

    def _run_sql(self, dc: Datacube, path: str, **params: str) -> bool:
        return run_sql(dc, path, **params)


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
