#!/usr/bin/env bash
set -e

mkdir -p /etc/pki/tls/certs
ln -s /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt;

get_wms_config.sh

docker-entrypoint.sh "$@"


