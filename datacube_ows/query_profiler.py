# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
from time import time


class QueryProfiler:
    def __init__(self, active):
        self.active = active
        self._events = {}
        self._stats = {}
        if active:
            self.start_event("query")

    def start_event(self, name):
        if self.active:
            self._events[name] = [time(), None]

    def __setitem__(self, name, val):
        self._stats[name] = val

    def end_event(self, name):
        if self.active:
            if name in self._events:
                self._events[name][1] = time()
            else:
                self._events[name] = [None, time()]

    def profile(self):
        result = {}
        if self.active:
            self.end_event("query")
            result["profile"] = {}
            for name, rng in self._events.items():
                if rng[0] and rng[1]:
                    result["profile"][name] = rng[1] - rng[0]
            result["info"] = self._stats
        return result
