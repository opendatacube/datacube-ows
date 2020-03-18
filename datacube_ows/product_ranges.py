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

DEFAULT_GEOJSON = json.loads('''{
"type": "Polygon",
"coordinates": [
  [
    [
      110.91796875,
      -43.96119063892024
    ],
    [
      158.203125,
      -43.96119063892024
    ],
    [
      158.203125,
      -10.660607953624762
    ],
    [
      110.91796875,
      -10.660607953624762
    ],
    [
      110.91796875,
      -43.96119063892024
    ]
  ]
]
}''')

DEFAULT_GEOJSON_CRS = datacube.utils.geometry.CRS('EPSG:4326')

def accum_min(a, b):
    if a is None:
        return b
    elif b is None:
        return a
    else:
        return min(a, b)


def accum_max(a, b):
    if a is None:
        return b
    elif b is None:
        return a
    else:
        return max(a, b)


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

def determine_product_ranges(dc, dc_product, extractor, summary_dataset=False):
    # pylint: disable=too-many-locals, too-many-branches, too-many-statements, protected-access
    start = datetime.now()
    print("Product: ", dc_product.name)
    r = {
        "lat": {
            "min": None,
            "max": None
        },
        "lon": {
            "min": None,
            "max": None
        },
    }
    sub_r = {}
    time_set = set()
    cfg = get_config()
    print ("OK, Let's do it")
    crsids = get_crsids(cfg)
    extents = {crsid: None for crsid in crsids}
    crses = get_crses(cfg)
    ds_count = 0
    for ds in dc.find_datasets(product=dc_product.name):
        print("Processing a dataset", ds.id)
        if summary_dataset:
            ds_time = ds.metadata.time[0]
        else:
            ds_time = local_date(ds)
        if extractor is not None:
            path = extractor(ds)
            if path not in sub_r:
                sub_r[path] = {
                    "lat": {
                        "min": None,
                        "max": None,
                    },
                    "lon": {
                        "min": None,
                        "max": None,
                    },
                    "time_set": set(),
                    "extents": {crsid: None for crsid in crsids}
                }
            sub_r[path]["lat"]["min"] = accum_min(sub_r[path]["lat"]["min"], ds.metadata.lat.begin)
            sub_r[path]["lat"]["max"] = accum_max(sub_r[path]["lat"]["max"], ds.metadata.lat.end)
            sub_r[path]["lon"]["min"] = accum_min(sub_r[path]["lon"]["min"], ds.metadata.lon.begin)
            sub_r[path]["lon"]["max"] = accum_max(sub_r[path]["lon"]["max"], ds.metadata.lon.end)
        else:
            path = None

        r["lat"]["min"] = accum_min(r["lat"]["min"], ds.metadata.lat.begin)
        r["lat"]["max"] = accum_max(r["lat"]["max"], ds.metadata.lat.end)
        r["lon"]["min"] = accum_min(r["lon"]["min"], ds.metadata.lon.begin)
        r["lon"]["max"] = accum_max(r["lon"]["max"], ds.metadata.lon.end)

        time_set.add(ds_time)
        if path is not None:
            sub_r[path]["time_set"].add(ds_time)

        for crsid in crsids:
            print("Working with CRS", crsid)
            crs = crses[crsid]
            ext = ds.extent
            if ext.crs != crs:
                ext = ext.to_crs(crs)
            cvx_ext = ext.convex_hull
            if cvx_ext != ext:
                print("INFO: Dataset", ds.id, "CRS", crsid, "extent is not convex.")
            if extents[crsid] is None:
                extents[crsid] = cvx_ext
            else:
                if not extents[crsid].is_valid:
                    print("WARNING: Extent Union for", ds.id, "CRS", crsid, "is not valid")
                if not cvx_ext.is_valid:
                    print("WARNING: Extent for CRS", crsid, "is not valid")
                union = extents[crsid].union(cvx_ext)
                if union._geom is not None:
                    extents[crsid] = union
                else:
                    print("WARNING: Dataset", ds.id, "CRS", crsid, "union topology exception, ignoring union")
            if path is not None:
                if sub_r[path]["extents"][crsid] is None:
                    sub_r[path]["extents"][crsid] = cvx_ext
                else:
                    sub_r[path]["extents"][crsid] = sub_r[path]["extents"][crsid].union(cvx_ext)
        ds_count += 1

    if ds_count > 0:
        r["times"] = sorted(time_set)
        r["time_set"] = time_set
        r["bboxes"] = { crsid: jsonise_bbox(extents[crsid].boundingbox) for crsid in crsids }
        print("LATS: ", r["lat"], " LONS: ", r["lon"])
        if extractor is not None:
            for path in sub_r.keys():
                sub_r[path]["times"] = sorted(sub_r[path]["time_set"])
                sub_r[path]["bboxes"] = {crsid: jsonise_bbox(sub_r[path]["extents"][crsid].boundingbox) for crsid in crsids}
                del sub_r[path]["extents"]
            r["sub_products"] = sub_r
        end = datetime.now()
        print("Scanned %d datasets in %d seconds" % (ds_count, (end - start).seconds))
    else:
        end = datetime.now()
        print("No datasets indexed. Nothing to do and didn't do it in %s seconds" % (end - start).seconds)
    return r


