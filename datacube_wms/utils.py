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