===============================
datacube-wms
===============================

.. image:: https://img.shields.io/travis/opendatacube/datacube-wms.svg
        :target: https://travis-ci.org/opendatacube/datacube-wms

Datacube Web Map Service


* Free software: Apache Software License 2.0
* Documentation: https://datacube-wms.readthedocs.io.


Features
--------

* TODO

Setup
-----

* Follow datacube installation instructions

* The Datacube WMS requires a more recent version of rasterio than is
  currently packaged with conda.  Run the following commands::

      conda config --prepend channels conda-forge/label/dev
      conda update --all

* Datacube WMS requires the scikit-image package:  `conda install scikit-image`

* Manually install dea-proto::

    pip install 'git+https://github.com/opendatacube/dea-proto.git#egg=dea-proto[async]'

* Run `create_tables.sql` database script to create schema and tables used
  by WMS server.

* Run `python update_ranges.py` (in the Datacube Conda environment).  This
  script will need to be re-run every time additional datasets are added to
  the Datacube.

* Edit `datacube_wms/wms_cfg.py` as required (See `datacube_wms/wms_cfg_example.py` for examples).
  If you are using git, you should either create a branch first, or use `datacube_wms/wms_cfg_local.py` instead.
  (If it exists, `wms_cfg_local.py` is read in preference to `wms_cfg.py`, but is explicitly ignored by git.)

* Launch flask app using your favorite WSGI server. The following approaches
  have been tested:

Flask Dev Server
----------------

* `cd` to the directory containing this README file.

* Set the `FLASK_APP` environment variable::

        export FLASK_APP=datacube_wms/ogc.py

* Run the Flask dev server::

        flask run

* If you want the dev server to listen to external requests (i.e. requests
  from other computers), use the `--host` option::

        flask run --host=0.0.0.0

Apache2 mod_wsgi
---------------

Getting mod_wsgi to work with a Conda virtual environment is not trivial. The
following steps worked for me, but will not support connecting your web server
to multiple web apps using different virtual environments.

* Uninstall any previously installed mod_wsgi packages

* (From the Datacube Conda environment) install mod_wsgi with pip.  Take note
  of the name of the resulting module which is given to you at the end of the
  install process, you will need it later::

        pip install mod_wsgi

* Find the full path of mod_wsgi-express with `which mod_wsgi-express`

* Install mod_wsgi into Apache::

        sudo /full/path/to/installed/mod_wsgi-express install-module

* Ensure the following lines appear somewhere in your Apache2 config (Note
  they must appear in the "root" of the config, they cannot appear inside
  a `VirtualHost` section)::

        LoadModule wsgi_module /full/path/to/wsgi/module.so
        WSGIPythonHome /path/to/your/conda/cubeenv

* Add the following to your Apache config (inside the
  appropriate `VirtualHost` section)::

        WSGIDaemonProcess datacube_wms processes=20 threads=1 user=uuu group=ggg maximum-requests=10000
        WSGIScriptAlias /datacube_wms /path/to/source_code/wms/datacube_wms/wsgi.py
        <Location /datacube_wms>
                WSGIProcessGroup datacube_wms
        </Location>
        <Directory /path/to/source_code/wms/datacube_wms>
                <Files wsgi.py>
                        AllowOverride None
                        Require all granted
                </Files>
        </Directory>

  Note that `uuu` and `ggg` above are the user and group of the owner of the Conda virtual environment.

* Edit `datacube_wms/wsgi.py` to suit your system.

* Update the url in service_cfg in `datacube_wms/wms_cfg.py`.

Docker
-------
To run this image, use something like: ::

  docker run \
      --rm \
      opendatacube/wms \
      gunicorn -b '0.0.0.0:8000' -w 5 --timeout 300 datacube_wms:wms


The image comes with the standard ODC installed, including the entrypoint that sets the config from the environment.

Additionally, the image includes another flag that can be used to grab a config file from a URL:

* `WMS_CONFIG_URL`


Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

