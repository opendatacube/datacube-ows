import sys
import os

# This is the directory of the source code that the web app will run from
sys.path.append("/home/phaesler/src/datacube/wms")

# The location of the datcube config file.
os.environ.setdefault("DATACUBE_CONFIG_PATH", "/home/phaesler/.datacube.conf.local")

from datacube_wms.ogc import app
application = app
