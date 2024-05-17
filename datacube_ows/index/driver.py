# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

from threading import Lock
from typing import Optional

from datacube.drivers.driver_cache import load_drivers


TYPE_CHECKING = False
if TYPE_CHECKING:
    from datacube_ows.index.api import OWSAbstractIndexDriver

cache_lock = Lock()


class OWSIndexDriverCache:
    _instance = None
    _initialised = False
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            with cache_lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, group: str) -> None:
        with cache_lock:
            if not self._initialised:
                self._initialised = True
                self._drivers = load_drivers(group)
    def __call__(self, name: str) -> Optional["OWSAbstractIndexDriver"]:
        """
        :returns: None if driver with a given name is not found

        :param name: Driver name
        :return: Returns IndexDriver
        """
        return self._drivers.get(name, None)

    def drivers(self) -> list[str]:
        """ Returns list of driver names
        """
        return list(self._drivers.keys())


def ows_index_drivers() -> list[str]:
    return OWSIndexDriverCache("datacube_ows.plugins.index").drivers()


def ows_index_driver_by_name(name: str) -> Optional["OWSAbstractIndexDriver"]:
    return OWSIndexDriverCache("datacube_ows.plugins.index")(name)
