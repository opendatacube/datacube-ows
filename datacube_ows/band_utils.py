# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from __future__ import division

import numpy

# Style index functions


def scale_data(imgband_data, scale_from, scale_to):
    sc_min, sc_max = scale_from
    tc_min, tc_max = scale_to
    clipped = imgband_data.clip(sc_min, sc_max)
    normalised = (clipped - sc_min) / (sc_max - sc_min)
    scaled = normalised * (tc_max - tc_min)
    return scaled + tc_min


def scalable(undecorated):
    def decorated(*args, **kwargs):
        scale_from = kwargs.pop("scale_from", None)
        scale_to = kwargs.pop("scale_to", None)
        if scale_from is not None and scale_to is None:
            scale_to = [0, 255]
        unscaled = undecorated(*args, **kwargs)
        if scale_from:
            return scale_data(unscaled, scale_from, scale_to)
        return unscaled

    return decorated


def band_modulator(undecorated):
    def decorated(data, *args, **kwargs):
        band_mapper = kwargs.get("band_mapper", None)
        mult_band = kwargs.pop("mult_band", None)
        raw_data = undecorated(data, *args, **kwargs)
        if mult_band and band_mapper:
            mult_band = band_mapper(mult_band)
        if mult_band:
            return data[mult_band] * raw_data
        return raw_data
    return decorated

def pre_scaled_band(data, band, scale, offset):
    # Pre-scale a band as `data[band] * scale + offset`
    return data[band] * scale + offset

def sum_bands(data, band1, band2, band_mapper=None):
    if band_mapper:
        band1 = band_mapper(band1)
        band2 = band_mapper(band2)
    return data[band1] + data[band2]

def pre_scaled_sum_bands(
    data, band1, band2,
    scale1=1.0, offset1=0.0,
    scale2=1.0, offset2=0.0,
    band_mapper=None):
    # Calculate the sum of two bands, after pre-scaling them with a scale and offset
    if band_mapper:
        band1 = band_mapper(band1)
        band2 = band_mapper(band2)
    # Pre-scaled bands data
    data1 = pre_scaled_band(data, band1, scale1, offset1)
    data2 = pre_scaled_band(data, band2, scale2, offset2)
    return data1 + data2


def delta_bands(data, band1, band2, band_mapper=None):
    if band_mapper:
        band1 = band_mapper(band1)
        band2 = band_mapper(band2)
    typ1 = data[band1].dtype
    typ2 = data[band2].dtype
    if typ1.name.startswith('uint'):
        nodata = data[band1].nodata
        data[band1] = data[band1].astype('int32')
        data[band1].attrs["nodata"] = nodata
    if typ2.name.startswith('uint'):
        nodata = data[band2].nodata
        data[band2] = data[band2].astype('int32')
        data[band2].attrs["nodata"] = nodata
    # if typ1.name.startswith('uint') or typ2.name.startswith('uint'):
        # data = data.astype('int32', copy=False)
    return data[band1] - data[band2]

def pre_scaled_delta_bands(
    data, band1, band2,
    scale1=1.0, offset1=0.0,
    scale2=1.0, offset2=0.0,
    band_mapper=None):
    # Calculate the difference between two bands, after pre-scaling them with a scale
    # and offset
    if band_mapper:
        band1 = band_mapper(band1)
        band2 = band_mapper(band2)
    typ1 = data[band1].dtype
    typ2 = data[band2].dtype
    if typ1.name.startswith('uint'):
        nodata = data[band1].nodata
        data[band1] = data[band1].astype('int32')
        data[band1].attrs["nodata"] = nodata
    if typ2.name.startswith('uint'):
        nodata = data[band2].nodata
        data[band2] = data[band2].astype('int32')
        data[band2].attrs["nodata"] = nodata
    # if typ1.name.startswith('uint') or typ2.name.startswith('uint'):
        # data = data.astype('int32', copy=False)
        # Pre-scaled bands data
    data1 = pre_scaled_band(data, band1, scale1, offset1)
    data2 = pre_scaled_band(data, band2, scale2, offset2)
    return data1 - data2

