# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import absolute_import, division, print_function

import logging
from functools import wraps
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
