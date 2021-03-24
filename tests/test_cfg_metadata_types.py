import pytest

from datacube_ows.ogc_utils import ConfigException
from datacube_ows.ows_configuration import AttributionCfg, SuppURL


def test_cfg_attrib_empty():
    attrib = AttributionCfg.parse({})
    assert attrib is None


def test_cfg_attrib_emptyfail():
    with pytest.raises(ConfigException) as excinfo:
        attrib = AttributionCfg.parse({"foo": "bar"})
    assert "At least one" in str(excinfo.value)


def test_cfg_attrib_title_only():
    attrib = AttributionCfg.parse({"title": "Sir"})
    assert attrib.title == "Sir"
    assert attrib.logo_width is None
    assert attrib.url is None


def test_cfg_attrib_url_only():
    attrib = AttributionCfg.parse(
        {
            "url": "http://test.url/path/name",
        }
    )
    assert attrib.title is None
    assert attrib.logo_width is None
    assert attrib.url == "http://test.url/path/name"


def test_cfg_attrib_minimal_logo_only():
    attrib = AttributionCfg.parse(
        {"logo": {"url": "http://test.url/path/img.png", "format": "image/png"}}
    )
    assert attrib.title is None
    assert attrib.url is None
    assert attrib.logo_url == "http://test.url/path/img.png"
    assert attrib.logo_fmt == "image/png"
    assert attrib.logo_width is None


def test_cfg_attrib_logo_requirements():
    with pytest.raises(ConfigException) as excinfo:
        attrib = AttributionCfg.parse(
            {
                "logo": {
                    "url": "http://test.url/path/img.png",
                }
            }
        )
    assert "url and format" in str(excinfo.value)
    with pytest.raises(ConfigException) as excinfo:
        attrib = AttributionCfg.parse({"logo": {"format": "image/png"}})
    assert "url and format" in str(excinfo.value)


def test_cfg_attrib_logo_options():
    attrib = AttributionCfg.parse(
        {
            "logo": {
                "url": "http://test.url/path/img.png",
                "format": "image/png",
                "width": 200,
            }
        }
    )
    assert attrib.logo_url == "http://test.url/path/img.png"
    assert attrib.logo_fmt == "image/png"
    assert attrib.logo_width == 200
    assert attrib.logo_height is None
    attrib = AttributionCfg.parse(
        {
            "logo": {
                "url": "http://test.url/path/img.png",
                "format": "image/png",
                "width": 200,
                "height": 300,
            }
        }
    )
    assert attrib.logo_height == 300


def test_cfg_attrib_all_flds(minimal_dc):
    attrib = AttributionCfg.parse(
        {
            "title": "Boogie Woogie",
            "url": "http://test.url/path",
            "logo": {
                "url": "http://test.url/path/img.png",
                "format": "image/png",
                "width": 200,
                "height": 150,
            },
        }
    )
    assert attrib.title == "Boogie Woogie"
    assert attrib.url == "http://test.url/path"
    assert attrib.logo_url == "http://test.url/path/img.png"
    assert attrib.logo_fmt == "image/png"
    assert attrib.logo_width == 200
    assert attrib.logo_height == 150
    attrib.make_ready(minimal_dc)
    assert attrib.ready


def test_surl_empty():
    supps = SuppURL.parse_list(None)
    assert supps == []
    supps = SuppURL.parse_list([])
    assert supps == []


def test_surl_no_url():
    with pytest.raises(KeyError):
        supps = SuppURL.parse_list([{"format": "text/html"}])


def test_surl_no_format():
    with pytest.raises(KeyError):
        supps = SuppURL.parse_list([{"url": "http://test.url/path"}])


def test_surl_full(minimal_dc):
    supps = SuppURL.parse_list(
        [
            {"url": "http://test.url/path", "format": "text/html"},
            {"url": "http://test.url/another_path", "format": "text/plain"},
        ]
    )
    assert len(supps) == 2
    assert supps[0].url == "http://test.url/path"
    assert supps[1].url == "http://test.url/another_path"
    assert supps[0].format == "text/html"
    assert supps[1].format == "text/plain"
    supps[0].make_ready(minimal_dc)
    assert supps[0].ready
    assert not supps[1].ready