def get_ids_in_db(conn):
    results = conn.execute("select id from wms.product_ranges")
    ids = [r["id"] for r in results]
    return ids


def get_product_paths_in_db(conn, dc_product):
    results = conn.execute("""
        SELECT sub_product_id
        FROM wms.sub_product_ranges
        WHERE product_id = %s
        ORDER BY product_id, sub_product_id""",
                           dc_product.id
                           )
    ids = { r["sub_product_id"] for r in results }
    return ids


def rng_update(conn, rng, product, path=None):
    # pylint: disable=bad-continuation
    if isinstance(product, OWSNamedLayer):
        if product.multi_product:
            assert path is None
            conn.execute("""
            UPDATE wms.multiproduct_ranges
            SET
                  lat_min=%s,
                  lat_max=%s,
                  lon_min=%s,
                  lon_max=%s,   
                  dates=%s,
                  bboxes=%s
            WHERE wms_product_name=%s
            """,
                         rng["lat"]["min"],
                         rng["lat"]["max"],
                         rng["lon"]["min"],
                         rng["lon"]["max"],
                         Json([t.strftime("%Y-%m-%d") for t in rng["times"]]),
                         Json({crsid: jsonise_bbox(bbox) for crsid, bbox in rng["bboxes"].items() }),
                         product.name)
            return
        product = product.product
    if path is not None:
        conn.execute("""
            UPDATE wms.sub_product_ranges
            SET
                  lat_min=%s,
                  lat_max=%s,
                  lon_min=%s,
                  lon_max=%s,   
                  dates=%s,
                  bboxes=%s
            WHERE product_id=%s
            AND   sub_product_id=%s
                 """,
                     rng["lat"]["min"],
                     rng["lat"]["max"],
                     rng["lon"]["min"],
                     rng["lon"]["max"],

                     Json([t.strftime("%Y-%m-%d") for t in rng["times"]]),
                     Json({crsid: jsonise_bbox(bbox) for crsid, bbox in rng["bboxes"].items() }),
                     product.id,
                     path
                     )
    else:
        conn.execute("""
            UPDATE wms.product_ranges
            SET
                  lat_min=%s,
                  lat_max=%s,
                  lon_min=%s,
                  lon_max=%s,   
                  dates=%s,
                  bboxes=%s
            WHERE id=%s
                 """,
                 rng["lat"]["min"],
                 rng["lat"]["max"],
                 rng["lon"]["min"],
                 rng["lon"]["max"],

                 Json([t.strftime("%Y-%m-%d") for t in rng["times"]]),
                 Json({crsid: jsonise_bbox(bbox) for crsid, bbox in rng["bboxes"].items() }),
                     product.id
                    )


