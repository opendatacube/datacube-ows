import os

import pytest

from datacube_ows.config_utils import OWSMessageFile
from datacube_ows.ows_configuration import ConfigException

src_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def test_good_msg_file(monkeypatch):
    monkeypatch.chdir(src_dir)
    with open("tests/msg/good.po", "r") as fp:
        msg = OWSMessageFile(fp)
    assert msg["foo.bar.baz"] == "Single line msgstr"
    assert msg["tic.tac.toe"] == "\nA multi-line string that continues\nAcross line-breaks.\n"


def test_double_msgid_file(monkeypatch):
    monkeypatch.chdir(src_dir)
    with open("tests/msg/double_msgid.po", "r") as fp:
        with pytest.raises(ConfigException) as e:
            msg = OWSMessageFile(fp)
    assert "Unexpected msgid line in message file: at line " in str(e.value)


def test_duplicate_msgid_file(monkeypatch):
    monkeypatch.chdir(src_dir)
    with open("tests/msg/duplicate_msgid.po", "r") as fp:
        with pytest.raises(ConfigException) as e:
            msg = OWSMessageFile(fp)
    assert "Duplicate msgid: at line " in str(e.value)


def test_double_msgstr_file(monkeypatch):
    monkeypatch.chdir(src_dir)
    with open("tests/msg/double_msgstr.po", "r") as fp:
        with pytest.raises(ConfigException) as e:
            msg = OWSMessageFile(fp)
    assert "Badly formatted multi-line msgstr: at line " in str(e.value)


def test_missing_msgid_file(monkeypatch):
    monkeypatch.chdir(src_dir)
    with open("tests/msg/missing_msgid.po", "r") as fp:
        with pytest.raises(ConfigException) as e:
            msg = OWSMessageFile(fp)
    assert "msgstr without msgid: at line" in str(e.value)


def test_untagged_str_file(monkeypatch):
    monkeypatch.chdir(src_dir)
    with open("tests/msg/untagged_string.po", "r") as fp:
        with pytest.raises(ConfigException) as e:
            msg = OWSMessageFile(fp)
    assert "untagged string: at line " in str(e.value)


def test_multiline_msgid_file(monkeypatch):
    monkeypatch.chdir(src_dir)
    with open("tests/msg/multiline_msgid.po", "r") as fp:
        with pytest.raises(ConfigException) as e:
            msg = OWSMessageFile(fp)
    assert "Multiline msgids not supported by OWS: at line " in str(e.value)

