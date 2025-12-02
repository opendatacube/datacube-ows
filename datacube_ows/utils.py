# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import datetime
import logging
from collections.abc import Callable
from datetime import timezone
from functools import wraps
from time import monotonic
from typing import Any, TypeVar, cast

from datacube import Datacube
from datacube.api.query import GroupBy, solar_day
from datacube.index import Index
from datacube.model import Dataset
from numpy import datetime64 as npdt64
from numpy import timedelta64 as npdelt64
from sqlalchemy.engine.base import Connection

F = TypeVar("F", bound=Callable[..., Any])


def log_call(func: F) -> F:
    """
    Profiling function decorator

    Placing @log_call at the top of a function or method, results in all calls to that function or method
    being logged at debug level.
    """

    @wraps(func)
    def log_wrapper(*args, **kwargs) -> F:
        _LOG = logging.getLogger()
        _LOG.debug("%s args: %s kwargs: %s", func.__name__, args, kwargs)
        return func(*args, **kwargs)

    return cast(F, log_wrapper)


def time_call(func: F) -> F:
    """
    Profiling function decorator

    Placing @log_call at the top of a function or method, results in all calls to that function or method
    being timed at debug level.

    For debugging or optimisation research only.  Should not occur in mainline code.
    """

    @wraps(func)
    def timing_wrapper(*args, **kwargs) -> Any:
        start: float = monotonic()
        result: Any = func(*args, **kwargs)
        stop: float = monotonic()
        _LOG = logging.getLogger()
        _LOG.debug("%s took: %d ms", func.__name__, int((stop - start) * 1000))
        return result

    return cast(F, timing_wrapper)


def group_by_begin_datetime(
    pnames: list[str] | None = None, truncate_dates: bool = True
) -> GroupBy:
    """
    Returns an ODC GroupBy object, suitable for daily/monthly/yearly/etc statistical/summary data.
    (Or for sub-day time resolution data)
    """
    base_sort_key = lambda ds: ds.time.begin  # noqa: E731
    if pnames:
        index = {pn: i for i, pn in enumerate(pnames)}
        sort_key = lambda ds: (index.get(ds.product.name), base_sort_key(ds))  # noqa: E731
    else:
        sort_key = base_sort_key
    if truncate_dates:
        grp_by = lambda ds: npdt64(  # noqa: E731
            datetime.datetime(
                ds.time.begin.year, ds.time.begin.month, ds.time.begin.day
            ),
            "ns",
        )
    else:
        grp_by = lambda ds: npdt64(  # noqa: E731
            datetime.datetime(
                ds.time.begin.year,
                ds.time.begin.month,
                ds.time.begin.day,
                ds.time.begin.hour,
                ds.time.begin.minute,
                ds.time.begin.second,
            ),
            "ns",
        )
    return GroupBy(
        dimension="time",
        group_by_func=grp_by,
        units="seconds since 1970-01-01 00:00:00",
        sort_key=sort_key,
    )


def group_by_solar(pnames: list[str] | None = None) -> GroupBy:
    base_sort_key = lambda ds: ds.time.begin  # noqa: E731
    if pnames:
        index = {pn: i for i, pn in enumerate(pnames)}
        sort_key = lambda ds: (index.get(ds.product.name), base_sort_key(ds))  # noqa: E731
    else:
        sort_key = base_sort_key
    return GroupBy(
        dimension="time",
        group_by_func=lambda x: npdt64(solar_day(x), "ns"),  # type: ignore[call-overload]
        units="seconds since 1970-01-01 00:00:00",
        sort_key=sort_key,
    )


# NB Epoch is arbitrary - could be any date in past or future.
epoch = npdt64("1970-01-01", "ns")


def group_by_mosaic(pnames: list[str] | None = None) -> GroupBy:
    # Need to sort in reverse date order to ensure that latest data is always rendered.
    # (see definition of _default_fuser() in datacube.storage._loader._default_fuser)
    def reverse_solar_day_sortkey(ds: Dataset) -> npdelt64:
        return epoch - solar_day(ds)

    base_sort_key = lambda ds: ds.time.begin  # noqa: E731
    if pnames:
        index = {pn: i for i, pn in enumerate(pnames)}
        sort_key: Callable[[Dataset], tuple] = lambda ds: (  # noqa: E731
            reverse_solar_day_sortkey(ds),
            index.get(ds.product.name),
            base_sort_key(ds),
        )
    else:
        sort_key = lambda ds: (reverse_solar_day_sortkey(ds), base_sort_key(ds))  # noqa: E731
    return GroupBy(
        dimension="time",
        group_by_func=lambda n: epoch,
        units="seconds since 1970-01-01 00:00:00",
        sort_key=sort_key,
    )


def get_sqlconn(dc: Datacube) -> Connection:
    """
    Extracts a SQLAlchemy database connection from a Datacube object.

    :param dc: An initialised Datacube object
    :return: A SQLAlchemy database connection object.
    """
    # pylint: disable=protected-access
    return dc.index._db._engine.connect()  # type: ignore[attr-defined]


def get_driver_name(index: Index) -> str:
    """Return the driver name for the engine of a datacube index."""
    return index._db._engine.url.get_driver_name()  # type: ignore[attr-defined]


def find_matching_date(dt, dates) -> bool:
    """
    Check for a matching datetime in sorted list, using subday time resolution second-rounding rules.

    :param dt: The date to dun
    :param dates: List of sorted date-times
    :return: True if match found
    """

    def range_of(dt: datetime.datetime) -> tuple[datetime.datetime, datetime.datetime]:
        start = datetime.datetime(
            dt.year, dt.month, dt.day, dt.hour, dt.minute, dt.second, tzinfo=dt.tzinfo
        )
        end = start + datetime.timedelta(seconds=1)
        return start, end

    dt = default_to_utc(dt)
    region = dates
    while region:
        dtlen = len(region)
        splitter = dtlen // 2
        start, end = range_of(region[splitter])
        if dt >= start and dt < end:
            return True
        region = region[0:splitter] if dt < start else region[splitter + 1 :]

    return False


def default_to_utc(dt: datetime.datetime) -> datetime.datetime:
    if not dt.tzinfo:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt
