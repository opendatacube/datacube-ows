# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

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
