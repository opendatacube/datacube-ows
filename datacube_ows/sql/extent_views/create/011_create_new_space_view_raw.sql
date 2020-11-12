-- Creating NEW SPACE Materialised View (Slowest step!)

-- Spatial extents per dataset (to be created as a column of the space-time table)
-- Try all different locations for spatial extents and UNION them
CREATE MATERIALIZED VIEW IF NOT EXISTS space_view_new (ID, spatial_extent)
AS
with
-- Crib metadata to use as for string matching various types
metadata_lookup as (
  select id,name from agdc.metadata_type
),
-- This is eo3 spatial (Uses CEMP INSAR as a sample product)
ranges as
(select id,
  (metadata #>> '{extent, lat, begin}') as lat_begin,
  (metadata #>> '{extent, lat, end}') as lat_end,
  (metadata #>> '{extent, lon, begin}') as lon_begin,
  (metadata #>> '{extent, lon, end}') as lon_end
   from agdc.dataset where
      metadata_type_ref in (select id from metadata_lookup where name='eo3')
      and archived is null
  ),
-- This is eo spatial (Uses ALOS-PALSAR over Africa as a sample product)
corners as
(select id,
  (metadata #>> '{extent, coord, ll, lat}') as ll_lat,
  (metadata #>> '{extent, coord, ll, lon}') as ll_lon,
  (metadata #>> '{extent, coord, lr, lat}') as lr_lat,
  (metadata #>> '{extent, coord, lr, lon}') as lr_lon,
  (metadata #>> '{extent, coord, ul, lat}') as ul_lat,
  (metadata #>> '{extent, coord, ul, lon}') as ul_lon,
  (metadata #>> '{extent, coord, ur, lat}') as ur_lat,
  (metadata #>> '{extent, coord, ur, lon}') as ur_lon
   from agdc.dataset where
        metadata_type_ref in (select id from metadata_lookup where name in ('eo','eo_s2_nrt','gqa_eo','eo_plus'))
        and archived is null
    )
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
 from agdc.dataset where
        metadata_type_ref in (select id from metadata_lookup where name in ('eo3_landsat_ard'))
        and archived is null
