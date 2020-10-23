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
            "y": [ "some", "body", "once" ],
            "z": [ 44, 42, 53 ],
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
            "y": [ "told", "me" ],
            "z": [ 11 ]
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