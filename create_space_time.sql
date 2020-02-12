-- This is an exploration script for maintaining spatio-temporal extents for datasets in
-- datacube database outside of JSON blobs with a coalesce around 2 different types
-- metadata definitions (eodataset and eo3)

-- Install Postgis extensions on public schema
create extension postgis;
-- Needed to give other schemas access to PostGIS functions installed in the public schema
ALTER DATABASE datacube
SET
  search_path = public,
  agdc;

-- Handling different variants of metadata requires COALESCE
-- https://www.postgresql.org/docs/11/functions-conditional.html#FUNCTIONS-COALESCE-NVL-IFNULL

-- Try all different locations for temporal extents and COALESCE them
-- This is the eodataset variant of the temporal extent
select
  tstzrange(
    (metadata -> 'extent' ->> 'from_dt') :: timestamp,(metadata -> 'extent' ->> 'to_dt') :: timestamp
  ) as temporal_extent
from agdc.dataset where metadata_type_ref=1::smallint;

-- This is the eo3 variant of the temporal extent, the sample eo3 dataset uses a singleton
-- timestamp, some other variants use start/end timestamps. From OWS perspective temporal
-- resolution is 1 whole day
select
  tstzrange(
    (metadata->'properties'->>'datetime'):: timestamp,
    (metadata->'properties'->>'datetime'):: timestamp + interval '1 day'
   ) as temporal_extent
from agdc.dataset where metadata_type_ref=3::smallint;

-- Try all different locations for spatial extents and COALESCE them
-- This is eo3 spatial (Uses CEMP INSAR as a sample product)
select metadata from agdc.dataset where metadata_type_ref=3::smallint;

-- This is eo spatial (Uses ALOS-PALSAR over Africa as a sample product)
with corners as
(select id,
  (metadata #> '{extent, coord, ll, lat}') as ll_lat,
  (metadata #> '{extent, coord, ll, lon}') as ll_lon,
  (metadata #> '{extent, coord, lr, lat}') as lr_lat,
  (metadata #> '{extent, coord, lr, lon}') as lr_lon,
  (metadata #> '{extent, coord, ul, lat}') as ul_lat,
  (metadata #> '{extent, coord, ul, lon}') as ul_lon,
  (metadata #> '{extent, coord, ur, lat}') as ur_lat,
  (metadata #> '{extent, coord, ur, lon}') as ur_lon
   from agdc.dataset where metadata_type_ref=1::smallint)
select id,format('POLYGON(( %s %s, %s %s, %s %s, %s %s, %s %s))',
        ll_lon, ll_lat, lr_lon, lr_lat,  ur_lon, ur_lat, 
        ul_lon, ul_lat, ll_lon, ll_lat)::geometry as spatial_extent 
from corners;

-- This is optional and in native projection where present (3577, spatial reference where present)
select
    ST_Transform(
    ST_SetSRID(
    ST_GeomFromGeoJSON(
        metadata #>> '{grid_spatial,projection,valid_data}'),
        3577
    ),
    4326
    ) as spatial_extent
from agdc.dataset;