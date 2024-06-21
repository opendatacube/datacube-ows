# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import click

from threading import Lock
from typing import Iterable, Type
from uuid import UUID

from odc.geo import Geometry, CRS
from datacube import Datacube
from datacube.model import Product, Dataset

from datacube_ows.ows_configuration import OWSNamedLayer
from datacube_ows.index.api import OWSAbstractIndex, OWSAbstractIndexDriver, LayerSignature, LayerExtent, TimeSearchTerm
from datacube_ows.index.sql import run_sql


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
        raise NotImplementedError()

    def get_ranges(self, layer: OWSNamedLayer) -> LayerExtent | None:
        raise NotImplementedError()

    def ds_search(self,
                  layer: OWSNamedLayer,
                  times: Iterable[TimeSearchTerm] | None = None,
                  geom: Geometry | None = None,
                  products: Iterable[Product] | None = None
                  ) -> Iterable[Dataset]:
        raise NotImplementedError()

    def dsid_search(self,
                    layer: OWSNamedLayer,
                    times: Iterable[TimeSearchTerm] | None = None,
                    geom: Geometry | None = None,
                    products: Iterable[Product] | None = None
                    ) -> Iterable[UUID]:
        raise NotImplementedError()

    def count(self,
              layer: OWSNamedLayer,
              times: Iterable[TimeSearchTerm] | None = None,
              geom: Geometry | None = None,
              products: Iterable[Product] | None = None
              ) -> int:
        raise NotImplementedError()

    def extent(self,
               layer: OWSNamedLayer,
               times: Iterable[TimeSearchTerm] | None = None,
               geom: Geometry | None = None,
               products: Iterable[Product] | None = None,
               crs: CRS | None = None
               ) -> Geometry | None:
        raise NotImplementedError()

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
