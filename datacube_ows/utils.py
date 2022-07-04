# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import logging
from functools import wraps
from time import monotonic
from typing import Any, Callable, List, Optional, TypeVar

F = TypeVar('F', bound=Callable[..., Any])

def log_call(func: F) -> F:
    """
    Profiling function decorator

    Placing @log_call at the top of a function or method, results in all calls to that function or method
    being logged at debug level.
    """
    @wraps(func)
    def log_wrapper(*args, **kwargs):
        _LOG = logging.getLogger()
        _LOG.debug("%s args: %s kwargs: %s", func.__name__, args, kwargs)
        return func(*args, **kwargs)
    return log_wrapper


def time_call(func: F) -> F:
    """
    Profiling function decorator

    Placing @log_call at the top of a function or method, results in all calls to that function or method
    being timed at debug level.

    For debugging or optimisation research only.  Should not occur in mainline code.
    """
    @wraps(func)
    def timing_wrapper(*args, **kwargs):
        start: float = monotonic()
        result: Any = func(*args, **kwargs)
        stop: float = monotonic()
        _LOG = logging.getLogger()
        _LOG.debug("%s took: %d ms", func.__name__, int((stop - start) * 1000))
        return result
    return timing_wrapper


def group_by_statistical(pnames: Optional[List[str]] = None) -> "datacube.api.query.GroupBy":
    """
    Returns an ODC GroupBy object, suitable for daily statistical/summary data.
    """
    from datacube.api.query import GroupBy
    base_sort_key = lambda ds: ds.time.begin
    if pnames:
        index = {
            pn: i
            for i, pn in enumerate(pnames)
        }
        sort_key = lambda ds: (index.get(ds.type.name), base_sort_key(ds))
    else:
        sort_key = base_sort_key
    return GroupBy(
        dimension='time',
        group_by_func=lambda ds: ds.time.begin,
        units='seconds since 1970-01-01 00:00:00',
        sort_key=sort_key
    )

def group_by_solar(pnames: Optional[List[str]] = None) -> "datacube.api.query.GroupBy":
    from datacube.api.query import GroupBy, solar_day
    base_sort_key = lambda ds: ds.time.begin
    if pnames:
        index = {
            pn: i
            for i, pn in enumerate(pnames)
        }
        sort_key = lambda ds: (index.get(ds.type.name), base_sort_key(ds))
    else:
        sort_key = base_sort_key
    return GroupBy(
        dimension='time',
        group_by_func=solar_day,
        units='seconds since 1970-01-01 00:00:00',
        sort_key=sort_key
    )



def get_sqlconn(dc: "datacube.Datacube") -> "sqlalchemy.engine.base.Connection":
    """
    Extracts a SQLAlchemy database connection from a Datacube object.

    :param dc: An initialised Datacube object
    :return: A SQLAlchemy database connection object.
    """
    # pylint: disable=protected-access
    return dc.index._db._engine.connect()
