# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from datacube_ows.cfg_parser_impl import main
from datacube_ows.startup_utils import initialise_debugging

if __name__ == '__main__':
    initialise_debugging()
    main()
