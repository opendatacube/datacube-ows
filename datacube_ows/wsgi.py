# pylint: skip-file
import os
import sys

from datacube_ows.ogc import app

# This is the directory of the source code that the web app will run from
sys.path.append("/opt")

# The location of the datcube config file.
os.environ.setdefault("DATACUBE_CONFIG_PATH", "/opt/odc/.datacube.conf.local")

application = app


def main():
    app.run()


if __name__ == "__main__":
    main()
