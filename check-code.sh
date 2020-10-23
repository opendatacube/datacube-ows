#!/usr/bin/env bash
# Convenience script for running Travis-like checks.

set -eu
set -x

# Run tests, taking coverage.
# Users can specify extra folders as arguments.
python3 -m pytest --cov=datacube_ows --cov-report=xml tests/
cp /tmp/coverage.xml /mnt/artifacts

set +x
