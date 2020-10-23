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

def sum_bands(data, band1, band2, band_mapper=None):
    if band_mapper:
        band1=band_mapper(band1)
        band2=band_mapper(band2)
    return data[band1] + data[band2]


def delta_bands(data, band1, band2, band_mapper=None):
    if band_mapper:
        band1=band_mapper(band1)
        band2=band_mapper(band2)
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


# N.B. Modifying scale_to would be dangerous - don't do it.
# pylint: disable=dangerous-default-value
def norm_diff(data, band1, band2, band_mapper=None, scale_from=None, scale_to=[0,255]):
    # Calculate a normalised difference index.
    unscaled = delta_bands(data, band1,band2, band_mapper) / sum_bands(data, band1, band2, band_mapper)
    if scale_from:
        scaled = scale_data(unscaled, scale_from, scale_to)
    else:
        scaled = unscaled
    return scaled


def constant(data, band, const, band_mapper=None):
    # Covert an xarray for a flat constant.
    # Useful for displaying mask extents as a flat colour and debugging.
    # params is assumed to be a tuple containing a constant value and a band name/alias.

    if band_mapper:
        band = band_mapper(band)
    return data[band] * 0.0 + const


def single_band(data, band, band_mapper=None):
    # Use the raw value of a band directly as the index function.

    if band_mapper:
        band = band_mapper(band)
    return data[band]


def band_quotient(data, band1, band2, band_mapper=None, scale_from=None, scale_to=[0,255]):
    if band_mapper:
        band1=band_mapper(band1)
        band2=band_mapper(band2)
    unscaled = data[band1] / data[band2]
    if scale_from:
        scaled = scale_data(unscaled, scale_from, scale_to)
    else:
        scaled = unscaled
    return scaled


def band_quotient_sum(data, band1a, band1b, band2a, band2b, band_mapper=None):
    return band_quotient(data, band1a, band1b, band_mapper) + band_quotient(data, band2a, band2b, band_mapper)


def sentinel2_ndci(data, b_red_edge, b_red, b_green, b_swir, band_mapper=None):
    red_delta = delta_bands(data, b_red_edge, b_red, band_mapper)
    red_sum = sum_bands(data,b_red_edge, b_red, band_mapper)
    mndwi = norm_diff(data, b_green, b_swir, band_mapper)

    return red_delta / red_sum.where(mndwi > 0.1)


def multi_date_delta(data):
    data1, data2 = (data.sel(time=dt) for dt in data.coords["time"].values)

#    data1, data2 = data.values.item(0), data.values.item(1)
    return data2 - data1


def single_band_log(data, band, scale_factor, exponent, band_mapper=None):
    if band_mapper:
        band = band_mapper(band)
    d = data[band]
    return scale_factor * ( (d ** exponent) - 1.0)


def single_band_arcsec(data, band, scale_from=None, scale_to=None, band_mapper=None):
    if scale_from is not None and scale_to is None:
        scale_to = [0,255]
    if band_mapper:
        band = band_mapper(band)
    d = data[band]
    unscaled = numpy.arccos(1/(d + 1))
    if scale_from:
        return scale_data(unscaled, scale_from, scale_to)
    return unscaled


def single_band_offset_log(data, band, scale=1.0, scale_from=None, scale_to=None, offset=None, band_mapper=None):
    if scale_from is not None and scale_to is None:
        scale_to = [0,255]
    if band_mapper:
        band = band_mapper(band)
    d = data[band]
    if offset is not None:
        d = data[band] + offset
        unscaled =  numpy.log(d*scale)
    else:
        unscaled =  numpy.log1p(d*scale)
    if scale_from:
        return scale_data(unscaled, scale_from, scale_to)
    return unscaled


def radar_vegetation_index(data, band_hv, band_hh, band_mapper=None):
    if band_mapper:
        band_hv = band_mapper(band_hv)
        band_hh = band_mapper(band_hh)
    hv_sq = data[band_hv]*data[band_hv]
    hh_sq = data[band_hh]*data[band_hh]
    return (hv_sq * 4.0) / (hh_sq + hv_sq)

