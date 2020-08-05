from enum import Enum
import json

from geoalchemy2 import Geometry
from datacube.utils.geometry import Geometry as ODCGeom
from sqlalchemy import MetaData, Table, select, or_, Column, SMALLINT, text
from psycopg2.extras import DateTimeTZRange
from sqlalchemy.dialects.postgresql import UUID, TSTZRANGE
from sqlalchemy.sql.functions import count, func

def get_sqlalc_engine(dc=None, index=None, engine=None):
    if engine:
        return engine
    if index:
        return index._db._engine
    if dc:
        return dc.index._db._engine
    raise NotImplementedError("Give me something to work with here")

def get_st_view(meta):
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
    COUNT: return a count of matching datasets
    EXTENT: return full extent of query as a Geometry
    """
    ALL = 0
    IDS = 1
    COUNT = 2
    EXTENT = 3

    def sel(self, stv):
        if self == self.ALL:
            return [stv]
        if self == self.IDS:
            return [stv.c.id]
        if self == self.COUNT:
            return [count(stv.c.id)]
        if self == self.EXTENT:
            return [text("ST_AsGeoJSON(ST_Union(spatial_extent))")]
        assert False

def mv_search_datasets(dc=None, index=None, engine=None,
                       sel=MVSelectOpts.IDS,
                       times=None,
                       layer=None,
                       geom=None):
    """
    Perform a dataset query via the space_time_view

    :param layer:

    A ows_configuration.OWSNamedLayer object (single or multiproduct)

    You must supply one of
    :param dc: A Datacube object
    :param index: A datacube index
    :param engine: An SQLAlchemy engine
    :param sel: Selection mode - a MVSelectOpts enum. Defaults to IDS.
    :param times: A list of pairs of datetimes (with time zone)
    :param geom: A datacube.utils.geometry.Geometry object
    :return: See MVSelectOpts doc
    """
    engine = get_sqlalc_engine(dc=dc, index=index, engine=engine)
    stv = st_view
    if layer is None:
        raise Exception("Must filter by product/layer")
    prod_ids = [p.id for p in layer.products]
    s = select(sel.sel(stv)).where(stv.c.dataset_type_ref.in_(prod_ids))
    if times is not None:
        s = s.where(
            or_(
                *[
                    stv.c.temporal_extent.op("&&")(DateTimeTZRange(*t))
                    for t in times
                ]
            )
        )
    if geom is not None:
        geom_js = json.dumps(geom.json)
        print(geom_js)
        s = s.where(stv.c.spatial_extent.intersects(geom_js))
    print(s) # Print SQL Statement
    conn = engine.connect()
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
                print("Output:", geojson)
                return ODCGeom(json.loads(geojson))
                # return ODCGeom(r[0])

    assert False