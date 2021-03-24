"""Gunicorn config for Prometheus internal metrics
"""
import os

from prometheus_flask_exporter.multiprocess import GunicornInternalPrometheusMetrics


def child_exit(server, worker):
    if os.environ.get("prometheus_multiproc_dir", False):
        GunicornInternalPrometheusMetrics.mark_process_dead_on_child_exit(worker.pid)
