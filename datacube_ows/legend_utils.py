# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import io

import requests
from PIL import Image


def get_image_from_url(url):
    foo = requests.get
    r = requests.get(url, timeout=1)
    if r.status_code == 200 and r.headers['content-type'] == 'image/png':
        bytesio = io.BytesIO()
        bytesio.write(r.content)
        bytesio.seek(0)
        return Image.open(bytesio)
    return None
