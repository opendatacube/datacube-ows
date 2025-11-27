-- Confirm owner of layer_ranges table (if it already exists)

-- Note "bootstrap" scripts need to be run by a database superuser

alter table if exists ows.layer_ranges owner to agdc_admin
