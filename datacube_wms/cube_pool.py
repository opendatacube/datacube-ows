from __future__ import absolute_import, division, print_function
from contextlib import contextmanager
from datacube import Datacube
from threading import Lock

class CubePool():
    _instances = {}
    _cubes = None
    _cubes_lock = None

    def __new__(cls, app):
        if app not in cls._instances:
            cls._instances[app] = super(CubePool, cls).__new__(cls)
        return cls._instances[app]

    def __init__(self, app):
        self.app = app
        if not self._cubes:
            self._cubes = {}
        if not self._cubes_lock:
            self._cubes_lock = Lock()

    def get_cube(self):
        self._cubes_lock.acquire()
        for c, assigned in self._cubes.items():
            if not assigned:
                self._cubes[c] = True
                self._cubes_lock.release()
                return c
        c = self._new_cube()
        self._cubes[c] = True
        self._cubes_lock.release()
        return c

    def release_cube(self, c):
        if c not in self._cubes:
            raise Exception("Cannot release non-pool datacube.")
        self._cubes_lock.acquire()
        self._cubes[c] = False
        self._cubes_lock.release()

    def _new_cube(self):
        return Datacube(app=self.app)

    def __len__(self):
        return len(self._cubes)


def get_cube(app="wms"):
    pool = CubePool(app=app)
    return pool.get_cube()


def release_cube(c, app="wms"):
    pool = CubePool(app=app)
    return pool.release_cube(c)


def pool_size(app="wms"):
    pool = CubePool(app=app)
    return len(pool)


@contextmanager
def cube(app="wms"):
    dc = get_cube(app)
    try:
        yield dc
    finally:
        release_cube(dc, app)
