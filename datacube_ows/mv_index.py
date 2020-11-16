from enum import Enum
import json

from geoalchemy2 import Geometry
from datacube.utils.geometry import Geometry as ODCGeom
from sqlalchemy import MetaData, Table, select, or_, Column, SMALLINT, text
from psycopg2.extras import DateTimeTZRange
from sqlalchemy.dialects.postgresql import UUID, TSTZRANGE
from sqlalchemy.sql.functions import count, func

def get_sqlalc_engine(index):
    # pylint: disable=protected-access
    return index._db._engine

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
    DATASETS: return list of ODC dataset objects
    COUNT: return a count of matching datasets
    EXTENT: return full extent of query as a Geometry
    """
    ALL = 0
    IDS = 1
    COUNT = 2
    EXTENT = 3
    DATASETS = 4

    def sel(self, stv):
        if self == self.ALL:
            return [stv]
        if self == self.IDS or self == self.DATASETS:
            return [stv.c.id]
        if self == self.COUNT:
            return [count(stv.c.id)]
        if self == self.EXTENT:
            return [text("ST_AsGeoJSON(ST_Union(spatial_extent))")]
        assert False

def mv_search_datasets(index,
                       sel=MVSelectOpts.IDS,
                       times=None,
                       layer=None,
                       geom=None,
                       mask=False,
                       resource_limited=False):
    """
    Perform a dataset query via the space_time_view

    :param layer: A ows_configuration.OWSNamedLayer object (single or multiproduct)
    :param index: A datacube index (required)

    :param sel: Selection mode - a MVSelectOpts enum. Defaults to IDS.
    :param times: A list of pairs of datetimes (with time zone)
    :param geom: A datacube.utils.geometry.Geometry object
    :param mask: Bool, if true use the flags product of layer
    :param resource_limited: Bool, if true use low-res summary products

    :return: See MVSelectOpts doc
    """
    engine = get_sqlalc_engine(index)
    stv = st_view
    if layer is None:
        raise Exception("Must filter by product/layer")
    if mask and resource_limited and layer.pq_low_res_products:
        prod_ids = [p.id for p in layer.pq_low_res_products]
    elif mask:
        prod_ids = [p.id for p in layer.pq_products]
    elif resource_limited and layer.low_res_products:
        prod_ids = [p.id for p in layer.low_res_products]
    else:
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
    orig_crs = None
    if geom is not None:
        orig_crs = geom.crs
        if str(geom.crs) != "EPSG:4326":
            geom = geom.to_crs("EPSG:4326")
        geom_js = json.dumps(geom.json)
        s = s.where(stv.c.spatial_extent.intersects(geom_js))
    # print(s) # Print SQL Statement
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
                if geojson is None:
                    return None
                uniongeom = ODCGeom(json.loads(geojson), crs="EPSG:4326")
                if geom:
                    intersect = uniongeom.intersection(geom)
                    if orig_crs and orig_crs != "EPSG:4326":
                        intersect = intersect.to_crs(orig_crs)
                else:
                    intersect = uniongeom
                return intersect
    if sel == MVSelectOpts.DATASETS:
        ids = [r[0] for r in conn.execute(s)]
        return index.datasets.bulk_get(ids)
    assert False