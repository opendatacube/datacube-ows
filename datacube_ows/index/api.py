# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import dataclasses
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable
from datetime import date, datetime
from typing import Any, Literal, NamedTuple, TypeAlias, Union
from uuid import UUID

from datacube import Datacube
from datacube.index.abstract import AbstractIndex
from datacube.model import Dataset, Product
from odc.geo.crs import CRS
from odc.geo.geom import Geometry, polygon

from datacube_ows.config_utils import CFG_DICT, ConfigException

TYPE_CHECKING = False
if TYPE_CHECKING:
    from datacube_ows.ows_configuration import OWSNamedLayer


class AbortRun(Exception):
    pass


class InsufficientDbPrivileges(AbortRun):
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


DateOrDateTime: TypeAlias = datetime | date
TimeSearchTerm: TypeAlias = (
    tuple[datetime, datetime] | tuple[date, date] | DateOrDateTime
)


class CoordRange(NamedTuple):
    min: float
    max: float


class LayerExtent:
    def __init__(
        self,
        lat: CoordRange,
        lon: CoordRange,
        times: list[DateOrDateTime],
        bboxes: CFG_DICT,
    ) -> None:
        self.lat = lat
        self.lon = lon
        self.times = times
        self.start_time = times[0]
        self.end_time = times[-1]
        self.time_set = set(times)
        self.bboxes = bboxes


class OWSAbstractIndex(ABC):
    name: str = ""

    # method to check if we are in a user group
    # N.B. Subclasses may add additional groups to the Literal as required.
    @abstractmethod
    def _check_perms(self, dc: Datacube, group: Literal["admin"]) -> None: ...

    # method to check database access (for ping op) (requires odc "user" perms)
    @abstractmethod
    def check_db_access(self, dc: Datacube) -> bool: ...

    # method to delete obsolete schemas etc. (requires odc "admin" perms)
    @abstractmethod
    def cleanup_schema(self, dc: Datacube): ...

    # Schema creation method (requires odc "admin" perms)
    @abstractmethod
    def create_schema(self, dc: Datacube): ...

    # Spatiotemporal index update method (e.g. refresh materialised views) (requires odc "manage" perms)
    @abstractmethod
    def update_geotemporal_index(self, dc: Datacube): ...

    # Range table update method (requires odc "manage" perms)
    @abstractmethod
    def create_range_entry(
        self, layer: "OWSNamedLayer", cache: dict[LayerSignature, list[str]]
    ) -> None: ...

    # Range table read method (requires odc "user" perms)
    @abstractmethod
    def get_ranges(self, layer: "OWSNamedLayer") -> LayerExtent | None: ...

    # Spatiotemporal search methods (requires odc "user" perms)
    @abstractmethod
    def ds_search(
        self,
        layer: "OWSNamedLayer",
        times: Iterable[TimeSearchTerm] | None = None,
        geom: Geometry | None = None,
        products: Iterable[Product] | None = None,
    ) -> Iterable[Dataset]: ...

    def dsid_search(
        self,
        layer: "OWSNamedLayer",
        times: Iterable[TimeSearchTerm] | None = None,
        geom: Geometry | None = None,
        products: Iterable[Product] | None = None,
    ) -> Iterable[UUID]:
        for ds in self.ds_search(layer, times, geom, products):
            yield ds.id

    def count(
        self,
        layer: "OWSNamedLayer",
        times: Iterable[TimeSearchTerm] | None = None,
        geom: Geometry | None = None,
        products: Iterable[Product] | None = None,
    ) -> int:
        return len(list(self.dsid_search(layer, times, geom, products)))

    def extent(
        self,
        layer: "OWSNamedLayer",
        times: Iterable[TimeSearchTerm] | None = None,
        geom: Geometry | None = None,
        products: Iterable[Product] | None = None,
        crs: CRS | None = None,
    ) -> Geometry | None:
        geom = self._prep_geom(layer, geom)
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
                ext = ds_extent if ext is None else ext.union(ds_extent)
        if ext is not None and crs != CRS(layer.native_CRS):
            # Reproject to requested CRS if necessary
            return ext.to_crs(crs)
        return ext

    @staticmethod
    def _prep_geom(
        layer: "OWSNamedLayer", any_geom: Geometry | None
    ) -> Geometry | None:
        # Prepare a Geometry for geospatial search
        # Perhaps Core can be updated so this is not needed?
        if any_geom is None:
            # None?  Leave as None
            return None
        if any_geom.geom_type == "Point":
            # Point?  Expand to a polygon covering a single native pixel.
            any_geom = any_geom.to_crs(layer.native_CRS)
            x, y = any_geom.coords[0]
            delta_x, delta_y = layer.cfg_native_resolution
            return polygon(
                [
                    (x, y),
                    (x + delta_x, y),
                    (x + delta_x, y + delta_y),
                    (x, y + delta_y),
                    (x, y),
                ],
                crs=layer.native_CRS,
            )
        if any_geom.geom_type in ("MultiPoint", "LineString", "MultiLineString"):
            # Not a point, but not a polygon or multipolygon?  Expand to polygon by taking convex hull
            return any_geom.convex_hull
        # Return polygons and multipolygons as is.
        return any_geom


class OWSAbstractIndexDriver(ABC):
    @classmethod
    @abstractmethod
    def ows_index_class(cls) -> type[OWSAbstractIndex]: ...

    @classmethod
    @abstractmethod
    def ows_index(cls) -> OWSAbstractIndex: ...


def ows_index(odc: Datacube | AbstractIndex) -> OWSAbstractIndex:
    index = odc if isinstance(odc, AbstractIndex) else odc.index
    env = index.environment
    from datacube_ows.index.driver import ows_index_driver_by_name

    idx_drv_name = (
        "postgres" if env.index_driver in ("default", "legacy") else env.index_driver
    )
    ows_index_driver = ows_index_driver_by_name(idx_drv_name)
    if ows_index_driver is None:
        raise ConfigException(
            f"ODC Environment {env._name} uses ODC index driver {env.index_driver} which is "
            "not (yet) supported by OWS."
        )
    return ows_index_driver.ows_index()


def check_perms(
    group: Literal["admin", "manage"],
) -> Callable[[Callable], Callable]:
    def outer(f: Callable) -> Callable:
        def inner(
            instance, dcl: Union[Datacube, "OWSNamedLayer"], *args, **kwargs
        ) -> Any:
            from datacube_ows.ows_configuration import OWSNamedLayer

            if isinstance(dcl, OWSNamedLayer):
                dc = dcl.dc
            elif isinstance(dcl, Datacube):
                dc = dcl
            else:
                raise TypeError("Expected Datacube or OWSNamedLayer")
            instance._check_perms(dc, group)
            return f(instance, dcl, *args, **kwargs)

        return inner

    return outer
