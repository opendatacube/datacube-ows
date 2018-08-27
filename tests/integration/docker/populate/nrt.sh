#! /usr/bin/env bash

# Populate the db with nrt data
datacube system init

# Add products
wget https://raw.githubusercontent.com/GeoscienceAustralia/dea-config/master/prod/products/nrt/sentinel/products.yaml
datacube product add products.yaml

pip3 install ruamel.yaml
# get indexer
wget https://raw.githubusercontent.com/opendatacube/datacube-ecs/b6779c5e3bb480914aeb38f4ac127d61346d58f3/indexer/ls_s2_cog.py

# Set data
python3 ls_s2_cog.py dea-test-store --prefix "L2/sentinel-2-nrt/S2MSIARD/2018-07-06/S2B_OPER_MSI_ARD_TL_SGS__20180706T020425_A006949_T54HWK_N02.06/" --suffix ".yaml"
python3 ls_s2_cog.py dea-test-store --prefix "L2/sentinel-2-nrt/S2MSIARD/2018-07-06/S2A_OPER_MSI_ARD_TL_EPAE_20180706T025847_A015858_T52HEK_N02.06/" --suffix ".yaml"

PGPASSWORD=$DB_PASSWORD psql \
    -d $DB_DATABASE \
    -h $DB_HOSTNAME \
    -p $DB_PORT \
    -U $DB_USERNAME \
    -f create_tables.sql

cp /opt/wms_cfgs/$1 datacube_wms/wms_cfg.py
python3 update_ranges.py