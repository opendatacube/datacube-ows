# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from datacube_ows.config_toolkit import deepinherit


def test_deepinherit_shallow():
    parent = {
        "a": 72,
        "b": "eagle",
        "c": False
    }

    child = {
        "a": 365
    }
    child = deepinherit(parent, child)
    assert child['a'] == 365
    assert child["b"] == "eagle"
    assert not child["c"]


def test_deepinherit_deep():
    parent = {
        "a": 72,
        "b": {
            "fruit": "grapes",
            "spice": "cummin",
            "cake": "chocolate",
            "y": ["some", "body", "once"],
            "z": [44, 42, 53],
            "c": {
                "foo": "bar",
                "wing": "wang"
            }
        }
    }

    child = {
        "b": {
            "spice": "nutmeg",
            "c": {
                "wing": "chicken"
            },
            "y": ["told", "me"],
            "z": [11]
        }
    }
    child = deepinherit(parent, child)
    assert child["a"] == 72
    assert child["b"]["spice"] == "nutmeg"
    assert child["b"]["fruit"] == "grapes"
    assert child["b"]["c"]["foo"] == "bar"
    assert child["b"]["c"]["wing"] == "chicken"
    assert child["b"]["z"] == [11]
    assert child["b"]["y"] == ["some", "body", "once", "told", "me"]


def test_array_inheritance():
    inherit_from = {
        "foo": "bar",
        "ding": "dong",
        "bing": "bang",
        "wham": ["a-lam", "a-bing", "bong"],
        "king": {
            "tide": "oceanography",
            "crab": "crustacean",
            "Sick-Nasty": "Spades",
        }
    }
    inherit_to = {
        "foo": "baz",
        "wham": [],
        "king": {
            "Penguin": "Antarctica"
        }
    }
    inherited = deepinherit(inherit_from, inherit_to)
    assert inherited["foo"] == "baz"
    assert inherited["wham"] == []
    assert inherited["king"]["Penguin"] == "Antarctica"
    assert inherited["king"]["tide"] == "oceanography"

    inherit_to["wham"] = ["bim", "bala", "boom"]
    inherited = deepinherit(inherit_from, inherit_to)
    assert "a-bing" in inherited["wham"]
    assert "bim" in inherited["wham"]
