mixed_1 = {
    "include": "tests/cfg/simple.json",
    "type": "json"
}


mixed_2 = {
    "test": 5224,
    "subtest": {
        "include": "tests/cfg/simple.json",
        "type": "json"
    }
}

mixed_3 = {
    "test": 2634,
    "subtest": {
        "test_py": {
            "include": "tests.cfg.simple.simple",
            "type": "python"
        },
        "test_json": {
            "include": "tests/cfg/simple.json",
            "type": "json"
        }
    }
}