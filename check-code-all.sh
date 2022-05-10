#!/usr/bin/env bash
# Convenience script for running Travis-like checks.
set -ex

# ensure db is ready
sh ./docker/ows/wait-for-db
# Run tests, taking coverage.
# Users can specify extra folders as arguments.

# On top of base sql sample, index two more product for multiproducts
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/baseline_satellite_data/definitive/s2a_ard_granule.odc-product.yaml
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/baseline_satellite_data/definitive/s2b_ard_granule.odc-product.yaml

datacube dataset add https://data.dea.ga.gov.au/baseline/s2a_ard_granule/2017-11-09/S2A_OPER_MSI_ARD_TL_SGS__20171109T022112_A012440_T54KVF_N02.06/eo3-ARD-METADATA.odc-metadata.yaml
datacube dataset add https://data.dea.ga.gov.au/baseline/s2b_ard_granule/2017-11-09/S2B_OPER_MSI_ARD_TL_EPAE_20171109T165539_A003531_T56LLM_N02.06/eo3-ARD-METADATA.odc-metadata.yaml

# create material view for ranges extents
datacube-ows-update --schema --role $DB_USERNAME
datacube-ows-update

# run test
python3 -m pytest --cov=datacube_ows --cov-report=xml integration_tests/
cp /tmp/coverage.xml /mnt/artifacts

set +x
