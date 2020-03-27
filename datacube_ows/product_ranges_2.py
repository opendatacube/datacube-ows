#pylint: skip-file

from __future__ import absolute_import, division, print_function

from datetime import datetime
import datacube

from datacube_ows.ows_configuration import get_config, OWSNamedLayer  # , get_layers, ProductLayerDef
from datacube_ows.ogc_utils import local_date
from psycopg2.extras import Json
from itertools import zip_longest
import json

from datacube_ows.utils import get_sqlconn


def get_crsids(cfg=None):
    if not cfg:
        cfg = get_config()
    return cfg.published_CRSs.keys()


def get_crses(cfg=None):
    return  {crsid: datacube.utils.geometry.CRS(crsid) for crsid in get_crsids(cfg)}


def jsonise_bbox(bbox):
    if isinstance(bbox, dict):
        return bbox
    else:
        return {
            "top": bbox.top,
            "bottom": bbox.bottom,
            "left": bbox.left,
            "right": bbox.right,
        }


def create_multiprod_range_entry(dc, product, crses):
    conn = get_sqlconn(dc)
    txn = conn.begin()
    if isinstance(product, dict):
        prodids = [p.id for p in product["products"]]
        wms_name = product["name"]
    else:
        prodids = [ p.id for p in product.products ]
        wms_name = product.name

    # Attempt to insert row
    conn.execute("""
        INSERT INTO wms.multiproduct_ranges
        (wms_product_name,lat_min,lat_max,lon_min,lon_max,dates,bboxes)
        VALUES
        (%(p_id)s, 0, 0, 0, 0, %(empty)s, %(empty)s)
        ON CONFLICT (wms_product_name) DO NOTHING
        """,
                 {"p_id": wms_name, "empty": Json("")})

    # Update extents
    conn.execute("""
        UPDATE wms.multiproduct_ranges
        SET (lat_min,lat_max,lon_min,lon_max) =
        (wms_get_min(%(p_prodids)s, 'lat'), wms_get_max(%(p_prodids)s, 'lat'), wms_get_min(%(p_prodids)s, 'lon'), wms_get_max(%(p_prodids)s, 'lon'))
        WHERE wms_product_name=%(p_id)s
        """,
                 {"p_id": wms_name, "p_prodids": prodids})

    # Create sorted list of dates
    conn.execute("""
        WITH sorted
        AS (SELECT to_jsonb(array_agg(dates.d))
            AS dates
            FROM (SELECT DISTINCT to_date(metadata::json->'extent'->>'center_dt', 'YYYY-MM-DD')
                  AS d
                  FROM agdc.dataset
                  WHERE dataset_type_ref = any (%(p_prodids)s)
                  AND archived IS NULL
                  ORDER BY d) dates)
        UPDATE wms.multiproduct_ranges
        SET dates=sorted.dates
        FROM sorted
        WHERE wms_product_name=%(p_id)s
        """,
                 {"p_id": wms_name, "p_prodids": prodids})

    # calculate bounding boxes
    results = list(conn.execute("""
        SELECT lat_min,lat_max,lon_min,lon_max
        FROM wms.multiproduct_ranges
        WHERE wms_product_name=%(p_id)s
        """,
        {"p_id": wms_name} ))

    r = results[0]

    epsg4326 = datacube.utils.geometry.CRS("EPSG:4326")
    box = datacube.utils.geometry.box(
        float(r[2]),
        float(r[0]),
        float(r[3]),
        float(r[1]),
        epsg4326)

    cfg = get_config()
    conn.execute("""
        UPDATE wms.multiproduct_ranges
        SET bboxes = %s::jsonb
        WHERE wms_product_name=%s
        """,
                 Json({ crsid: jsonise_bbox(box.to_crs(crs).boundingbox) for crsid, crs in get_crses(cfg).items() }),
                 wms_name
    )

    txn.commit()
    conn.close()
    return


