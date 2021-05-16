# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import datetime

import numpy as np
import xarray as xr

coords = [
    ('x', [
        0.0, 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0,
        10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0, 17.0, 18.0, 19.0,
    ]),
    ('y', [-5.0, -4.0, -3.0, -2.0, -1.0, 0.0, 1.0, 2.0, 3.0, 4.0]),
    ('time', [np.datetime64(datetime.date.today())])
]


def test_function(a, b=2, c=3, **kwargs):
    return [f"a{a}  b{b}  c{c}", kwargs]


def dummy_da(val, name, coords, attrs=None, dtype=np.float64):
    if attrs is None:
        attrs = {}
    dims = [n for n, a in coords]
    data = np.ndarray([len(a) for n, a in coords], dtype=dtype)
    coords = dict(coords)
    data.fill(val)
    output = xr.DataArray(
        data,
        coords=coords,
        dims=dims,
        attrs=attrs,
        name=name,
    )
    return output


def dim1_da(name, vals, coords, with_time=True, attrs=None):
    if len(vals) != len(coords):
        raise Exception("vals and coords must match len")
    if attrs is None:
        attrs = {}
    dims = ["dim"]
    shape = [len(coords)]
    coords = {
        'dim': coords,
    }
    if with_time:
        dims.append("time")
        coords["time"] = [np.datetime64(datetime.date.today())]
        shape.append(1)
    buff_arr = np.array(vals)
    data = np.ndarray(shape, buffer=buff_arr, dtype=buff_arr.dtype)
    output = xr.DataArray(
        data,
        coords=coords,
        dims=dims,
        attrs=attrs,
        name=name,
    )
    return output

