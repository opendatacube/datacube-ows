-- Creating combined SPACE-TIME Materialised View",

CREATE MATERIALIZED VIEW IF NOT EXISTS space_time_view (ID, dataset_type_ref, spatial_extent, temporal_extent)
AS
select space_view.id, dataset_type_ref, spatial_extent, temporal_extent from space_view join time_view on space_view.id=time_view.id
