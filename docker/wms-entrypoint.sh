#!/usr/bin/env bash
set -e

export GDAL_DATA="$(gdal-config --datadir)"; docker-entrypoint.sh "$@"
