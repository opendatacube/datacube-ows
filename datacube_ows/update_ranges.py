#!/usr/bin/env python3

from datacube_ows import __version__
from datacube_ows.product_ranges import get_sqlconn, add_ranges
from datacube import Datacube
import psycopg2
from psycopg2.sql import SQL
import sqlalchemy
from datacube_ows.ows_configuration import get_config
import os
import click

@click.command()
@click.option("--views", is_flag=True, default=False, help="Refresh the ODC spatio-temporal materialised views.")
@click.option("--schema", is_flag=True, default=False, help="Create or update the OWS database schema, including the spatio-temporal materialised views.")
@click.option("--role", default=None, help="Role to grant database permissions to")
@click.option("--summary", is_flag=True, default=False, help="Treat any named ODC products with no corresponding configured OWS Layer as summary products" )
@click.option("--merge-only/--no-merge-only", default=False, help="When used with a multiproduct layer, the ranges for underlying datacube products are not updated.")
@click.option("--product", default=None, help="Deprecated option provided for backwards compatibility")
@click.option("--multiproduct", default=None, help="Deprecated option provided for backwards compatibility." )
@click.option("--calculate-extent/--no-calculate-extent", default=None, help="Has no effect any more.  Provided for backwards compatibility only")
@click.option("--version", is_flag=True, default=False, help="Print version string and exit")
@click.argument("layers", nargs=-1)
def main(layers,
         merge_only, summary,
         schema, views, role, version,
         product, multiproduct, calculate_extent):
    """Manage datacube-ows range tables.

    Valid invocations:

    * update_ranges.py --schema --role myrole
        Create (re-create) the OWS schema (including materialised views) and grants permission to role myrole

    * update_ranges.py --views
        Refresh the materialised views

    * One or more OWS or ODC layer names
        Update ranges for the specified LAYERS

    * No LAYERS (and neither the --views nor --schema options)
        (Update ranges for all configured OWS layers.

    Uses the DATACUBE_OWS_CFG environment variable to find the OWS config file.
    """
    # --version
    if version:
        print("Open Data Cube Open Web Services (datacube-ows) version",
              __version__
               )
        return 0
    # Handle old-style calls
    if not layers:
        layers = []
    if product:
        print("********************************************************************************")
        print("Warning: The product flag is deprecated and will be removed in a future release.")
        print("          The correct way to make this call is now:")
        print("          ")
        print("          python3 update_ranges.py %s" % product)
        print("********************************************************************************")
        layers.append(product)
    if multiproduct:
        print("********************************************************************************")
        print("Warning: The product flag is deprecated and will be removed in a future release.")
        print("          The correct way to make this call is now:")
        print("          ")
        if merge_only:
            print("          python3 update_ranges.py --merge-only %s" % multiproduct)
        else:
            print("          python3 update_ranges.py %s" % multiproduct)
        print("********************************************************************************")
        layers.append(multiproduct)
    if calculate_extent is not None:
        print("********************************************************************************")
        print("Warning: The calculate-extent and no-calculate-extent flags no longer have ")
        print("         any effect.  They are kept only for backwards compatibility and will")
        print("         be removed in a future release.")
        print("********************************************************************************")
    if schema and layers:
        print("Sorry, cannot update the schema and ranges in the same invocation.")
        return 1
    elif views and layers:
        print("Sorry, cannot update the materialised views and ranges in the same invocation.")
        return 1
    elif schema and not role:
        print("Sorry, cannot update schema without specifying a role")
        return 1
    elif role and not schema:
        print("Sorry, role only makes sense for updating the schema")
        return 1

    if os.environ.get("PYDEV_DEBUG"):
        import pydevd_pycharm
        pydevd_pycharm.settrace('172.17.0.1', port=12321, stdoutToServer=True, stderrToServer=True)

    dc = Datacube(app="ows_update_ranges")
    if schema:
        print("Checking schema....")
        print("Creating or replacing WMS database schema...")
        create_schema(dc, role)
        print("Creating or replacing materialised views...")
        create_views(dc)
        print("Done")
        return 0
    elif views:
        print("Refreshing materialised views...")
        refresh_views(dc)
        print("Done")
        return 0

    print("Deriving extents from materialised views")
    if not layers:
        layers = list(get_config().product_index.keys())
    try:
        add_ranges(dc, layers, summary, merge_only)
    except (psycopg2.errors.UndefinedColumn,
            sqlalchemy.exc.ProgrammingError):
        print("ERROR: OWS schema or extent materialised views appear to be missing",
              "\n",
              "       Try running with the --schema options first."
              )
        return 1
    return 0


