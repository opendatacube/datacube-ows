#pylint: skip-file
import sys
import os

# This is the directory of the source code that the web app will run from
sys.path.append("/opt/config")

# The location of the datcube config file.
os.environ.setdefault("DATACUBE_CONFIG_PATH", "/opt/odc/.datacube.conf.local")

from datacube_ows.ogc import app
application = app
