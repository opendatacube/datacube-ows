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

def sum_bands(data, band1, band2, product_cfg=None):
    if product_cfg:
        band1=product_cfg.band_idx.band(band1)
        band2=product_cfg.band_idx.band(band2)
    return data[band1] + data[band2]


def delta_bands(data, band1, band2, product_cfg=None):
    if product_cfg:
        band1=product_cfg.band_idx.band(band1)
        band2=product_cfg.band_idx.band(band2)
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
def norm_diff(data, band1, band2, product_cfg=None, scale_from=None, scale_to=[0,255]):
    # Calculate a normalised difference index.
    # unscaled = delta_bands(data, band1,band2, product_cfg) / sum_bands(data, band1, band2, product_cfg)
    # delta_data = delta_bands(data, band1,band2, product_cfg)
    # sum_data = sum_bands(data, band1, band2, product_cfg)
    unscaled = delta_bands(data, band1,band2, product_cfg) / sum_bands(data, band1, band2, product_cfg)
    if scale_from:
        scaled = scale_data(unscaled, scale_from, scale_to)
    else:
        scaled = unscaled
    return scaled


def constant(data, band, const, product_cfg=None):
    # Covert an xarray for a flat constant.
    # Useful for displaying mask extents as a flat colour and debugging.
    # params is assumed to be a tuple containing a constant value and a band name/alias.

    if product_cfg:
        band = product_cfg.band_idx.band(band)
    return data[band] * 0.0 + const


def single_band(data, band, product_cfg=None):
    # Use the raw value of a band directly as the index function.

    if product_cfg:
        band = product_cfg.band_idx.band(band)
    return data[band]


def band_quotient(data, band1, band2, product_cfg=None):
    if product_cfg:
        band1=product_cfg.band_idx.band(band1)
        band2=product_cfg.band_idx.band(band2)
    return data[band1] / data[band2]


def band_quotient_sum(data, band1a, band1b, band2a, band2b, product_cfg=None):
    return band_quotient(data, band1a, band1b, product_cfg) + band_quotient(data, band2a, band2b, product_cfg)


def sentinel2_ndci(data, b_red_edge, b_red, b_green, b_swir, product_cfg=None):
    red_delta = delta_bands(data, b_red_edge, b_red, product_cfg)
    red_sum = sum_bands(data,b_red_edge, b_red, product_cfg)
    mndwi = norm_diff(data, b_green, b_swir, product_cfg)

    return red_delta / red_sum.where(mndwi > 0.1)


def multi_date_delta(data):
    data1, data2 = (data.sel(time=dt) for dt in data.coords["time"].values)

#    data1, data2 = data.values.item(0), data.values.item(1)
    return data2 - data1


def single_band_log(data, band, scale_factor, exponent, product_cfg=None):
    if product_cfg:
        band = product_cfg.band_idx.band(band)
    return scale_factor * ( (data[band] ** exponent) - 1.0)


def single_band_offset_log(data, band, offset=None, product_cfg=None):
    if product_cfg:
        band = product_cfg.band_idx.band(band)
    d = data[band]
    if offset is None:
        d = numpy.log1p(d)
    else:
        d = data[band] + offset
    return numpy.log(d)
