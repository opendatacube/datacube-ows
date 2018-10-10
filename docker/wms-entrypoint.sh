#!/usr/bin/env bash
set -e

get_wms_config.sh

export GDAL_DATA="$(gdal-config --datadir)"; docker-entrypoint.sh "$@"
