#!/bin/bash
# Performs database creation, datacube and WMS database table setup and adds product definitions to datacube
#
# environment variables:
# DB_HOSTNAME:   Hostname or IP address for the database server
# DB_PORT:       Port used on database server
# DB_USERNAME:   Admin username for database server, must have create database privileges
# DB_PASSWORD:   Password for $DB_USERNAME
# DB_DATABASE:   Name of database that will be used by datacube and wms.
# PRODUCT_URLS:  ':' separated list of product definition URLs. Must not contain other ':' e.g. no 'https://'
# ONLY_PRODUCTS: If not empty this script will only add products and not perform database creation and initialization

# Create Database + datacube & WMS initialization
function setup_db {
docker-entrypoint.sh
datacube system init --no-init-users 2>&1

PGPASSWORD=$DB_PASSWORD psql \
    -d $DB_DATABASE \
    -h $DB_HOSTNAME \
    -p $DB_PORT \
    -U $DB_USERNAME \
    -f create_tables.sql 2>&1
}

# Add product definitions to datacube
# URLS must be delimited with ':' and WITHOUT http(s)://
function add_products {
    mkdir -p firsttime/products

    IFS=: read -ra URLS <<< "$PRODUCT_URLS"

    for U in "${URLS[@]}"
    do
        wget -P firsttime/products $U
    done

    for file in firsttime/products/*
    do
        datacube product add "$file"
    done
}

if [[ -z "${ONLY_PRODUCTS}" ]]; then
    setup_db
fi

add_products
