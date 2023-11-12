# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from datacube import Datacube

from datacube_ows.cube_pool import get_cube


def test_basic_cube_pool():
    dc_1 = get_cube(app="test")
    dc_2 = get_cube(app="test")
    assert dc_1 == dc_2
    dc_unalloc = Datacube(app="test")
    assert dc_1 != dc_unalloc
