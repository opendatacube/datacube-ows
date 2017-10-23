from datacube import Datacube
from threading import Lock

class CubePool(object):
    _instances = {}
    _cubes = None
    _cubes_lock = None
    def __new__(cls, app):
        if app not in cls._instances:
            cls._instances[app] = super(CubePool, cls).__new__(cls)
        return cls._instances[app]
    def __init__(self, app):
        self.app=app
        if not self._cubes:
            self._cubes = {}
        if not self._cubes_lock:
            self._cubes_lock = Lock()
    def get_cube(self):
        self._cubes_lock.acquire()
        for cube, assigned in self._cubes.items():
            if not assigned:
                self._cubes[cube] = True
                self._cubes_lock.release()
                return cube
        self._cubes_lock.release()
        cube = self._new_cube()
        self._cubes[cube] = True
        return cube
    def release_cube(self, cube):
        if cube not in self._cubes:
            raise Exception("Cannot release non-pool datacube.")
        self._cubes_lock.acquire()
        self._cubes[cube] = False
        self._cubes_lock.release()
    def _new_cube(self):
        return Datacube(app=self.app)

_pool = None

def _init_pool(app="wms"):
    _pool = CubePool(app=app)

def get_cube(app="wms"):
    pool = CubePool(app=app)
    return pool.get_cube()

def release_cube(cube, app="wms"):
    pool = CubePool(app=app)
    return pool.release_cube(cube)


