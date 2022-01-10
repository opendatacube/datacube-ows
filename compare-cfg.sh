#!/usr/bin/env bash
# Convenience script for running Travis-like checks.

set -eu
set -x

datacube-ows-cfg check -i /tmp/inventory.json

set +x
