# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

#pylint: skip-file

import math
from datetime import datetime, timedelta, timezone

import datacube
from psycopg2.extras import Json

from datacube_ows.ogc_utils import NoTimezoneException, tz_for_coord
from datacube_ows.ows_configuration import get_config
from datacube_ows.utils import get_sqlconn


def get_crsids(cfg=None):
    if not cfg:
        cfg = get_config()
    return cfg.internal_CRSs.keys()


def get_crses(cfg=None):
    return {crsid: datacube.utils.geometry.CRS(crsid) for crsid in get_crsids(cfg)}


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
    print("Merging multiproduct ranges for %s (ODC products: %s)" % (
        product.name,
        repr(product.product_names)
    ))
    conn = get_sqlconn(dc)
    prodids = [p.id for p in product.products]
    wms_name = product.name

    if all(
            not datasets_exist(dc, p_name)
            for p_name in product.product_names
    ):
        print("Could not find datasets for any product in multiproduct: ", product.name)
        conn.close()
        print("Done")
        return

    txn = conn.begin()
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
        SET lat_min = subq.lat_min,
            lat_max = subq.lat_max,
            lon_min = subq.lon_min,
            lon_max = subq.lon_max
        FROM (
            select min(lat_min) as lat_min,
                   max(lat_max) as lat_max,
                   min(lon_min) as lon_min,
                   max(lon_max) as lon_max
            from wms.product_ranges
            where id = ANY (%(p_prodids)s)
        ) as subq
        WHERE wms_product_name = %(p_id)s
        """,
                 {"p_id": wms_name, "p_prodids": prodids})

    # Create sorted list of dates
    results = conn.execute(
        """
        SELECT dates
        FROM   wms.product_ranges
        WHERE  id  = ANY (%(p_prodids)s)
        """, {"p_prodids": prodids}
    )
    dates = set()
    for r in results:
        for d in r[0]:
            dates.add(d)
    dates = sorted(dates)
    conn.execute("""
           UPDATE wms.multiproduct_ranges
           SET dates = %(dates)s
           WHERE wms_product_name= %(p_id)s
      """,
                 {
                     "dates": Json(dates),
                     "p_id": wms_name
                 }
    )

    # calculate bounding boxes
    results = list(conn.execute("""
        SELECT lat_min,lat_max,lon_min,lon_max
        FROM wms.multiproduct_ranges
        WHERE wms_product_name=%(p_id)s
        """,
        {"p_id": wms_name}))

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
                 Json({crsid: jsonise_bbox(box.to_crs(crs).boundingbox) for crsid, crs in get_crses(cfg).items()}),
                 wms_name
    )

    txn.commit()
    conn.close()
    return


def create_range_entry(dc, product, crses, summary_product=False):
  print("Updating range for ODC product %s..." % product.name)
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
      SET lat_min = st_ymin(subq.bbox),
          lat_max = st_ymax(subq.bbox),
          lon_min = st_xmin(subq.bbox),
          lon_max = st_xmax(subq.bbox)
      FROM (
        SELECT st_extent(stv.spatial_extent) as bbox
        FROM public.space_time_view stv
        WHERE stv.dataset_type_ref = %(p_id)s
      ) as subq
      WHERE pr.id = %(p_id)s
      """,
      {"p_id": prodid})

  # Set default timezone
  conn.execute("""
    set timezone to 'Etc/UTC'
  """)


  if summary_product:
      # Loop over dates
      dates = set()

      results = conn.execute(
          """
          select
                array_agg(temporal_extent)
          from public.space_time_view
          WHERE dataset_type_ref = %(p_id)s
          """,
          {"p_id": prodid}
      )
      for result in results:
          for dat_ran in result[0]:
              dates.add(dat_ran.lower)

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
      # Loop over dates
      dates = set()

      results = conn.execute(
          """
          select
                lower(temporal_extent), upper(temporal_extent),
                ST_X(ST_Centroid(spatial_extent)),
                ST_Y(ST_Centroid(spatial_extent))
          from public.space_time_view
          WHERE dataset_type_ref = %(p_id)s
          """ %
          {"p_id": prodid}
      )
      for result in results:
          dt1, dt2, lon, lat = result
          try:
              tz = tz_for_coord(lon, lat)
          except NoTimezoneException:
              offset = round(lon / 15.0)
              tz = timezone(timedelta(hours=offset))
          dates.add(dt1.astimezone(tz).date())
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

  # calculate bounding boxes
  results = list(conn.execute("""
    SELECT lat_min,lat_max,lon_min,lon_max
    FROM wms.product_ranges
    WHERE id=%(p_id)s
    """,
      {"p_id": prodid}))

  r = results[0]

  epsg4326 = datacube.utils.geometry.CRS("EPSG:4326")
  box = datacube.utils.geometry.box(
    float(r[2]),
    float(r[0]),
    float(r[3]),
    float(r[1]),
    epsg4326)

  all_bboxes = bbox_projections(box, crses)

  conn.execute("""
    UPDATE wms.product_ranges
    SET bboxes = %(bbox)s::jsonb
    WHERE id=%(p_id)s
    """, {
    "bbox": Json(all_bboxes),
    "p_id": product.id})

  txn.commit()
  conn.close()


