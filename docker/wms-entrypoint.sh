#!/usr/bin/env bash
set -e

get_wms_config.sh

docker-entrypoint.sh "$@"


