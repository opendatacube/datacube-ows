# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import json
from urllib.parse import urlparse

from flask import Request, request, render_template

from datacube_ows.config_utils import CFG_DICT
from datacube_ows.ows_configuration import OWSConfig, get_config

FlaskResponse = tuple[str | bytes, int, dict[str, str]]


def resp_headers(d: dict[str, str]) -> dict[str, str]:
    """
    Take a dictionary of http response headers and all required response headers from the configuration.

    :param d:
    :return:
    """
    from datacube_ows.ows_configuration import get_config
    return get_config().response_headers(d)


def parse_for_base_url(url: str) -> str:
    """
    Extract the base URL from a URL

    :param url: A URL
    :return: The base URL (path and parameters stripped)
    """
    parsed = urlparse(url)
    parsed = (parsed.netloc + parsed.path).rstrip("/")
    return parsed


def get_service_base_url(allowed_urls: list[str] | str, request_url: str) -> str:
    """
    Choose the base URL to advertise in XML.

    :param allowed_urls: A list of allowed URLs, or a single allowed URL.
    :param request_url: The URL the incoming request came from
    :return: Return one of the allowed URLs.  Either one that seems to match the request, or the first in the list
    """
    if isinstance(allowed_urls, str):
        return allowed_urls
    parsed_request_url = parse_for_base_url(request_url)
    parsed_allowed_urls = [parse_for_base_url(u) for u in allowed_urls]
    try:
        idx: int | None = parsed_allowed_urls.index(parsed_request_url)
    except ValueError:
        idx = None
    url = allowed_urls[idx] if idx is not None else allowed_urls[0]
    # template includes tailing /, strip any trail slash here to avoid duplicates
    url = url.rstrip("/")
    return url


def capture_headers(req: Request,
                    args_dict: dict[str, str | None]) -> dict[str, str | None]:
    """
    Capture significant flask metadata into the args dictionary

    :param req: A Flask request
    :param args_dict: A Flask args dictionary
    :return:
    """
    args_dict['referer'] = req.headers.get('Referer', None)
    args_dict['origin'] = req.headers.get('Origin', None)
    args_dict['requestid'] = req.environ.get("FLASK_REQUEST_ID")
    args_dict['host'] = req.headers.get('Host', None)
    args_dict['url_root'] = req.url_root

    return args_dict


def cache_control_headers(max_age: int) -> dict[str, str]:
    if max_age <= 0:
        return {"cache-control": "no-cache"}
    else:
        return {"cache-control": f"max-age={max_age}"}


def lower_get_args() -> dict[str, str]:
    """
    Return Flask request arguments, with argument names converted to lower case.

    Get parameters in WMS are case-insensitive, and intended to be single use.
    Spec does not specify which instance should be used if a parameter is provided more than once.
    This function uses the LAST instance.
    """
    d = {}
    for k in request.args.keys():
        kl = k.lower()
        for v in request.args.getlist(k):
            d[kl] = v
    return d


def json_response(result: CFG_DICT, cfg: OWSConfig | None = None) -> FlaskResponse:
    if not cfg:
        cfg = get_config()
    assert cfg is not None  # for type checker
    return json.dumps(result), 200, cfg.response_headers({"Content-Type": "application/json"})


def html_json_response(result: CFG_DICT, cfg: OWSConfig | None = None) -> FlaskResponse:
    if not cfg:
        cfg = get_config()
    assert cfg is not None  # for type checker
    html_content = render_template("html_feature_info.html", result=result)
    return html_content, 200, cfg.response_headers({"Content-Type": "text/html"})


def png_response(body: bytes, cfg: OWSConfig | None = None, extra_headers: dict[str, str] | None = None) -> FlaskResponse:
    if not cfg:
        cfg = get_config()
    assert cfg is not None  # For type checker
    if extra_headers is None:
        extra_headers = {}
    headers = {"Content-Type": "image/png"}
    headers.update(extra_headers)
    headers = cfg.response_headers(headers)
    return body, 200, cfg.response_headers(headers)
