# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from pyproj import CRS

SUPPORTED_CRS = [
   'EPSG:3857', # Web Mercator
   'EPSG:4326', # WGS-84
   'EPSG:3577', # GDA-94
   'EPSG:3111', # VicGrid94
   'EPSG:32648', # WGS 84 / Cambodiacube
   'ESRI:102022', # Africa
   # 'EPSG:102022', # Depreciated Africa
   'EPSG:6933', # Africa
]


def test_pyproj_crs():
   for crs_string in SUPPORTED_CRS:
      try:
         crs = CRS(crs_string)
         assert crs is not None
      except:
         assert False

