# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0


def test_index_driver_cache():
    from datacube_ows.index.driver import ows_index_drivers
    a = 2
    a = a+ 1
    assert "postgres" in ows_index_drivers()
    assert "postgis" in ows_index_drivers()
    from datacube_ows.index.driver import ows_index_driver_by_name
    assert ows_index_driver_by_name("postgres") is not None
