-- Grant schema modifying permissions to ODC admin and manage roles

-- Note "bootstrap" scripts need to be run by a database superuser

grant all on schema ows to odc_admin, odc_manage