def bbox_projections(starting_box, crses):
   result = {}
   for crsid, crs in crses.items():
       if crs.valid_region is not None:
           clipped_crs_region = (starting_box & crs.valid_region)
           if clipped_crs_region.wkt == 'POLYGON EMPTY':
               continue
           clipped_crs_bbox = clipped_crs_region.to_crs(crs).boundingbox
       else:
           clipped_crs_bbox = None
       if clipped_crs_bbox is not None:
           result[crsid] = jsonise_bbox(clipped_crs_bbox)
       else:
           projbbox = starting_box.to_crs(crs).boundingbox
           result[crsid] = sanitise_bbox(projbbox)
   return result


def sanitise_bbox(bbox):
    def sanitise_coordinate(coord, fallback):
        return coord if math.isfinite(coord) else fallback
    return {
        "top": sanitise_coordinate(bbox.top, float("9.999999999e99")),
        "bottom": sanitise_coordinate(bbox.bottom, float("-9.999999999e99")),
        "left": sanitise_coordinate(bbox.left, float("-9.999999999e99")),
        "right": sanitise_coordinate(bbox.right, float("9.999999999e99")),
    }


def datasets_exist(dc, product_name):
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


def add_ranges(dc, product_names, summary=False, merge_only=False):
    odc_products = {}
    ows_multiproducts = []
    errors = False
    for pname in product_names:
        dc_product = None
        ows_product = get_config().product_index.get(pname)
        if not ows_product:
            ows_product = get_config().native_product_index.get(pname)
        if ows_product:
            for dc_pname in ows_product.product_names:
                if dc_pname in odc_products:
                    odc_products[dc_pname]["ows"].append(ows_product)
                else:
                    odc_products[dc_pname] = {"ows": [ows_product]}
            print("OWS Layer %s maps to ODC Product(s): %s" % (
                ows_product.name,
                repr(ows_product.product_names)
            ))
            if ows_product.multi_product:
                ows_multiproducts.append(ows_product)
        if not ows_product:
            dc_product = dc.index.products.get_by_name(pname)
            if dc_product:
                print("ODC Layer: %s" % pname)
                if pname in odc_products:
                    odc_products[pname]["ows"].append(None)
                else:
                    odc_products[pname] = {"ows": [None]}
            else:
                print("Unrecognised product name:", pname)
                errors = True
                continue

    if ows_multiproducts and merge_only:
        print("Merge-only: Skipping range update of products:", repr(list(odc_products.keys())))
    else:
        for pname, ows_prods in odc_products.items():
            dc_product = dc.index.products.get_by_name(pname)
            if dc_product is None:
                print("Could not find ODC product:", pname)
                errors = True
            elif datasets_exist(dc, dc_product.name):
                prod_summary = summary
                for ows_prod in ows_prods["ows"]:
                    if ows_prod:
                        prod_summary = not ows_prod.is_raw_time_res
                        break
                create_range_entry(dc, dc_product, get_crses(), prod_summary)
            else:
                print("Could not find any datasets for: ", pname)
    for mp in ows_multiproducts:
        create_multiprod_range_entry(dc, mp, get_crses())

    print("Done.")
    return errors

def get_ranges(dc, product, path=None, is_dc_product=False):
    cfg = product.global_cfg
    conn = get_sqlconn(dc)
    if not is_dc_product and product.multi_product:
        if path is not None:
            raise Exception("Combining subproducts and multiproducts is not yet supported")
        results = conn.execute("""
            SELECT *
            FROM wms.multiproduct_ranges
            WHERE wms_product_name=%s""",
                               product.name
                              )
    else:
        if is_dc_product:
            prod_id = product.id
        else:
            prod_id = product.product.id
        if path is not None:
            results = conn.execute("""
                SELECT *
                FROM wms.sub_product_ranges
                WHERE product_id=%s and sub_product_id=%s""",
                                   prod_id, path
                                  )
        else:
            results = conn.execute("""
                SELECT *
                FROM wms.product_ranges
                WHERE id=%s""",
                                   prod_id
                                  )
    for result in results:
        conn.close()
        times = [datetime.strptime(d, "%Y-%m-%d").date() for d in result["dates"] if d is not None]
        if not times:
            return None
        return {
            "lat": {
                "min": float(result["lat_min"]),
                "max": float(result["lat_max"]),
            },
            "lon": {
                "min": float(result["lon_min"]),
                "max": float(result["lon_max"]),
            },
            "times": times,
            "start_time": times[0],
            "end_time": times[-1],
            "time_set": set(times),
            "bboxes": cfg.alias_bboxes(result["bboxes"])
        }
    return None
