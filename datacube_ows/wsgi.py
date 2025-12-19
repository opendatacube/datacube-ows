# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0


# pylint: skip-file
import os
import sys

# This is the directory of the source code that the web app will run from
sys.path.append("/src")

# The location of the datacube config file.
if os.path.isfile("/src/odc/.datacube.conf.local"):
    os.environ.setdefault("ODC_CONFIG_PATH", "/src/odc/.datacube.conf.local")

from datacube_ows import __version__, create_app

application = create_app()


def main() -> None:
    if "--version" in sys.argv:
        print("Open Data Cube Open Web Services (datacube-ows) version", __version__)
        exit(0)
    application.run()


if __name__ == "__main__":
    main()
