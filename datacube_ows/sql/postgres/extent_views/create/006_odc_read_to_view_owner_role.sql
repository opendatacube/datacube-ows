-- Grant read access to AGDC tables to view owner role.

GRANT SELECT ON agdc.dataset, agdc.dataset_type, agdc.metadata_type, agdc.dataset_location TO ows_view_owner;
