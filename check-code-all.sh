#!/usr/bin/env bash
# Convenience script for running Travis-like checks.
set -ex

# ensure db is ready
sh ./docker/ows/wait-for-db
# Run tests, taking coverage.
# Users can specify extra folders as arguments.

datacube metadata add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/product_metadata/eo3_landsat_ard.odc-type.yaml

# On top of base sql sample, index two more product for multiproducts
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/baseline_satellite_data/definitive/s2a_ard_granule.odc-product.yaml
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/baseline_satellite_data/definitive/s2b_ard_granule.odc-product.yaml
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/land_and_vegetation/c3_fc/ga_ls_fc_3.odc-product.yaml

# add flag masking products
datacube product add https://explorer.dev.dea.ga.gov.au/products/geodata_coast_100k.odc-product.yaml
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/inland_water/c3_wo/ga_ls_wo_3.odc-product.yaml

datacube dataset add https://data.dea.ga.gov.au/baseline/s2a_ard_granule/2017-11-09/S2A_OPER_MSI_ARD_TL_SGS__20171109T022112_A012440_T54KUD_N02.06/eo3-ARD-METADATA.yaml
datacube dataset add https://data.dea.ga.gov.au/baseline/s2b_ard_granule/2017-11-09/S2B_OPER_MSI_ARD_TL_EPAE_20171109T165835_A003531_T55HFA_N02.06/eo3-ARD-METADATA.yaml
datacube dataset add https://data.dea.ga.gov.au/baseline/s2a_ard_granule/2017-08-21/S2A_OPER_MSI_ARD_TL_SGS__20170821T040758_A011296_T54KUD_N02.05/eo3-ARD-METADATA.yaml
datacube dataset add https://data.dea.ga.gov.au/baseline/s2b_ard_granule/2017-08-21/S2B_OPER_MSI_ARD_TL_SGS__20170821T031444_A002387_T55HFA_N02.05/eo3-ARD-METADATA.yaml

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