def create_range_entry(dc, product, crses, summary_product=False):
  # NB. product is an ODC product
  conn = get_sqlconn(dc)
  txn = conn.begin()
  prodid = product.id

  # insert empty row if one does not already exist
  conn.execute("""
    INSERT INTO wms.product_ranges
    (id,lat_min,lat_max,lon_min,lon_max,dates,bboxes)
    VALUES
    (%(p_id)s, 0, 0, 0, 0, %(empty)s, %(empty)s)
    ON CONFLICT (id) DO NOTHING
    """,
    {"p_id": prodid, "empty": Json("")})


  # Update min/max lat/longs
  conn.execute(
    """
    UPDATE wms.product_ranges pr
    SET lat_min = st_ymin(st_extent(sv.spatial_extent)),
        lat_max = st_ymax(st_extent(sv.spatial_extent)),
        lon_min = st_xmin(st_extent(sv.spatial_extent)),
        lon_max = st_xmax(st_extent(sv.spatial_extent))
    FROM public.space_view sv
    WHERE sv.dataset_type_ref=%(p_id)s
    """,
    {"p_id": prodid})

  # Set default timezone
  conn.execute("""
    set timezone to 'Etc/UTC'
  """)

  # Experimental shit

  results = conn.execute(
      """
      select  dataset_type_ref,
            ST_XMin(st_extent(spatial_extent)),
            ST_XMax(st_extent(spatial_extent)),
            ST_YMin(st_extent(spatial_extent)),
            ST_YMax(st_extent(spatial_extent)),
            array_agg(temporal_extent)
      from space_time_view 
      group by dataset_type_ref
      """
  )

  for result in results:
      print("Oo-ah!")

  conn.rollback()
  quit()

  if summary_product:
      # Loop over dates
      dates = set()

      for result in conn.execute("""
        SELECT DISTINCT cast(metadata -> 'extent' ->> 'from_dt' as date) as dt
        FROM agdc.dataset
        WHERE dataset_type_ref = %(p_id)s
        AND archived IS NULL
        ORDER BY dt 
      """,
                                 {"p_id": prodid}):
          dates.add(result[0])
      dates = sorted(dates)

      conn.execute("""
           UPDATE wms.product_ranges
           SET dates = %(dates)s
           WHERE id= %(p_id)s
      """,
                   {
                       "dates": Json([t.strftime("%Y-%m-%d") for t in dates]),
                       "p_id": prodid
                   }
      )
  else:
      # Create sorted list of dates
      conn.execute("""
        WITH sorted
        AS (SELECT to_jsonb(array_agg(dates.d))
            AS dates
            FROM (SELECT DISTINCT
                   date(cast(metadata -> 'extent' ->> 'center_dt' as timestamp) AT TIME ZONE 'UTC' +
                    (least(to_number(metadata -> 'extent' -> 'coord' -> 'll' ->> 'lon', '9999.9999999999999999999999999999999999'),
                    to_number(metadata -> 'extent' -> 'coord' -> 'ul' ->> 'lon', '9999.9999999999999999999999999999999999')) +
                    greatest(to_number(metadata -> 'extent' -> 'coord' -> 'lr' ->> 'lon', '9999.9999999999999999999999999999999999'),
                    to_number(metadata -> 'extent' -> 'coord' -> 'ur' ->> 'lon', '9999.9999999999999999999999999999999999'))) / 30.0 * interval '1 hour')
                  AS d
                  FROM agdc.dataset
                  WHERE dataset_type_ref=%(p_id)s
                  AND archived IS NULL
                  ORDER BY d) dates)
        UPDATE wms.product_ranges
        SET dates=sorted.dates
        FROM sorted
        WHERE id=%(p_id)s
        """,
        {"p_id": prodid})

  # calculate bounding boxes
  results = list(conn.execute("""
    SELECT lat_min,lat_max,lon_min,lon_max
    FROM wms.product_ranges
    WHERE id=%s
    """,
    prodid))

  r = results[0]

  epsg4326 = datacube.utils.geometry.CRS("EPSG:4326")
  box = datacube.utils.geometry.box(
    float(r[2]),
    float(r[0]),
    float(r[3]),
    float(r[1]),
    epsg4326)

  conn.execute("""
    UPDATE wms.product_ranges
    SET bboxes = %s::jsonb
    WHERE id=%s
    """,
    Json(
      {crsid: {"top": box.to_crs(crs).boundingbox.top,
               "bottom": box.to_crs(crs).boundingbox.bottom,
               "left": box.to_crs(crs).boundingbox.left,
               "right": box.to_crs(crs).boundingbox.right}
        for crsid, crs in crses.items()
       }
    ),
    product.id)

  txn.commit()
  conn.close()


def check_datasets_exist(dc, product_name):
  conn = get_sqlconn(dc)

  results = conn.execute("""
    SELECT COUNT(*)
    FROM agdc.dataset ds, agdc.dataset_type p
    WHERE ds.archived IS NULL
    AND ds.dataset_type_ref = p.id
    AND p.name = %s""",
    product_name)

  conn.close()

  return list(results)[0][0] > 0


def add_product_range(dc, product):
    if isinstance(product, str):
        product_name = product
        dc_product = dc.index.products.get_by_name(product)
    else:
        product_name = product.name
        dc_product = product

    ows_product = get_config().native_product_index.get(product_name)
    if ows_product:
        summary_product = not ows_product.is_raw_time_res
    else:
        summary_product = False

    assert dc_product is not None

    if check_datasets_exist(dc, product_name):
        create_range_entry(dc, dc_product, get_crses(), summary_product)
    else:
        print("Could not find any datasets for: ", product_name)


def add_multiproduct_range(dc, product, follow_dependencies=True):
    if isinstance(product, str):
        product = get_config().product_index.get(product)

    assert product is not None
    assert product.multi_product

    if follow_dependencies:
        for product_name in product.product_names:
            dc_prod = dc.index.products.get_by_name(product_name)
            if not check_datasets_exist(dc, product_name):
                print("Could not find any datasets for: ", product_name)
            else:
                add_product_range(dc, product_name)

    # Actually merge and store!
    create_multiprod_range_entry(dc, product, get_crses())


def add_all(dc):
    multi_products = set()
    for product_cfg in get_config().product_index.values():
        product_name = product_cfg.product_name
        if product_cfg.multi_product:
            multi_products.add(product_cfg)
        else:
            print("Adding range for:", product_name)
            add_product_range(dc, product_name)

    for p in multi_products:
        print("Adding multiproduct range for:", p.name)
        add_multiproduct_range(dc, p, follow_dependencies=False)

