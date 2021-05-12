# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from copy import deepcopy


def deepinherit(parent, child):
    expanded = deepcopy(parent)
    deepupdate(expanded, child)
    return expanded


def deepupdate(target, src):
    for k in src:
        if isinstance(src[k], dict):
            if k not in target:
                target[k] = {}
            # recurse dictionary
            deepupdate(target[k], src[k])
        elif isinstance(src[k], str):
            # Use child's version of str
            target[k] = src[k]
        else:
            try:
                iter(src[k])
                # non-str iterable
                if not src[k]:
                    # Empty list - replace target list
                    target[k] = []
                elif isinstance(src[k][0], int) or isinstance(src[k][0], float):
                    # Array of numbers or floats - replace target list
                    target[k] = src[k]
                else:
                    # iterables of other types - append child to parent
                    if k in target:
                        target[k] = target[k] + src[k]
                    else:
                        target[k] = src[k]
            except TypeError:
                # Non-iterable - Use child's version
                target[k] = src[k]


