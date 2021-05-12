# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
"""Gunicorn config for Prometheus internal metrics
"""
import os

from prometheus_flask_exporter.multiprocess import \
    GunicornInternalPrometheusMetrics


def child_exit(server, worker):
    if os.environ.get("prometheus_multiproc_dir", False):
        GunicornInternalPrometheusMetrics.mark_process_dead_on_child_exit(worker.pid)
