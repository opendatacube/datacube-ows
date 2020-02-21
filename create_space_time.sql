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

-- Handling different variants of metadata requires UNION with WHICH clauses per metadata type
-- https://www.postgresql.org/docs/11/queries-union.html

-- Try all different locations for temporal extents and UNION them
-- This is the eodataset variant of the temporal extent
select
  id,tstzrange(
    (metadata -> 'extent' ->> 'from_dt') :: timestamp,(metadata -> 'extent' ->> 'to_dt') :: timestamp
  ) as temporal_extent
from agdc.dataset where 
  metadata_type_ref=1::smallint or metadata_type_ref=5::smallint
UNION
-- This is the eo3 variant of the temporal extent, the sample eo3 dataset uses a singleton
-- timestamp, some other variants use start/end timestamps. From OWS perspective temporal
-- resolution is 1 whole day
select
  id,tstzrange(
    (metadata->'properties'->>'datetime'):: timestamp,
    (metadata->'properties'->>'datetime'):: timestamp + interval '1 day'
   ) as temporal_extent
from agdc.dataset where metadata_type_ref=3::smallint
UNION
-- Start/End timestamp variant product.
-- http://dapds00.nci.org.au/thredds/fileServer/xu18/ga_ls8c_ard_3/092/090/2019/06/05/ga_ls8c_ard_3-0-0_092090_2019-06-05_final.odc-metadata.yaml
select
  id,tstzrange(
    (metadata->'properties'->>'dtr:start_datetime'):: timestamp,
    (metadata->'properties'->>'dtr:end_datetime'):: timestamp
   ) as temporal_extent
from agdc.dataset where metadata_type_ref=4::smallint;


-- Spatial extents per dataset (to be created as a column of the space-time table)
-- Try all different locations for spatial extents and UNION them
with 
-- This is eo3 spatial (Uses CEMP INSAR as a sample product)
ranges as
(select id,
  (metadata #> '{extent, lat, begin}') as lat_begin,
  (metadata #> '{extent, lat, end}') as lat_end,
  (metadata #> '{extent, lon, begin}') as lon_begin,
  (metadata #> '{extent, lon, end}') as lon_end
   from agdc.dataset where 
      metadata_type_ref=3::smallint
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
   from agdc.dataset where metadata_type_ref=1::smallint 
   or metadata_type_ref=5::smallint)
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
 from agdc.dataset where metadata_type_ref=4::smallint;


-- This is optional and in native projection where present,
-- String processing drops EPSG prefix
select
  id,
  ST_Transform(
    ST_SetSRID(
      ST_GeomFromGeoJSON(
        metadata #>> '{grid_spatial,projection,valid_data}'),
        substr(
          metadata #>> '{grid_spatial,projection,spatial_reference}',6)::integer
        ),
        4326
      ) as detail_spatial_extent
      from agdc.dataset
      where
        metadata_type_ref=3::smallint

select id,
  ST_Transform(
    ST_SetSRID(
      ST_GeomFromGeoJSON(
        metadata #>> '{geometry}'),
        substr(
          metadata #>> '{crs}',6)::integer
        ),
        4326
      ) as detail_spatial_extent

 from agdc.dataset where metadata_type_ref=4::smallint;

select count(1),metadata_type_ref from agdc.dataset group by metadata_type_ref;