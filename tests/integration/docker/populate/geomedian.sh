#! /usr/bin/env bash

# Populate the db with nrt data
datacube system init

# Add products
wget https://raw.githubusercontent.com/GeoscienceAustralia/digitalearthau/develop/digitalearthau/config/products/geomedian_nbart_annual.yaml
datacube product add geomedian_nbart_annual.yaml

pip3 install ruamel.yaml
# get indexer
wget https://raw.githubusercontent.com/opendatacube/datacube-ecs/b6779c5e3bb480914aeb38f4ac127d61346d58f3/indexer/ls_s2_cog.py

# Set data
python3 ls_s2_cog.py dea-test-store --prefix "geomedian-australia/v2.1.0/L8/x_-15/y_-24/2015/01/01/" --suffix ".yaml"

PGPASSWORD=$DB_PASSWORD psql \
    -d $DB_DATABASE \
    -h $DB_HOSTNAME \
    -p $DB_PORT \
    -U $DB_USERNAME \
    -f create_tables.sql

cp /opt/wms_cfgs/$1 datacube_wms/wms_cfg.py
python3 update_ranges.py