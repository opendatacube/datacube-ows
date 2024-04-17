# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import datetime
import json
from enum import Enum
from typing import Any, Iterable, Optional, Tuple, Union, cast

import pytz
from odc.geo.geom import Geometry as ODCGeom
from geoalchemy2 import Geometry
from psycopg2.extras import DateTimeTZRange
from sqlalchemy import (SMALLINT, Column, MetaData, Table, and_, or_, select,
                        text)
from sqlalchemy.dialects.postgresql import TSTZRANGE, UUID
from sqlalchemy.sql.functions import count, func

from datacube_ows.utils import default_to_utc


def get_sqlalc_engine(index: "datacube.index.Index") -> "sqlalchemy.engine.base.Engine":
    # pylint: disable=protected-access
    return index._db._engine


def get_st_view(meta: MetaData) -> Table:
    return Table('space_time_view', meta,
             Column('id', UUID()),
             Column('dataset_type_ref', SMALLINT()),
             Column('spatial_extent', Geometry(from_text='ST_GeomFromGeoJSON', name='geometry')),
             Column('temporal_extent', TSTZRANGE())
                 )
_meta = MetaData()
st_view = get_st_view(_meta)


class MVSelectOpts(Enum):
    """
    Enum for mv_search_datasets sel parameter.

    ALL: return all columns, select *, as result set
    IDS: return list of database_ids only.
    DATASETS: return list of ODC dataset objects
    COUNT: return a count of matching datasets
    EXTENT: return full extent of query result as a Geometry
    """
    ALL = 0
    IDS = 1
    COUNT = 2
    EXTENT = 3
    DATASETS = 4
    INVALID = 9999

    def sel(self, stv: Table) -> Iterable["sqlalchemy.sql.elements.ClauseElement"]:
        if self == self.ALL:
            return [stv]
        if self == self.IDS or self == self.DATASETS:
            return [stv.c.id]
        if self == self.COUNT:
            return [cast("sqlalchemy.sql.elements.ClauseElement", count(stv.c.id))]
        if self == self.EXTENT:
            return [text("ST_AsGeoJSON(ST_Union(spatial_extent))")]
        assert False

TimeSearchTerm = Union[
    Tuple[datetime.datetime, datetime.datetime],
    datetime.datetime,
]

def mv_search(index: "datacube.index.Index",
              sel: MVSelectOpts = MVSelectOpts.IDS,
              times: Optional[Iterable[TimeSearchTerm]] = None,
              geom: Optional[ODCGeom] = None,
              products: Optional[Iterable["datacube.model.DatasetType"]] = None) -> Union[
        Iterable[Iterable[Any]],
        Iterable[str],
        Iterable["datacube.model.Dataset"],
        int,
        None,
        ODCGeom]:
    """
    Perform a dataset query via the space_time_view

    :param products: An iterable of combinable products to search
    :param index: A datacube index (required)

    :param sel: Selection mode - a MVSelectOpts enum. Defaults to IDS.
    :param times: A list of pairs of datetimes (with time zone)
    :param geom: A odc.geo.geom.Geometry object

    :return: See MVSelectOpts doc
    """
    engine = get_sqlalc_engine(index)
    stv = st_view
    if products is None:
        raise Exception("Must filter by product/layer")
    prod_ids = [p.id for p in products]

    s = select(*sel.sel(stv)).where(stv.c.dataset_type_ref.in_(prod_ids))
    if times is not None:
        or_clauses = []
        for t in times:
            if isinstance(t, datetime.datetime):
                t = datetime.datetime(t.year, t.month, t.day, t.hour, t.minute, t.second)
                t = default_to_utc(t)
                if not t.tzinfo:
                    t = t.replace(tzinfo=pytz.utc)
                tmax = t + datetime.timedelta(seconds=1)
                or_clauses.append(
                    and_(
                        func.lower(stv.c.temporal_extent) >= t,
                        func.lower(stv.c.temporal_extent) < tmax,
                    )
                )
            elif isinstance(t, datetime.date):
                t = datetime.datetime(t.year, t.month, t.day, tzinfo=pytz.utc)
                tmax = t + datetime.timedelta(days=1)
                or_clauses.append(
                    and_(
                        func.lower(stv.c.temporal_extent) >= t,
                        func.lower(stv.c.temporal_extent) < tmax,
                    )
                )
            else:
                or_clauses.append(
                    stv.c.temporal_extent.op("&&")(DateTimeTZRange(*t))
                )
        s = s.where(or_(*or_clauses))
    orig_crs = None
    if geom is not None:
        orig_crs = geom.crs
        if str(geom.crs) != "EPSG:4326":
            geom = geom.to_crs("EPSG:4326")
        geom_js = json.dumps(geom.json)
        s = s.where(stv.c.spatial_extent.intersects(geom_js))
    # print(s) # Print SQL Statement
    with engine.connect() as conn:
        if sel == MVSelectOpts.ALL:
            return conn.execute(s)
        if sel == MVSelectOpts.IDS:
            return [r[0] for r in conn.execute(s)]
        if sel in (MVSelectOpts.COUNT, MVSelectOpts.EXTENT):
            for r in conn.execute(s):
                if sel == MVSelectOpts.COUNT:
                    return r[0]
                if sel == MVSelectOpts.EXTENT:
                    geojson = r[0]
                    if geojson is None:
                        return None
                    uniongeom = ODCGeom(json.loads(geojson), crs="EPSG:4326")
                    if geom:
                        intersect = uniongeom.intersection(geom)
                        if intersect.wkt == 'POLYGON EMPTY':
                            return None
                        if orig_crs and orig_crs != "EPSG:4326":
                            intersect = intersect.to_crs(orig_crs)
                    else:
                        intersect = uniongeom
                    return intersect
        if sel == MVSelectOpts.DATASETS:
            ids = [r[0] for r in conn.execute(s)]
            return index.datasets.bulk_get(ids)
