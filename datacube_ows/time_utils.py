# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import datetime
import logging
from typing import Optional

from datacube.model import Dataset
from dateutil.parser import parse
from odc.geo import CRS, Geometry
from odc.geo.geobox import GeoBox
from pytz import timezone, utc
from timezonefinder import TimezoneFinder

from datacube_ows.config_utils import OWSExtensibleConfigEntry

_LOG: logging.Logger = logging.getLogger(__name__)
tf = TimezoneFinder(in_memory=True)


class NoTimezoneException(Exception):
    """Exception, raised internally if no timezone can be found"""


def dataset_center_time(dataset: Dataset) -> datetime.datetime:
    """
    Determine a center_time for the dataset

    Use metadata time if possible as this is what WMS uses to calculate its temporal extents
    datacube-core center time accessed through the dataset API is calculated and may
    not agree with the metadata document.

    :param dataset:  An ODC dataset.
    :return: A datetime object representing the datasets center time
    """
    center_time: datetime.datetime = dataset.center_time
    try:
        metadata_time: str = dataset.metadata_doc['extent']['center_dt']
        center_time = parse(metadata_time)
    except KeyError:
        try:
            metadata_time = dataset.metadata_doc['properties']['dtr:start_datetime']
            center_time = parse(metadata_time)
        except KeyError:
            pass
    return center_time


def solar_date(dt: datetime.datetime, tz: datetime.tzinfo) -> datetime.date:
    """
    Convert a datetime to a new timezone, and evalute as a date.

    :param dt: A datetime in an aribitrary timezone.
    :param tz: The timezone to evaluate the date in.
    :return: A date object.
    """
    return dt.astimezone(tz).date()


def local_date(ds: Dataset, tz: datetime.tzinfo | None =  None) -> datetime.date:
    """
    Calculate the local (solar) date for a dataset.

    :param ds: An ODC dataset object
    :param tz: (optional) A timezone object. If not provided, determine the timezone from extent of the dataset.
    :return: A date object.
    """
    dt_utc: datetime.datetime = dataset_center_time(ds)
    if not tz:
        tz = tz_for_geometry(ds.extent)
    return solar_date(dt_utc, tz)


def tz_for_dataset(ds: Dataset) -> datetime.tzinfo:
    """
    Determine the timezone for a dataset (using it's extent)

    :param ds: An ODC dataset object
    :return: A timezone object
    """
    return tz_for_geometry(ds.extent)


def tz_for_coord(lon: float | int, lat: float | int) -> datetime.tzinfo:
    """
    Determine the Timezone for given lat/long coordinates

    :param lon: Longitude, in degress
    :param lat: Latitude, in degrees
    :return: A timezone object
    :raises: NoTimezoneException
    """
    try:
        tzn: Optional[str] = tf.timezone_at(lng=lon, lat=lat)
    except Exception as e:
        # Generally shouldn't happen - a common symptom of various geographic and timezone related bugs
        _LOG.warning("Timezone detection failed for lat %f, lon %s (%s)", lat, lon, str(e))
        raise
    if not tzn:
        raise NoTimezoneException("tz find failed.")
    return timezone(tzn)


def local_solar_date_range(geobox: GeoBox, date: datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
    """
    Converts a date to a local solar date datetime range.

    :param geobox: Geometry used to determine the appropriate timezone for local date conversion
    :param date: A date object
    :return: A tuple of two UTC datetime objects, spanning 1 second shy of 24 hours.
    """
    tz: datetime.tzinfo = tz_for_geometry(geobox.geographic_extent)
    start = datetime.datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=tz)
    end = datetime.datetime(date.year, date.month, date.day, 23, 59, 59, tzinfo=tz)
    return (start.astimezone(utc), end.astimezone(utc))


def month_date_range(date: datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
    """
    Take a month from a date and convert to a one month long UTC datetime range encompassing the month.

    Ignores timezone effects - suitable for statistical/summary data

    :param date: A date or datetime object to take the month and year from
    :return: A tuple of two UTC datetime objects, delimiting an entire calendar month.
    """
    start = datetime.datetime(date.year, date.month, 1, 0, 0, 0, tzinfo=utc)
    y: int = date.year
    m: int = date.month + 1
    if m == 13:
        m = 1
        y = y + 1
    end = datetime.datetime(y, m, 1, 0, 0, 0, tzinfo=utc) - datetime.timedelta(days=1)
    return start, end


def year_date_range(date: datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
    """
    Convert a date to a UTC datetime range encompassing the calendar year including the date.

    Ignores timezone effects - suitable for statistical/summary data

    :param date: A date or datetime object to take the year from
    :return: A tuple of two UTC datetime objects, delimiting an entire calendar year.
    """
    start = datetime.datetime(date.year, 1, 1, 0, 0, 0, tzinfo=utc)
    end = datetime.datetime(date.year, 12, 31, 23, 59, 59, tzinfo=utc)
    return start, end


def day_summary_date_range(date: datetime.date) -> tuple[datetime.datetime, datetime.datetime]:
    """
    Convert a date to a UTC datetime range encompassing the calendar date.

    Ignores timezone effects - suitable for statistical/summary data

    :param date: A date or datetime object to take the day, month and year from
    :return: A tuple of two UTC datetime objects, delimiting a calendar day.
    """
    start = datetime.datetime(date.year, date.month, date.day, 0, 0, 0, tzinfo=utc)
    end = datetime.datetime(date.year, date.month, date.day, 23, 59, 59, tzinfo=utc)
    return start, end


def tz_for_geometry(geom: Geometry) -> datetime.tzinfo:
    """
    Determine the timezone from a geometry.  Be clever if we can,
    otherwise use a minimal timezone based on the longitude.

    :param geom: A geometry object
    :return: A timezone object
    """
    crs_geo = CRS("EPSG:4326")
    geo_geom: Geometry = geom.to_crs(crs_geo)
    centroid: Geometry = geo_geom.centroid
    try:
        # 1. Try being smart with the centroid of the geometry
        return tz_for_coord(centroid.coords[0][0], centroid.coords[0][1])
    except NoTimezoneException:
        pass
    for pt in geo_geom.boundary.coords:
        try:
            # 2. Try being smart all the points in the geometry
            return tz_for_coord(pt[0], pt[1])
        except NoTimezoneException:
            pass
    # 3. Meh, just use longitude
    offset = round(centroid.coords[0][0] / 15.0)
    return datetime.timezone(datetime.timedelta(hours=offset))


def rolling_window_ndays(
        available_dates: list[datetime.datetime],
        layer_cfg: OWSExtensibleConfigEntry,
        ndays: int = 6) -> tuple[datetime.datetime, datetime.datetime]:
    idx = -ndays
    days = available_dates[idx:]
    start, _ = layer_cfg.search_times(days[idx])
    _, end = layer_cfg.search_times(days[-1])
    return (start, end)
