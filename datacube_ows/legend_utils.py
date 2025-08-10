# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import io
import logging

from PIL import Image
from requests import Session
from requests.sessions import HTTPAdapter
from urllib3 import Retry

from datacube_ows.ogc_exceptions import WMSException

_LOG: logging.Logger = logging.getLogger(__name__)

RETRY_CODES = frozenset([413, 429, 500, 502, 503])

RETRIES = Retry(
    total=10,
    backoff_factor=0.5,
    raise_on_status=False,
    status_forcelist=RETRY_CODES,
)


def make_session(max_retries: Retry) -> Session:
    session = Session()
    session.mount("http://", HTTPAdapter(max_retries=max_retries))
    session.mount("https://", HTTPAdapter(max_retries=max_retries))
    return session


retrying_requests = make_session(RETRIES)


def get_image_from_url(url: str) -> Image.Image | None:
    """
    Fetch image a png from external URL, and return it as an Image.

    :param url:  A URL pointing to some png image
    :return: A PIL image object (OR None if the url does not return a PNG image)
    """
    r = retrying_requests.get(url)
    if r.status_code != 200:
        raise WMSException(
            f"Could not retrieve legend - external URL is failing with http code {r.status_code}"
        )
    if r.headers["content-type"] != "image/png":
        _LOG.warning(
            "External legend has MIME type %s. OWS strongly recommends PNG format for legend images.",
            r.headers["content-type"],
        )
    bytesio = io.BytesIO()
    bytesio.write(r.content)
    bytesio.seek(0)
    return Image.open(bytesio)
