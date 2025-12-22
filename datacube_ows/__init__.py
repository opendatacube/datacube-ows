# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

try:
    from ._version import version as __version__
except ImportError:
    # Default version number.
    # Will only be used when running datacube-ows direct from source code (not properly installed)
    __version__ = "1.9.7"

from .startup_utils import create_app

__all__ = ["__version__", "create_app"]