def rng_insert(conn, rng, product, path=None):
    # pylint: disable=bad-continuation
    if isinstance(product, OWSNamedLayer):
        if product.multi_product:
            conn.execute("""
                INSERT into wms.multiproduct_ranges
                    (wms_product_name,  lat_min,lat_max,lon_min,lon_max,   dates,bboxes)
                VALUES
                    (%s, %s,%s,%s,%s,    %s,%s)
                     """,
                     product.name,

                     rng["lat"]["min"],
                     rng["lat"]["max"],
                     rng["lon"]["min"],
                     rng["lon"]["max"],

                     Json([t.strftime("%Y-%m-%d") for t in rng["times"]]),
                     Json({crsid: jsonise_bbox(bbox) for crsid, bbox in rng["bboxes"].items() }),
                     )
            return
        product = product.product
    if path is not None:
        conn.execute("""
                INSERT into wms.sub_product_ranges
                    (product_id, sub_product_id,  lat_min,lat_max,lon_min,lon_max,   dates,bboxes)
                VALUES
                    (%s,%s,   %s,%s,%s,%s,    %s,%s)
                     """,
                     product.id,
                     path,

                     rng["lat"]["min"],
                     rng["lat"]["max"],
                     rng["lon"]["min"],
                     rng["lon"]["max"],

                     Json([t.strftime("%Y-%m-%d") for t in rng["times"]]),
                     Json({crsid: jsonise_bbox(bbox) for crsid, bbox in rng["bboxes"].items() }),
                     )
    else:
        conn.execute("""
                INSERT into wms.product_ranges
                    (id,   lat_min,lat_max,lon_min,lon_max,   dates,bboxes)
                VALUES
                    (%s,   %s,%s,%s,%s,    %s,%s)
                     """,
                     product.id,

                     rng["lat"]["min"],
                     rng["lat"]["max"],
                     rng["lon"]["min"],
                     rng["lon"]["max"],

                     Json([t.strftime("%Y-%m-%d") for t in rng["times"]]),
                     Json({crsid: jsonise_bbox(bbox) for crsid, bbox in rng["bboxes"].items() }),
                    )


def ranges_equal(r1, rdb):
    # pylint: disable=too-many-branches
    for coord in ("lat", "lon"):
        for ext in ("max", "min"):
            if abs(r1[coord][ext] - rdb[coord][ext]) > 1e-12:
                return False
    if len(r1["times"]) != len(rdb["times"]):
        return False
    for t1, t2 in zip_longest(r1["times"], rdb["times"]):
        if t1 != t2:
            return False
    if len(r1["bboxes"]) != len(rdb["bboxes"]):
        return False
    try:
        for cs in r1["bboxes"].keys():
            bb1 = r1["bboxes"][cs]
            bb2 = rdb["bboxes"][cs]
            if abs(bb1["top"] - float(bb2["top"])) > 1e-12:
                return False
            if abs(bb1["bottom"] - float(bb2["bottom"])) > 1e-12:
                return False
            if abs(bb1["left"] - float(bb2["left"])) > 1e-12:
                return False
            if abs(bb1["right"] - float(bb2["right"])) > 1e-12:
                return False
    except KeyError:
        return False
    return True


def update_range(dc, product, multi=False, follow_dependencies=True):
    if multi:
        product = get_config().product_index.get(product)
    else:
        product = dc.index.products.get_by_name(product)

    if product is None:
        raise Exception("Requested product not found.")

    if multi:
        return update_multi_range(dc, product, follow_dependencies=follow_dependencies)
    else:
        return update_single_range(dc, product)


def update_single_range(dc, product):
    if isinstance(product, OWSNamedLayer):
        assert not product.multi_product
        dc_product = product.product
        extractor  = product.sub_product_extractor
        summary = not product.is_raw_time_res
    else:
        dc_product = product
        extractor = None
        product = get_config().native_product_index.get(product.name)
        if product:
            summary = not product.is_raw_time_res
        else:
            summary = False

    product_range = determine_product_ranges(dc, dc_product, extractor, summary)
    conn = get_sqlconn(dc)
    txn = conn.begin()
    db_range = get_ranges(dc, dc_product, is_dc_product=True)
    subids_in_db = get_product_paths_in_db(conn, dc_product)

    ok = 0
    ins = 0
    upd = 0
    if db_range:
        if ranges_equal(product_range, db_range):
            print("Ranges equal, not updating")
            ok = 1
        else:
            rng_update(conn, product_range, dc_product)
            print("Updating range")
            upd = 1
    else:
        rng_insert(conn, product_range, dc_product)
        print("Inserting new range")
        ins = 1

    sok = 0
    sins = 0
    supd = 0
    if "sub_products" in product_range:
        for path, subr in product_range["sub_products"].items():
            if path in subids_in_db:
                db_range = get_ranges(dc, dc_product, path, is_dc_product=True)
                if ranges_equal(subr, db_range):
                    sok += 1
                else:
                    rng_update(conn, subr, dc_product, path)
                    supd += 1
            else:
                rng_insert(conn, subr, dc_product, path)
                sins += 1
    txn.commit()
    conn.close()

    return (ok, upd, ins, sok, supd, sins)


