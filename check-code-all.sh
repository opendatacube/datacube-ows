#!/usr/bin/env bash
# Convenience script for running Travis-like checks.
set -ex

# ensure db is ready
sh ./docker/ows/wait-for-db
# Run tests, taking coverage.
# Users can specify extra folders as arguments.

# On top of base sql sample, index two more product for multiproducts
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/inland_water/wofs/wofs_albers.yaml
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/land_and_vegetation/fc/ls5_fc_albers.yaml
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/land_and_vegetation/fc/ls7_fc_albers.yaml
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/land_and_vegetation/fc/ls8_fc_albers.yaml

datacube dataset add https://data.dea.ga.gov.au/WOfS/WOFLs/v2.1.5/combined/x_6/y_-29/2004/05/03/LS_WATER_3577_6_-29_20040503003241500000_v1526732475.yaml
datacube dataset add https://data.dea.ga.gov.au/fractional-cover/fc/v2.2.1/ls5/x_6/y_-29/2004/05/11/LS5_TM_FC_3577_6_-29_20040511002356.yaml
datacube dataset add https://data.dea.ga.gov.au/fractional-cover/fc/v2.2.1/ls7/x_6/y_-29/2004/05/19/LS7_ETM_FC_3577_6_-29_20040519003242.yaml
datacube dataset add https://data.dea.ga.gov.au/fractional-cover/fc/v2.2.1/ls8/x_6/y_-29/2018/05/27/LS8_OLI_FC_3577_6_-29_20180527003612.yaml


# create material view for ranges extents
datacube-ows-update --schema --role $DB_USERNAME
datacube-ows-update

# run test
python3 -m pytest --cov=datacube_ows --cov-report=xml integration_tests/
cp /tmp/coverage.xml /mnt/artifacts

set +x
