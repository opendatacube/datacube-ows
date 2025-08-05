# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from collections.abc import Callable

import xarray as xr


def trivial_identity(x):
    return x


def legacy_finfo_data(data):
    return data


def new_finfo_vars(data, ds) -> list:
    return list(data.data_vars.keys())


def new_finfo_platform(data, ds):
    return ds.metadata.platform


def new_twodate_finfo(data: xr.Dataset, band, band_mapper: Callable | None = None) -> xr.Dataset:
    if band_mapper is not None:
        band = band_mapper(band)
    data1, data2 = (data.sel(time=dt) for dt in data.coords["time"].values)
    return data2[band].item() - data1[band].item()
