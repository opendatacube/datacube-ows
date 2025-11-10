-- Confirm owner of time materialized view (if it already exists)

-- Note "bootstrap" scripts need to be run by a database superuser

alter materialized view if exists ows.space_time_view owner to agdc_manage;
