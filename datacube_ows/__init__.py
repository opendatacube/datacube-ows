# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
try:
    from ._version import version as __version__
except ImportError:
    __version__ = "1.8.32+?"
