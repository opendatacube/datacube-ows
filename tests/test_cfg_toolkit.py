from datacube_ows.config_toolkit import deepinherit

def test_inherit():
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
