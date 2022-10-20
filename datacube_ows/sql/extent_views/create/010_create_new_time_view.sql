-- Creating NEW TIME Materialised View (start of hard work)

-- Try all different locations for temporal extents and UNION them

CREATE MATERIALIZED VIEW IF NOT EXISTS time_view_new (dataset_type_ref, ID, temporal_extent)
AS
with
-- Crib metadata to use as for string matching various types
metadata_lookup as (
  select id,name from agdc.metadata_type
)
-- This is the eodataset variant of the temporal extent (from/to variant)
select
  dataset_type_ref, id,
  case
    when metadata -> 'extent' ->> 'from_dt' is null then
      tstzrange(
        (metadata -> 'extent' ->> 'center_dt') :: timestamp,
        (metadata -> 'extent' ->> 'center_dt') :: timestamp,
        '[]'
      )
    else
      tstzrange(
        (metadata -> 'extent' ->> 'from_dt') :: timestamp,
        (metadata -> 'extent' ->> 'to_dt') :: timestamp,
        '[]'
      )
  end as temporal_extent
from agdc.dataset where
  metadata_type_ref in (select id from metadata_lookup where name in ('eo','eo_s2_nrt', 'gqa_eo','eo_plus'))
  and archived is null
UNION
-- This is the eo3 variant of the temporal extent, the sample eo3 dataset uses a singleton
-- timestamp, some other variants use start/end timestamps. From OWS perspective temporal
-- resolution is 1 whole day
-- Start/End timestamp variant product.
-- http://dapds00.nci.org.au/thredds/fileServer/xu18/ga_ls8c_ard_3/092/090/2019/06/05/ga_ls8c_ard_3-0-0_092090_2019-06-05_final.odc-metadata.yaml
select
  dataset_type_ref, id,tstzrange(
    coalesce(metadata->'properties'->>'dtr:start_datetime', metadata->'properties'->>'datetime'):: timestamp,
    coalesce((metadata->'properties'->>'dtr:end_datetime'):: timestamp,(metadata->'properties'->>'datetime'):: timestamp),
    '[]'
   ) as temporal_extent
from agdc.dataset where
    metadata_type_ref in (select id from metadata_lookup where name in ('eo3_landsat_ard','eo3', 'eo3_sentinel_ard'))
    and archived is null
