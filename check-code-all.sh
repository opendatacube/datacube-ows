#!/usr/bin/env bash
# Convenience script for running Travis-like checks.
set -ex

# Run tests, taking coverage.
# Users can specify extra folders as arguments.
datacube-ows-update
python3 -m pytest --cov=datacube_ows --cov-report=xml integration_tests/
cp /tmp/coverage.xml /mnt/artifacts

set +x