def create_views(dc):
    commands = [
        ("Installing Postgis extensions on public schema",
         "create extension if not exists postgis"),
        ("Giving other schemas access to PostGIS functions installed in the public schema",
         """ALTER DATABASE %s
            SET
              search_path = public,
              agdc
         """ % os.environ.get("DB_DATABASE", "datacube")),
        ("Dropping already existing Materialized View Index 1/3",
            "DROP INDEX IF EXISTS space_time_view_geom_idx"),
        ("Dropping already existing Materialized View Index 2/3",
            "DROP INDEX IF EXISTS space_time_view_time_idx"),
        ("Dropping already existing Materialized View Index 3/3",
            "DROP INDEX IF EXISTS space_time_view_ds_idx"),
        ("Dropping already existing Materialized View 1/3",
            "DROP MATERIALIZED VIEW IF EXISTS space_time_view"),
        ("Dropping already existing Materialized View 2/3",
            "DROP MATERIALIZED VIEW IF EXISTS time_view"),
        ("Dropping already existing Materialized View 3/3",
            "DROP MATERIALIZED VIEW IF EXISTS space_view"),
        ("Setting default timezone to UTC",
            "set timezone to 'Etc/UTC'"),

# Handling different variants of metadata requires UNION with WHICH clauses per metadata type
# https://www.postgresql.org/docs/11/queries-union.html

# Try all different locations for temporal extents and UNION them
        ("Creating TIME Materialised View",
         """
CREATE MATERIALIZED VIEW IF NOT EXISTS time_view (dataset_type_ref, ID, temporal_extent)
AS
with
-- Crib metadata to use as for string matching various types
metadata_lookup as (
  select id,name from agdc.metadata_type
)
-- This is the eodataset variant of the temporal extent
select
  dataset_type_ref, id,tstzrange(
    (metadata -> 'extent' ->> 'from_dt') :: timestamp,(metadata -> 'extent' ->> 'to_dt') :: timestamp + interval '1 microsecond'
  )  as temporal_extent
from agdc.dataset where
  metadata_type_ref in (select id from metadata_lookup where name in ('eo','gqa_eo','eo_plus'))
UNION
-- This is the eo3 variant of the temporal extent, the sample eo3 dataset uses a singleton
-- timestamp, some other variants use start/end timestamps. From OWS perspective temporal
-- resolution is 1 whole day
select
  dataset_type_ref, id,tstzrange(
    (metadata->'properties'->>'datetime'):: timestamp,
    (metadata->'properties'->>'datetime'):: timestamp + interval '1 day'
   ) as temporal_extent
from agdc.dataset where metadata_type_ref in (select id from metadata_lookup where name='eo3')
UNION
-- Start/End timestamp variant product.
-- http://dapds00.nci.org.au/thredds/fileServer/xu18/ga_ls8c_ard_3/092/090/2019/06/05/ga_ls8c_ard_3-0-0_092090_2019-06-05_final.odc-metadata.yaml
select
  dataset_type_ref, id,tstzrange(
    (metadata->'properties'->>'dtr:start_datetime'):: timestamp,
    (metadata->'properties'->>'dtr:end_datetime'):: timestamp
   ) as temporal_extent
from agdc.dataset where metadata_type_ref in (select id from metadata_lookup where name in ('eo3_landsat_ard'))
"""),
        # Spatial extents per dataset (to be created as a column of the space-time table)
        # Try all different locations for spatial extents and UNION them
        ("Creating SPACE Materialised View (Slowest step!)", """
CREATE MATERIALIZED VIEW IF NOT EXISTS space_view (ID, spatial_extent)
AS
with
-- Crib metadata to use as for string matching various types
metadata_lookup as (
  select id,name from agdc.metadata_type
),
-- This is eo3 spatial (Uses CEMP INSAR as a sample product)
ranges as
(select id,
  (metadata #> '{extent, lat, begin}') as lat_begin,
  (metadata #> '{extent, lat, end}') as lat_end,
  (metadata #> '{extent, lon, begin}') as lon_begin,
  (metadata #> '{extent, lon, end}') as lon_end
   from agdc.dataset where
      metadata_type_ref in (select id from metadata_lookup where name='eo3')
  ),
-- This is eo spatial (Uses ALOS-PALSAR over Africa as a sample product)
corners as
(select id,
  (metadata #> '{extent, coord, ll, lat}') as ll_lat,
  (metadata #> '{extent, coord, ll, lon}') as ll_lon,
  (metadata #> '{extent, coord, lr, lat}') as lr_lat,
  (metadata #> '{extent, coord, lr, lon}') as lr_lon,
  (metadata #> '{extent, coord, ul, lat}') as ul_lat,
  (metadata #> '{extent, coord, ul, lon}') as ul_lon,
  (metadata #> '{extent, coord, ur, lat}') as ur_lat,
  (metadata #> '{extent, coord, ur, lon}') as ur_lon
   from agdc.dataset where metadata_type_ref in (select id from metadata_lookup where name in ('eo','gqa_eo','eo_plus')))
select id,format('POLYGON(( %s %s, %s %s, %s %s, %s %s, %s %s))',
        lon_begin, lat_begin, lon_end, lat_begin,  lon_end, lat_end,
        lon_begin, lat_end, lon_begin, lat_begin)::geometry
as spatial_extent
from ranges
UNION
select id,format('POLYGON(( %s %s, %s %s, %s %s, %s %s, %s %s))',
        ll_lon, ll_lat, lr_lon, lr_lat,  ur_lon, ur_lat,
        ul_lon, ul_lat, ll_lon, ll_lat)::geometry as spatial_extent
from corners
UNION
-- This is lansat_scene and landsat_l1_scene with geometries
select id,
  ST_Transform(
    ST_SetSRID(
      ST_GeomFromGeoJSON(
        metadata #>> '{geometry}'),
        substr(
          metadata #>> '{crs}',6)::integer
        ),
        4326
      ) as spatial_extent
 from agdc.dataset where metadata_type_ref in (select id from metadata_lookup where name in ('eo3_landsat_ard'))
         """, True),
# Join the above queries for space and time as CTE's into a space-time view

        ("Creating combined SPACE-TIME Materialised View",
         """
CREATE MATERIALIZED VIEW IF NOT EXISTS space_time_view (ID, dataset_type_ref, spatial_extent, temporal_extent)
AS
select space_view.id, dataset_type_ref, spatial_extent, temporal_extent from space_view join time_view on space_view.id=time_view.id
        """),

# Spatial extents are indexed using GIST index for BBOX queries
# https://postgis.net/workshops/postgis-intro/indexing.html
        ("Creating Materialised View Index 1/3", """
CREATE INDEX space_time_view_geom_idx
  ON space_time_view
  USING GIST (spatial_extent)
  """),

# Time range types can carray indexes for range lookup
# https://www.postgresql.org/docs/11/rangetypes.html#RANGETYPES-INDEXING
    ("Creating Materialised View Index 2/3", """
     CREATE INDEX space_time_view_time_idx
  ON space_time_view
  USING SPGIST (temporal_extent)
    """),

# Create standard btree index over dataset_type_ref to ease searching by
# https://ieftimov.com/post/postgresql-indexes-btree/
           ("Creating Materialised View Index 3/3", """
            CREATE INDEX space_time_view_ds_idx
  ON space_time_view
  USING BTREE(dataset_type_ref)
  """),

    ]
    run_sql(dc, commands)


