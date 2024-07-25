# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

def trivial_identity(x):
    return x


def legacy_finfo_data(data):
    return data


def new_finfo_vars(data, ds):
    return list(data.data_vars.keys())


def new_finfo_platform(data, ds):
    return ds.metadata.platform


def new_twodate_finfo(data, band, band_mapper=None):
    if band_mapper is not None:
        band = band_mapper(band)
    data1, data2 = (data.sel(time=dt) for dt in data.coords["time"].values)
    return data2[band].item() - data1[band].item()
