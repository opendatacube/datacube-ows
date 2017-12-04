import sys

# This is the directory of the source code that the web app will run from
sys.path.append("/home/phaesler/src/datacube/wms")

# The location of the datcube config file.
import os

os.environ.setdefault("DATACUBE_CONFIG_PATH", "/home/phaesler/.datacube.conf")

import math

from datacube_wms.wms import app

application = app