def update_multi_range(dc, product, follow_dependencies=True):
    assert product.multi_product

    if follow_dependencies:
        for dc_product in product.products:
            update_single_range(dc, dc_product)

    mp_ranges = None
    for p in product.products:
        mp_ranges = merge_ranges(mp_ranges, get_ranges(dc, p, is_dc_product=True))


    db_range = get_ranges(dc, product)
    conn = get_sqlconn(dc)
    txn = conn.begin()

    ok = 0
    ins = 0
    upd = 0
    if db_range:
        if ranges_equal(mp_ranges, db_range):
            print("Ranges equal, not updating")
            ok = 1
        else:
            rng_update(conn, mp_ranges, product)
            print("Updating range")
            upd = 1
    else:
        rng_insert(conn, mp_ranges, product)
        print("Inserting new range")
        ins = 1


    txn.commit()
    conn.close()
    return (ok, upd, ins)


def update_all_ranges(dc):
    i = 0
    u = 0
    p = 0
    si = 0
    su = 0
    sp = 0
    mi = 0
    mu = 0
    mp = 0

    multiproducts = set()

    for prod in get_config().product_index.values():
        if prod.multi_product:
            multiproducts.add(prod)
        else:
            stats = update_single_range(dc, prod)
            p  += stats[0]
            u  += stats[1]
            i  += stats[2]
            sp += stats[3]
            su += stats[4]
            si += stats[5]

    for mprod in multiproducts:
        stats = update_multi_range(dc, mprod, follow_dependencies=False)
        mp += stats[0]
        mu += stats[1]
        mi += stats[2]

    return p, u, i, sp, su, si, mp, mu, mi


def get_ranges(dc, product, path=None, is_dc_product=False):
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
        times = [datetime.strptime(d, "%Y-%m-%d").date() for d in result["dates"]]
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
            "bboxes": result["bboxes"]
        }
    return None


def merge_ranges(r1, r2):
    if r1 is None:
        return r2
    elif r2 is None:
        return r1
    time_set = r1["time_set"] | r2["time_set"]
    times = sorted(list(time_set))
    return {
        "lat": {
            "min": min(r1["lat"]["min"], r2["lat"]["min"]),
            "max": max(r1["lat"]["max"], r2["lat"]["max"]),
        },
        "lon": {
            "min": min(r1["lon"]["min"], r2["lon"]["min"]),
            "max": max(r1["lon"]["max"], r2["lon"]["max"]),
        },
        "times": times,
        "start_time": times[0],
        "end_time": times[-1],
        "time_set": time_set,
        "bboxes": {
            crs: {
                "top": max(r1["bboxes"][crs]["top"], r2["bboxes"][crs]["top"]),
                "bottom": min(r1["bboxes"][crs]["bottom"], r2["bboxes"][crs]["bottom"]),
                "right": max(r1["bboxes"][crs]["right"], r2["bboxes"][crs]["right"]),
                "left": min(r1["bboxes"][crs]["left"], r2["bboxes"][crs]["left"]),
            }
            for crs in r1["bboxes"].keys()
        }
    }


def get_sub_ranges(dc, product):
    conn = get_sqlconn(dc)
    results = conn.execute("select sub_product_id from wms.sub_product_ranges where product_id=%s", product.product.id)
    return {r["sub_product_id"]: get_ranges(dc, product.product.id, r["sub_product_id"]) for r in results}


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
  conn = get_sqlconn(dc)
  txn = conn.begin()
  prodid = product.id

  # Attempt to insert row
  conn.execute("""
    INSERT INTO wms.product_ranges
    (id,lat_min,lat_max,lon_min,lon_max,dates,bboxes)
    VALUES
    (%(p_id)s, 0, 0, 0, 0, %(empty)s, %(empty)s)
    ON CONFLICT (id) DO NOTHING
    """,
    {"p_id": prodid, "empty": Json("")})

  # Update extents
  conn.execute("""
    UPDATE wms.product_ranges
    SET (lat_min,lat_max,lon_min,lon_max) =
    (wms_get_min(%(p_idarr)s, 'lat'), wms_get_max(%(p_idarr)s, 'lat'), wms_get_min(%(p_idarr)s, 'lon'), wms_get_max(%(p_idarr)s, 'lon'))
    WHERE id=%(p_id)s
    """,
    {"p_id": prodid, "p_idarr": [ prodid ]})

  # Set default timezone
  conn.execute("""
    set timezone to 'Etc/UTC'
  """)

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

