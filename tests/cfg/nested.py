

nested = {
    "include": "tests.cfg.simple.simple",
    "type": "python",
}

nested_1 = [
    {
        "test": 8888,
    },
    {
        "include": "tests.cfg.simple.simple1",
        "type": "python"
    }
]

nested_2 = {
    "test": 3424,
    "subtest": {
        "include": "tests.cfg.simple.simple2",
        "type": "python"
    }
}

nested_3 = {
    "test": 233,
    "things": [
        {
            "test": 2562,
            "thing": None
        },
        {
            "test": 2563,
            "thing": {
                "include": "tests.cfg.simple.simple",
                "type": "python"
            }
        },
        {
            "test": 2564,
            "thing": {
                "include": "tests.cfg.simple.simple3",
                "type": "python"
            }
        },
    ]
}

nested_4 = {
    "test": 222,
    "things": [
        {
            "test": 2572,
            "thing": None
        },
        {
            "test": 2573,
            "thing": {
                "include": "tests.cfg.simple.simple",
                "type": "python"
            }
        },
        {
            "test": 2574,
            "thing": {
                "include": "tests.cfg.nested.nested_3",
                "type": "python"
            }
        },
    ]
}

infinite_1 = {
    "include": "tests.cfg.nested.infinite_1",
    "type": "python"
}


infinite_2 = {
    "test": 7777,
    "subtest": {
        "include": "tests.cfg.nested.infinite_2a",
        "type": "python"
    }
}


infinite_2a = {
    "test": 7778,
    "subtest": {
        "include": "tests.cfg.nested.infinite_2b",
        "type": "python"
    }
}


infinite_2b = {
    "test": 7779,
    "subtest": {
        "include": "tests.cfg.nested.infinite_2",
        "type": "python"
    }
}


