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


class ODCInitException(Exception):
    def __init__(self, e: Exception):
        super().__init__(str(e))
        self.cause = e

    def __str__(self):
        return "ODC initialisation failed:" + str(self.cause)


# CubePool class
class CubePool:
    """
    A Cube pool is a thread-safe resource pool for managing Datacube objects (which map to database connections).
    """
    # _instances, global mapping of CubePools by app name
    _instances: MutableMapping[str, "CubePool"] = {}

    _cubes_lock_: bool = False

    _instance: Optional[Datacube] = None

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
        if not self._cubes_lock_:
            self._cubes_lock: Lock = Lock()
            self._cubes_lock_ = True

    def get_cube(self) -> Optional[Datacube]:
        """
        Return a Datacube object.  Either generating a new Datacube, or recycling an unassigned one already in the pool.

        :return:  a Datacube object (or None on error).
        """
        self._cubes_lock.acquire()
        try:
            if self._instance is None:
                self._instance = self._new_cube()
        # pylint: disable=broad-except
        except Exception as e:
            _LOG.error("ODC initialisation failed: %s", str(e))
            raise(ODCInitException(e))
        finally:
            self._cubes_lock.release()
        return self._instance

    def _new_cube(self) -> Datacube:
        return Datacube(app=self.app)


# Lowlevel CubePool API
def get_cube(app: str = "ows") -> Optional[Datacube]:
    """
    Obtain a Datacube object from the appropriate pool

    :param app: The app pool to use - defaults to "ows".
    :return: a Datacube object (or None) in case of database error.
    :raises: ODCInitException
    """
    return CubePool(app=app).get_cube()


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
    :raises: ODCInitException
    """
    yield get_cube(app)
