#!/usr/bin/env bash
# Convenience script for running Travis-like checks.
set -ex

# ensure db is ready
sh ./docker/ows/wait-for-db
# Run tests, taking coverage.
# Users can specify extra folders as arguments.

# On top of base sql sample, index two more product for multiproducts
datacube product add https://data.dea.ga.gov.au/geomedian-australia/v2.1.0/product-definition.yaml
datacube dataset add https://data.dea.ga.gov.au/geomedian-australia/v2.1.0/L7/x_-11/y_-13/2016/01/01/ls7_gm_nbart_-11_-13_20160101.yaml
datacube dataset add https://data.dea.ga.gov.au/geomedian-australia/v2.1.0/L8/x_-11/y_-13/2016/01/01/ls8_gm_nbart_-11_-13_20160101.yaml

# create material view for ranges extents
datacube-ows-update --schema --role $DB_USERNAME
datacube-ows-update

# run test
python3 -m pytest --cov=datacube_ows --cov-report=xml integration_tests/
cp /tmp/coverage.xml /mnt/artifacts

set +x