def refresh_views(dc):
    commands = [
        ("Refreshing TIME materialized view",
         "REFRESH MATERIALIZED VIEW time_view"
         ),
        ("Refreshing SPACE materialized view",
         "REFRESH MATERIALIZED VIEW space_view"
         ),
        ("Refreshing combined SPACE-TIME materialized view",
         "REFRESH MATERIALIZED VIEW CONCURRENTLY space_time_view"
         ),
    ]
    run_sql(dc, commands)


def create_schema(dc, role):
    commands = [
        ("Creating/replacing wms schema", "create schema if not exists wms"),

        ("Creating/replacing product ranges table", """
            create table if not exists wms.product_ranges (
                id smallint not null primary key references agdc.dataset_type (id),

                lat_min decimal not null,
                lat_max decimal not null,
                lon_min decimal not null,
                lon_max decimal not null,

                dates jsonb not null,

                bboxes jsonb not null)
        """),
        ("Creating/replacing sub-product ranges table", """
            create table if not exists wms.sub_product_ranges (
                product_id smallint not null references agdc.dataset_type (id),
                sub_product_id smallint not null,
                lat_min decimal not null,
                lat_max decimal not null,
                lon_min decimal not null,
                lon_max decimal not null,
                dates jsonb not null,
                bboxes jsonb not null,
                constraint pk_sub_product_ranges primary key (product_id, sub_product_id) )
        """),
        ("Creating/replacing multi-product ranges table", """
            create table if not exists wms.multiproduct_ranges (
                wms_product_name varchar(128) not null primary key,
                lat_min decimal not null,
                lat_max decimal not null,
                lon_min decimal not null,
                lon_max decimal not null,
                dates jsonb not null,
                bboxes jsonb not null)
        """),
        # Functions
        ("Creating/replacing wms_get_min() function", """
            CREATE OR REPLACE FUNCTION wms_get_min(integer[], text) RETURNS numeric AS $$
            DECLARE
                ret numeric;
                ul text[] DEFAULT array_append('{extent, coord, ul}', $2);
                ur text[] DEFAULT array_append('{extent, coord, ur}', $2);
                ll text[] DEFAULT array_append('{extent, coord, ll}', $2);
                lr text[] DEFAULT array_append('{extent, coord, lr}', $2);
            BEGIN
                WITH m AS ( SELECT metadata FROM agdc.dataset WHERE dataset_type_ref = any($1) AND archived IS NULL )
                SELECT MIN(LEAST((m.metadata#>>ul)::numeric, (m.metadata#>>ur)::numeric,
                       (m.metadata#>>ll)::numeric, (m.metadata#>>lr)::numeric))
                INTO ret
                FROM m;
                RETURN ret;
            END;
            $$ LANGUAGE plpgsql;
        """),
        ("Creating/replacing wms_get_max() function", """
            CREATE OR REPLACE FUNCTION wms_get_max(integer[], text) RETURNS numeric AS $$
            DECLARE
                ret numeric;
                ul text[] DEFAULT array_append('{extent, coord, ul}', $2);
                ur text[] DEFAULT array_append('{extent, coord, ur}', $2);
                ll text[] DEFAULT array_append('{extent, coord, ll}', $2);
                lr text[] DEFAULT array_append('{extent, coord, lr}', $2);
            BEGIN
                WITH m AS ( SELECT metadata FROM agdc.dataset WHERE dataset_type_ref = ANY ($1) AND archived IS NULL )
                SELECT MAX(GREATEST((m.metadata#>>ul)::numeric, (m.metadata#>>ur)::numeric,
                       (m.metadata#>>ll)::numeric, (m.metadata#>>lr)::numeric))
                INTO ret
                FROM m;
                RETURN ret;
            END;
            $$ LANGUAGE plpgsql;
        """),
        ("""Granting usage on schema""",
         "GRANT USAGE ON SCHEMA wms TO %s" % role
        )
    ]
    run_sql(dc, commands)

def run_sql(dc, commands):
    conn = get_sqlconn(dc)
    for cmd_blob in commands:
        if len(cmd_blob) == 2:
            msg, sql = cmd_blob
            override = False
        else:
            msg, sql, override = cmd_blob
        print(msg)
        if override:
            q = SQL(sql)
            with conn.connection.cursor() as psycopg2connection:
                psycopg2connection.execute(q)
        else:
            conn.execute(sql)

    # Add user based on param
    # use psycopg2 directly to get proper psql
    # quoting on the role name identifier
    # print("Granting usage on schema")
    # q = SQL("GRANT USAGE ON SCHEMA wms TO {}").format(Identifier(role))
    # with conn.connection.cursor() as psycopg2connection:
    #     psycopg2connection.execute(q)
    conn.close()

    return


if __name__ == '__main__':
    main()


