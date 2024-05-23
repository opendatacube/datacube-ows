# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import dataclasses
from abc import ABC, abstractmethod
from datetime import datetime, date
from typing import NamedTuple, Iterable, Type
from uuid import UUID

from datacube import Datacube
from datacube.index.abstract import AbstractIndex
from datacube.model import Product, Dataset
from odc.geo import Geometry, CRS

from datacube_ows.config_utils import CFG_DICT, ConfigException

TYPE_CHECKING = False
if TYPE_CHECKING:
    from datacube_ows.ows_configuration import OWSNamedLayer

class AbortRun(Exception):
    pass


@dataclasses.dataclass(frozen=True)
class LayerSignature:
    time_res: str
    products: tuple[str, ...]
    env: str
    datasets: int

    def as_json(self) -> dict[str, list[str] | str | int]:
        return {
            "time_res": self.time_res,
            "products": list(self.products),
            "env": self.env,
            "datasets": self.datasets,
        }


DateOrDateTime = datetime | date
TimeSearchTerm = tuple[datetime, datetime] | tuple[date, date] | DateOrDateTime


class CoordRange(NamedTuple):
    min: float
    max: float


class LayerExtent:
    def __init__(self, lat: CoordRange, lon: CoordRange, times: list[DateOrDateTime], bboxes: CFG_DICT):
        self.lat = lat
        self.lon = lon
        self.times = times
        self.start_time = times[0]
        self.end_time = times[-1]
        self.time_set = set(times)
        self.bboxes = bboxes


class OWSAbstractIndex(ABC):
    name: str = ""

    # method to delete obsolete schemas etc.
    @abstractmethod
    def cleanup_schema(self, dc: Datacube):
        ...

    # Schema creation method
    @abstractmethod
    def create_schema(self, dc: Datacube):
        ...

    # Permission management method
    @abstractmethod
    def grant_perms(self, dc: Datacube, role: str, read_only: bool = False):
        ...

    # Spatiotemporal index update method (e.g. refresh materialised views)
    @abstractmethod
    def update_geotemporal_index(self, dc: Datacube):
        ...

    # Range table update method
    @abstractmethod
    def create_range_entry(self, layer: "OWSNamedLayer", cache: dict[LayerSignature, list[str]]) -> None:
        ...

    # Range table read method
    @abstractmethod
    def get_ranges(self, layer: "OWSNamedLayer") -> LayerExtent | None:
        ...

    # Spatiotemporal search methods
    @abstractmethod
    def ds_search(self,
                  layer: "OWSNamedLayer",
                  times: Iterable[TimeSearchTerm] | None = None,
                  geom: Geometry | None = None,
                  products: Iterable[Product] | None = None
                  ) -> Iterable[Dataset]:
        ...

    def dsid_search(self,
                    layer: "OWSNamedLayer",
                    times: Iterable[TimeSearchTerm] | None = None,
                    geom: Geometry | None = None,
                    products: Iterable[Product] | None = None
                    ) -> Iterable[UUID]:
        for ds in self.ds_search(layer, times, geom, products):
            yield ds.id

    def count(self,
              layer: "OWSNamedLayer",
              times: Iterable[TimeSearchTerm] | None = None,
              geom: Geometry | None = None,
              products: Iterable[Product] | None = None
              ) -> int:
        return len([dsid for dsid in self.dsid_search(layer, times, geom, products)])

    def extent(self,
               layer: "OWSNamedLayer",
               times: Iterable[TimeSearchTerm] | None = None,
               geom: Geometry | None = None,
               products: Iterable[Product] | None = None,
               crs: CRS | None = None
               ) -> Geometry | None:
        if crs is None:
            crs = CRS("epsg:4326")
        ext: Geometry | None = None
        # Accumulate extent in native CRS if possible.
        for ds in self.ds_search(layer, times, geom, products):
            if ds.extent:
                if ds.extent.crs != CRS(layer.native_CRS):
                    # Reproject to layer "native" CRS if needed.
                    ds_extent: Geometry = ds.extent.to_crs(layer.native_CRS)
                else:
                    ds_extent = ds.extent
                if ext is None:
                    ext = ds_extent
                else:
                    ext = ext.union(ds_extent)
        if ext is not None and crs != CRS(layer.native_CRS):
            # Reproject to requested CRS if necessary
            return ext.to_crs(crs)
        return ext


class OWSAbstractIndexDriver(ABC):
    @classmethod
    @abstractmethod
    def ows_index_class(cls) -> Type[OWSAbstractIndex]:
        ...

    @classmethod
    @abstractmethod
    def ows_index(cls) -> OWSAbstractIndex:
        ...


def ows_index(odc: Datacube | AbstractIndex) -> OWSAbstractIndex:
    if isinstance(odc, AbstractIndex):
        index = odc
    else:
        index = odc.index
    env = index.environment
    from datacube_ows.index.driver import ows_index_driver_by_name
    if env.index_driver in ('default', 'legacy'):
        idx_drv_name = "postgres"
    else:
        idx_drv_name = env.index_driver
    ows_index_driver = ows_index_driver_by_name(idx_drv_name)
    if ows_index_driver is None:
        raise ConfigException(f"ODC Environment {env._name} uses ODC index driver {env.index_driver} which is "
                              f"not (yet) supported by OWS.")
    return ows_index_driver.ows_index()
