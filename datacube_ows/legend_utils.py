# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import io
from typing import Optional

import requests
from PIL import Image


def get_image_from_url(url: str) -> Optional[Image.Image]:
    """
    Fetch image a png from external URL, and return it as an Image.

    :param url:  A URL pointing to some png image
    :return: A PIL image object (OR None if the url does not return a PNG image)
    """
    r = requests.get(url, timeout=1)
    if r.status_code == 200 and r.headers['content-type'] == 'image/png':
        bytesio = io.BytesIO()
        bytesio.write(r.content)
        bytesio.seek(0)
        return Image.open(bytesio)
    return None
