#!/usr/bin/env bash
# Convenience script for running Travis-like checks.

set -eu
set -x

pep8 tests --max-line-length 120

pylint -j 2 --reports no datacube_wms

# Run tests, taking coverage.
# Users can specify extra folders as arguments.
pytest -r sx --cov datacube_wms --doctest-ignore-import-errors --durations=5 datacube_wms tests

set +x
