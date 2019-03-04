from __future__ import absolute_import, division, print_function

from functools import wraps

import logging
from time import monotonic

def log_call(func):
    @wraps(func)
    def log_wrapper(*args, **kwargs):
        _LOG = logging.getLogger()
        _LOG.debug("%s args: %s kwargs: %s", func.__name__, args, kwargs)
        return func(*args, **kwargs)
    return log_wrapper

def time_call(func):
    @wraps(func)
    def timing_wrapper(*args, **kwargs):
        start = monotonic()
        result = func(*args, **kwargs)
        stop = monotonic()
        _LOG = logging.getLogger()
        _LOG.debug("%s took: %d ms", func.__name__, int((stop - start) * 1000))
        return result
    return timing_wrapper

def opencensus_trace_call(tracer=None, name=""):
    def decorator(func):
        @wraps(func)
        def opencensus_wrapper(*args, **kwargs):
            span_name = name if name else func.__name__
            with tracer.span(name=span_name):
                return func(*args, **kwargs)
        if tracer is None:
            return func
        else:
            return opencensus_wrapper

    return decorator

def get_jaeger_exporter():
    from opencensus.trace.exporters.jaeger_exporter import JaegerExporter
    import os

    je = JaegerExporter(service_name=os.getenv("JAEGER_SERVICE_NAME", "OGC Web Services"),
                        host_name=os.getenv("JAEGER_HOST_NAME"),
                        port=os.getenv("JAEGER_PORT"),
                        endpoint=os.getenv("JAEGER_ENDPOINT"),
                        agent_host_name=os.getenv("JAEGER_HOST_NAME"),
                        agent_port=os.getenv("JAEGER_PORT"),
                        agent_endpoint=os.getenv("JAEGER_ENDPOINT"))
    return je
