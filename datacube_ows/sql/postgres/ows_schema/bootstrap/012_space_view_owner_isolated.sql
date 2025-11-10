-- Confirm owner of space materialized view (if it already exists)

-- Note "bootstrap" scripts need to be run by a database superuser

alter materialized view if exists ows.space_view owner to agdc_manage;
