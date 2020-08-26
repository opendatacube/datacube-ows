-- Creating NEW combined SPACE-TIME Materialised View

CREATE MATERIALIZED VIEW IF NOT EXISTS space_time_view_new (ID, dataset_type_ref, spatial_extent, temporal_extent)
AS
select space_view_new.id, dataset_type_ref, spatial_extent, temporal_extent from space_view_new join time_view_new on space_view_new.id=time_view_new.id