# N.B. Modifying scale_to would be dangerous - don't do it.
# pylint: disable=dangerous-default-value
@scalable
def norm_diff(data, band1, band2, band_mapper=None):
    # Calculate a normalised difference index.
    return delta_bands(data, band1, band2, band_mapper) / sum_bands(data, band1, band2, band_mapper)

@scalable
def pre_scaled_norm_diff(data, band1, band2,
                         scale1=1.0, offset1=0.0,
                         scale2=1.0, offset2=0.0,
                         band_mapper=None,):
    # Calculate a normalised difference index, after scaling the input bands with a
    # scale and offset
    return (pre_scaled_delta_bands(
        data, band1, band2, scale1, offset1, scale2, offset2, band_mapper) /
        pre_scaled_sum_bands(
            data, band1, band2, scale1, offset1, scale2, offset2, band_mapper)
    )
@scalable
def constant(data, band, const, band_mapper=None):
    # Covert an xarray for a flat constant.
    # Useful for displaying mask extents as a flat colour and debugging.
    # params is assumed to be a tuple containing a constant value and a band name/alias.

    if band_mapper:
        band = band_mapper(band)
    return data[band] * 0.0 + const


@scalable
def single_band(data, band, band_mapper=None):
    # Use the raw value of a band directly as the index function.

    if band_mapper:
        band = band_mapper(band)
    return data[band]


@scalable
def band_quotient(data, band1, band2, band_mapper=None):
    if band_mapper:
        band1 = band_mapper(band1)
        band2 = band_mapper(band2)
    return data[band1] / data[band2]


@scalable
def band_quotient_sum(data, band1a, band1b, band2a, band2b, band_mapper=None):
    return band_quotient(data, band1a, band1b, band_mapper) + band_quotient(data, band2a, band2b, band_mapper)


@scalable
def sentinel2_ndci(data, b_red_edge, b_red, b_green, b_swir, band_mapper=None):
    red_delta = delta_bands(data, b_red_edge, b_red, band_mapper)
    red_sum = sum_bands(data, b_red_edge, b_red, band_mapper)
    mndwi = norm_diff(data, b_green, b_swir, band_mapper)

    return red_delta / red_sum.where(mndwi > 0.1)


def multi_date_delta(data, time_direction=-1):
    data1, data2 = (data.sel(time=dt) for dt in data.coords["time"].values)

#    data1, data2 = data.values.item(0), data.values.item(1)
    if time_direction >= 0:
        return data1 - data2
    else:
        return data2 - data1

def multi_date_pass(data):
    return data


@band_modulator
@scalable
def single_band_log(data, band, scale_factor, exponent, band_mapper=None):
    if band_mapper:
        band = band_mapper(band)
    d = data[band]
    return scale_factor * ((d ** exponent) - 1.0)


@band_modulator
@scalable
def single_band_arcsec(data, band, band_mapper=None):
    if band_mapper:
        band = band_mapper(band)
    d = data[band]
    return numpy.arccos(1 / (d + 1))


@band_modulator
@scalable
def single_band_offset_log(data, band, scale=1.0, offset=None, band_mapper=None):
    if band_mapper:
        band = band_mapper(band)
    d = data[band]
    if offset is not None:
        d = data[band] * scale + offset
        unscaled = numpy.log(d)
    else:
        unscaled = numpy.log1p(d * scale)
    return unscaled


@scalable
def radar_vegetation_index(data, band_hv, band_hh, band_mapper=None):
    if band_mapper:
        band_hv = band_mapper(band_hv)
        band_hh = band_mapper(band_hh)
    hv_sq = data[band_hv] * data[band_hv]
    hh_sq = data[band_hh] * data[band_hh]
    return (hv_sq * 4.0) / (hh_sq + hv_sq)
