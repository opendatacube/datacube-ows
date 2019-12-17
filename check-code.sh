#!/usr/bin/env bash
# Convenience script for running Travis-like checks.

set -eu
set -x

pylint -j 2 --reports no datacube_ows --disable=C,R

# Run tests, taking coverage.
# Users can specify extra folders as arguments.
python3 -m pytest tests/ --ignore tests/test_wms_server.py --ignore tests/test_layers.py

set +x
