from __future__ import absolute_import, division, print_function

from functools import wraps

import logging
from time import monotonic
import os

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

def opencensus_tracing_enabled():
    return os.getenv("OPENCENSUS_TRACING_ENABLED", "false").lower() == "true"


def opencensus_trace_call(tracer=None, name=""):
    def decorator(func):
        @wraps(func)
        def opencensus_wrapper(*args, **kwargs):
            span_name = name if name else func.__name__
            with tracer.span(name=span_name):
                tracer.add_attribute_to_current_span(
                    "{}.args".format(span_name),
                    str(args))
                tracer.add_attribute_to_current_span(
                    "{}.kwargs".format(span_name),
                    str(kwargs))
                return func(*args, **kwargs)
        if tracer is None:
            return func
        else:
            return opencensus_wrapper

    return decorator

def get_jaeger_exporter():
    from opencensus.ext.jaeger import trace_exporter

    if not opencensus_tracing_enabled():
        return None

    opts = {
        "service_name": os.getenv("JAEGER_SERVICE_NAME", "OGC Web Services")
    }

    hostname = os.getenv("JAEGER_HOSTNAME")
    if hostname is not None:
        # opts["host_name"] = hostname
        opts["agent_host_name"] = hostname

    port = os.getenv("JAEGER_PORT")
    if port is not None:
        port = int(port)
        # opts["port"] = port
        opts["agent_port"] = port

    endpoint = os.getenv("JAEGER_ENDPOINT")
    if endpoint is not None:
        # opts["endpoint"] = endpoint
        opts["agent_endpoint"] = endpoint

    return trace_exporter(**opts)

def get_opencensus_sampler():
    from opencensus.trace.samplers import probability, always_on

    sample_rate = int(os.getenv("OPENCENSUS_SAMPLE_RATE", "100"))

    if not sample_rate < 100 and not sample_rate > 0:
        return always_on.AlwaysOnSampler
    else:
        return probability.ProbabilitySampler(rate=(sample_rate / 100.0))


def get_opencensus_tracer():
    if not opencensus_tracing_enabled():
        return None

    from opencensus.trace import tracer as tracer_module
    jaegerExporter = get_jaeger_exporter()
    sampler = get_opencensus_sampler()
    tracer = tracer_module.Tracer(exporter=jaegerExporter, sampler=sampler)

    return tracer


def group_by_statistical():
    from datacube.api.query import GroupBy

    return GroupBy(
        dimension='time',
        group_by_func=lambda ds: ds.time.begin,
        units='seconds since 1970-01-01 00:00:00',
        sort_key=lambda ds: ds.time.begin
    )


def get_sqlconn(dc):
    # pylint: disable=protected-access
    return dc.index._db._engine.connect()