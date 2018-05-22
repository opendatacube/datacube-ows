#!/usr/bin/env bash
set -e

get_wms_config.sh

# CURL is only searching for certificates in a RedHat specific path.
# Create the path and link our existing certificates this path
# to allow curl to find the certificates.
mkdir -p /etc/pki/tls/certs
ln -s /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt;

docker-entrypoint.sh "$@"


