import sys
import os

# This is the directory of the source code that the web app will run from
sys.path.append("/home/phaesler/src/datacube/data3/wms_s3")

# The location of the datcube config file.
os.environ.setdefault("DATACUBE_CONFIG_PATH", "/home/phaesler/src/datacube/data3/datacube.conf")



os.environ.setdefault("AWS_ACCESS_KEY_ID", "AKIAI5777O3EGBZS6UXQ")

os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "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")

from datacube_wms.wms import app
application = app
