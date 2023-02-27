#!/usr/bin/env bash
# Convenience script for running Travis-like checks.
set -ex

# ensure db is ready
sh ./docker/ows/wait-for-db
# Run tests, taking coverage.
# Users can specify extra folders as arguments.

datacube metadata add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/product_metadata/eo3_landsat_ard.odc-type.yaml
datacube metadata add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/product_metadata/eo3_sentinel_ard.odc-type.yaml

# On top of base sql sample, index two more product for multiproducts
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/baseline_satellite_data/c3/ga_s2am_ard_3.odc-product.yaml
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/baseline_satellite_data/c3/ga_s2bm_ard_3.odc-product.yaml
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/land_and_vegetation/c3_fc/ga_ls_fc_3.odc-product.yaml

# add flag masking products
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/sea_ocean_coast/geodata_coast_100k/geodata_coast_100k.odc-product.yaml
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/inland_water/c3_wo/ga_ls_wo_3.odc-product.yaml



datacube dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2bm_ard_3/52/LGM/2017/07/19/20170719T030622/ga_s2bm_ard_3-2-1_52LGM_2017-07-19_final.odc-metadata.yaml --confirm-ignore-lineage
datacube dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2bm_ard_3/52/LGM/2017/07/29/20170729T081630/ga_s2bm_ard_3-2-1_52LGM_2017-07-29_final.odc-metadata.yaml --confirm-ignore-lineage
datacube dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2bm_ard_3/52/LGM/2017/08/08/20170818T192649/ga_s2bm_ard_3-2-1_52LGM_2017-08-08_final.odc-metadata.yaml --confirm-ignore-lineage
datacube dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2am_ard_3/52/LGM/2017/07/14/20170714T082022/ga_s2am_ard_3-2-1_52LGM_2017-07-14_final.odc-metadata.yaml --confirm-ignore-lineage
datacube dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2am_ard_3/52/LGM/2017/07/24/20170724T030641/ga_s2am_ard_3-2-1_52LGM_2017-07-24_final.odc-metadata.yaml --confirm-ignore-lineage
datacube dataset add https://dea-public-data.s3.ap-southeast-2.amazonaws.com/baseline/ga_s2am_ard_3/52/LGM/2017/08/03/20170921T103758/ga_s2am_ard_3-2-1_52LGM_2017-08-03_final.odc-metadata.yaml --confirm-ignore-lineage

datacube dataset add https://data.dea.ga.gov.au/projects/geodata_coast_100k/v2004/x_15/y_-40/COAST_100K_15_-40.yaml
datacube dataset add https://data.dea.ga.gov.au/projects/geodata_coast_100k/v2004/x_8/y_-21/COAST_100K_8_-21.yaml

datacube dataset add https://data.dea.ga.gov.au/derivative/ga_ls_wo_3/1-6-0/094/077/2018/02/08/ga_ls_wo_3_094077_2018-02-08_final.odc-metadata.yaml --confirm-ignore-lineage
datacube dataset add https://data.dea.ga.gov.au/derivative/ga_ls_fc_3/2-5-1/094/077/2018/02/08/ga_ls_fc_3_094077_2018-02-08_final.odc-metadata.yaml --confirm-ignore-lineage

# create material view for ranges extents
datacube-ows-update --schema --role $DB_USERNAME
datacube-ows-update

# run test
python3 -m pytest --cov=datacube_ows --cov-report=xml integration_tests/
cp /tmp/coverage.xml /mnt/artifacts

set +x
