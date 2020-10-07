#!/usr/bin/env bash
# Convenience script for running Travis-like checks.
set -ex

# ensure db is ready
sh ./docker/ows/wait-for-db
# Run tests, taking coverage.
# Users can specify extra folders as arguments.

datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-datakube/3b9bfbdeece035d46a098faac95a0bbc6c659596/charts/datacube-index/files/product-nrt-s2.yaml

./add_dataset.sh

# Run delete script to cleanse old product name
PGPASSWORD=$DB_PASSWORD psql -U $DB_USERNAME -d $DB_DATABASE -a -f migrate_s2_nrt.sql -p $DB_PORT -h $DB_HOSTNAME

# Add a new metadata type
datacube metadata add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/products/nrt/sentinel/eo_s2_nrt.odc-type.yaml

#add new product definition
datacube product add https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/39eb4ce98dde51d82e508f7c8748523cc3a2f0a7/products/nrt/sentinel/s2_nrt.products.yaml

./add_dataset.sh
set +x
