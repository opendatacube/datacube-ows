-- Creating TIME Materialised View

-- Try all different locations for temporal extents and UNION them

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

