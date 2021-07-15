# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import logging
from contextlib import contextmanager
from threading import Lock
from typing import Generator, MutableMapping, Optional

from datacube import Datacube

_LOG: logging.Logger = logging.getLogger(__name__)

# CubePool class
class CubePool:
    """
    A Cube pool is a thread-safe resource pool for managing Datacube objects (which map to database connections).
    """
    # _instances, global mapping of CubePools by app name
    _instances: MutableMapping[str, "CubePool"] = {}

    _cubes_: bool = False
    _cubes_lock_: bool = False

    def __new__(cls, app: str) -> "CubePool":
        """
        Construction of CubePools is managed. Constructing a cubepool for an app string that already has a cubepool
        constructed, returns the existing cubepool, not a new one.
        """
        if app not in cls._instances:
            cls._instances[app] = super(CubePool, cls).__new__(cls)
        return cls._instances[app]

    def __init__(self, app: str) -> None:
        """
        Obtain the cube pool for the nominated app string, or create one if one does not exist yet.

        :param app: The app string used to construct any Datacube objects created by the pool.
        """
        self.app: str = app
        if not self._cubes_:
            self._cubes: MutableMapping[Datacube, bool] = {}
            self._cubes_ = True
        if not self._cubes_lock_:
            self._cubes_lock: Lock = Lock()
            self._cubes_lock_ = True

    def get_cube(self) -> Optional[Datacube]:
        """
        Return a Datacube object.  Either generating a new Datacube, or recycling an unassigned one already in the pool.

        :return:  a Datacube object (or None on error).
        """
        self._cubes_lock.acquire()
        for c, assigned in self._cubes.items():
            if not assigned:
                self._cubes[c] = True
                self._cubes_lock.release()
                return c
        try:
            c = self._new_cube()
            self._cubes[c] = True
        # pylint: disable=broad-except
        except Exception as e:
            _LOG.error("ODC initialisation failed: %s", str(e))
            c = None
        finally:
            self._cubes_lock.release()
        return c

    def release_cube(self, c: Datacube) -> None:
        """
        Return a datacube to the pool for reassignment.

        :param c: A Datacube object originally created by this CubePool and that is no longer required.
        """
        if c not in self._cubes:
            raise Exception("Cannot release non-pool datacube.")
        self._cubes_lock.acquire()
        self._cubes[c] = False
        self._cubes_lock.release()

    def _new_cube(self) -> Datacube:
        return Datacube(app=self.app)

    def __len__(self) -> int:
        return len(self._cubes)


# Lowlevel CubePool API
def get_cube(app: str = "ows") -> Optional[Datacube]:
    """
    Obtain a Datacube object from the appropriate pool

    :param app: The app pool to use - defaults to "ows".
    :return: a Datacube object (or None) in case of database error.
    """
    pool = CubePool(app=app)
    return pool.get_cube()


def release_cube(c: Datacube, app: str = "ows") -> None:
    """
    Return a Datacube to the pool for reuse.

    :param c: a Datacube object, allocated by a previous call to get_cube(app).
    :param app: the name of the pool to return the cube from - defaults to "ows"
    """
    pool = CubePool(app=app)
    return pool.release_cube(c)


def pool_size(app: str = "ows") -> int:
    """
    Return the total number of cubes (available and allocated) in a particular pool.

    :param app: The name of the pool to measure - defaults to "ows"
    :return: the total number of cubes in the pool.
    """
    pool = CubePool(app=app)
    return len(pool)


# High Level Cube Pool API
@contextmanager
def cube(app: str = "ows") -> Generator[Optional["datacube.api.core.Datacube"], None, None]:
    """
    Context manager for using a Datacube object from a pool.

    E.g.

    with cube() as dc:
         # Do stuff that needs a datacube object here.
         data = dc.load(.....)


    :param app: The pool to obtain the app from - defaults to "ows".
    :return: A Datacube context manager.
    """
    dc = get_cube(app)
    try:
        yield dc
    finally:
        if dc:
            release_cube(dc, app)
