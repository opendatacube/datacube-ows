#! /usr/bin/env bash

pushd docker
POPULATE=$1 docker-compose up -d
popd
cp "docker/config/${2}" ../../datacube_wms/wms_cfg_local.py
sleep 30
pytest -s --db_hostname="localhost" --db_port=54321
pushd docker
POPULATE=$1 docker-compose down
popd