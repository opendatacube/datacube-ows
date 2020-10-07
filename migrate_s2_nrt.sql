/*
   There are 5 tables under schema agdc namely:
     - dataset
     - dataset_location
     - dataset_source
     - dataset_type
     - metadata_type
*/
-- SELECT id of the targeted product
SELECT id
FROM agdc.dataset_type
WHERE name IN ('s2a_nrt_granule', 's2b_nrt_granule', 's2a_l1c_aws_pds', 's2b_l1c_aws_pds');

-- SELECT id of the targeted dataset
SELECT id
FROM agdc.dataset
WHERE dataset_type_ref IN (SELECT id FROM agdc.dataset_type WHERE name IN ('s2a_nrt_granule', 's2b_nrt_granule', 's2a_l1c_aws_pds', 's2b_l1c_aws_pds'));

-- SELECT the rows of the dataset_location
SELECT id
FROM agdc.dataset_location
WHERE dataset_ref IN  (SELECT id
FROM agdc.dataset
WHERE dataset_type_ref IN (SELECT id FROM agdc.dataset_type WHERE name IN ('s2a_nrt_granule', 's2b_nrt_granule', 's2a_l1c_aws_pds', 's2b_l1c_aws_pds'))
);

-- SELECT the rows of dataset_source
SELECT source_dataset_ref
FROM agdc.dataset_source
WHERE dataset_ref IN (SELECT id
FROM agdc.dataset
WHERE dataset_type_ref IN (SELECT id FROM agdc.dataset_type WHERE name IN ('s2a_nrt_granule', 's2b_nrt_granule', 's2a_l1c_aws_pds', 's2b_l1c_aws_pds'))
);

-- start deleting
DELETE
FROM agdc.dataset_source
WHERE dataset_ref IN (SELECT id
FROM agdc.dataset
WHERE dataset_type_ref IN (SELECT id FROM agdc.dataset_type WHERE name IN ('s2a_nrt_granule', 's2b_nrt_granule', 's2a_l1c_aws_pds', 's2b_l1c_aws_pds'))
);

DELETE
FROM agdc.dataset_location
WHERE dataset_ref IN  (SELECT id
FROM agdc.dataset
WHERE dataset_type_ref IN (SELECT id FROM agdc.dataset_type WHERE name IN ('s2a_nrt_granule', 's2b_nrt_granule', 's2a_l1c_aws_pds', 's2b_l1c_aws_pds'))
);

DELETE
FROM agdc.dataset
WHERE dataset_type_ref IN (SELECT id FROM agdc.dataset_type WHERE name IN ('s2a_nrt_granule', 's2b_nrt_granule', 's2a_l1c_aws_pds', 's2b_l1c_aws_pds'));

DELETE
FROM agdc.dataset_type
WHERE name IN ('s2a_nrt_granule', 's2b_nrt_granule', 's2a_l1c_aws_pds', 's2b_l1c_aws_pds');
