============
datacube-ows
============

.. image:: https://github.com/opendatacube/datacube-ows/workflows/Linting/badge.svg
        :target: https://github.com/opendatacube/datacube-ows/actions?query=workflow%3ALinting

.. image:: https://github.com/opendatacube/datacube-ows/workflows/Tests/badge.svg
        :target: https://github.com/opendatacube/datacube-ows/actions?query=workflow%3ATests

.. image:: https://github.com/opendatacube/datacube-ows/workflows/Docker/badge.svg
        :target: https://github.com/opendatacube/datacube-ows/actions?query=workflow%3ADocker

.. image:: https://github.com/opendatacube/datacube-ows/workflows/Scan/badge.svg
        :target: https://github.com/opendatacube/datacube-ows/actions?query=workflow%3A%22Scan%22

.. image:: https://codecov.io/gh/opendatacube/datacube-ows/branch/master/graph/badge.svg
        :target: https://codecov.io/gh/opendatacube/datacube-ows

Datacube Open Web Services


* Free software: Apache Software License 2.0
* Documentation: https://datacube-ows.readthedocs.io.


Features
--------

* Leverages the power of the Open Data Cube, including support for COGs on S3.
* Supports WMS and WMTS.
* Experimental support for WCS (1.0, 2.0, 2.1).

Note on Naming
--------------

This project originally supported WMS only and was known as "datacube_wms".

There are still a handful of file and object names in the codebase that
include the substring "wms" although they are actually more general.
These names will be updated to "ows" as time permits.

Setup
-----

Datacube_ows (and datacube_core itself) has many complex dependencies on particular versions of
geospatial libraries.  Dependency conflicts are almost unavoidable in environments that also contain
other large complex geospatial software packages.  We therefore strongly recommend some kind of
containerised solution and we supply scripts for building appropriate Docker containers.


Docker-Compose
--------------

setup env by export
^^^^^^^^^^^^^^^^^^^
We use docker-compose to make development and testing of the containerised ows images easier

To start OWS with flask connected to a pre-existing database on your local machine: ::

  export DB_USERNAME=username
  export DB_PASSWORD=password
  export DB_DATABASE=opendatacube
  export DB_HOSTNAME=localhost
  export DB_PORT=5432
  OWS_CFG_FILE=/path/to/ows_cfg.py
  docker-compose up

To start ows with a pre-indexed database: ::

  docker-compose -f docker-compose.yaml -f docker-compose.db.yaml up

To start ows with db and gunicorn instead of flask (production) ::

  docker-compose -f docker-compose.yaml -f docker-compose.db.yaml -f docker-compose.prod.yaml up

The default environment variables (in .env file) can be overriden by setting local environment variables ::

  # Enable pydev for pycharm (needs rebuild to install python libs)
  # hot reload is not supported, so we need to set FLASK_DEV to production
  export PYDEV_DEBUG=yes
  export FLASK_DEV=production
  docker-compose -f docker-compose.yaml -f docker-compose.db.yaml up --build

  # Change location of default config file (good for testing config changes on a local db)
  OWS_CFG_FILE=/path/to/ows_cfg.py
  docker-compose -f docker-compose.yaml

setup env with .env file
^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

    cp .env_simple .env # for a single ows config file setup
    cp .env_ows_root .env # for multi-file ows config with ows_root_cfg.py
    docker-compose up


Docker
------
To run the standard Docker image, create a docker volume containing your ows config files and use something like: ::

  docker build --tag=name_of_built_container .

  docker run \
      --rm \
      opendatacube/ows \
      gunicorn -b '0.0.0.0:8000' -w 5 --timeout 300 datacube_ows:ogc

  docker run --rm \
        -e DATACUBE_OWS_CFG=datacube_ows.config.test_cfg.ows_cfg   # Location of config object
        -e AWS_NO_SIGN_REQUEST=yes                                 # Allowing access to AWS S3 buckets
        -e AWS_DEFAULT_REGION=ap-southeast-2 \                     # AWS Default Region (supply even if NOT accessing files on S3! See Issue #151)
        -e SENTRY_KEY=set5gstgw45gdfgw54t \                        # Key for Sentry logging (optional)
        -e SENTRY_PROJECT=my_datacube_ows_project \                # Project name for Sentry logging (optional)
        -e DB_HOSTNAME=172.17.0.1 -e DB_PORT=5432 \                # Hostname/IP address and port of ODC postgres database
        -e DB_DATABASE=datacube \                                  # Name of ODC postgres database
        -e DB_USERNAME=cube -e DB_PASSWORD=DataCube \              # Username and password for ODC postgres database
        -e PYTHONPATH=/code                                        # The default PATH is under env, change this to target /code
        -p 8080:8000 \                                             # Publish the gunicorn port (8000) on the Docker
        \                                                          # container at port 8008 on the host machine.
        --mount source=test_cfg,target=/code/datacube_ows/config \ # Mount the docker volume where the config lives
        name_of_built_container

The image is based on the standard ODC container.

Manual installation
-------------------

At the time of writing, pre-built pip-installed configurations also work fairly seemlessly:

The folllowing instructions are for installing on a clean Linux system with established ODC environment.

* Create a
  new python 3.6 or 3.8 virtualenv and run pip install against the supplied
  requirements.txt (The --pre flag solves some problems in 3.6 but causes
  problems in 3.8.)::

    pip install [--pre] -r requirements.txt

* Run ::
    python update_ranges.py --role *datacube_owner_role* --schema

  to create schema, tables and materialised views used by datacube-ows.

* Create a configuration file for your service, and all data products you wish to publish in
  it.  See `datacube_ows/ows_cfg_example.py` for examples and documentation of the configuration
  format.  The simplest approach is to make a copy of `ows_cfg_example.py` called `ows_cfg.py`
  and edit as required.  But for production deployments other approaches such as importing
  config as json are possible::

    PYTHONPATH=.
    DATACUBE_OWS_CFG=ows_cfg_filename.ows_cfg
    AWS_NO_SIGN_REQUEST=yes
    AWS_DEFAULT_REGION=ap-southeast-2

* Run ``python update_ranges.py`` (in the Datacube virtual environment).

* When additional datasets are added to the datacube, the following steps will need to be run::

    python update_ranges.py --views --blocking
    python update_ranges.py

* If you are accessing data on AWS S3 and running `datacube_ows` on Ubuntu you may encounter errors with ``GetMap``
  similar to:
  ``Unexpected server error: '/vsis3/bucket/path/image.tif' not recognized as a supported file format.``.
  If this occurs run the following commands::

    mkdir -p /etc/pki/tls/certs
    ln -s /etc/ssl/certs/ca-certificates.crt /etc/pki/tls/certs/ca-bundle.crt

* Launch flask app using your favorite WSGI server.  We recommend using Gunicorn with
  either nginx or a load balancer.

The following approaches have also been tested:

Flask Dev Server
----------------

* Good for initial dev work and testing.  Not (remotely) suitable for production
  deployments.

* `cd` to the directory containing this README file.

* Set the `FLASK_APP` environment variable::

        export FLASK_APP=datacube_ows/ogc.py

* Run the Flask dev server::

        flask run

* If you want the dev server to listen to external requests (i.e. requests
  from other computers), use the `--host` option::

        flask run --host=0.0.0.0

Local Postgres database
-----------------------
1. create an empty database and db_user
2. run `datacube system init` after creating a datacube config file
3. A product added to your datacube `datacube product add url` some examples are here: https://github.com/GeoscienceAustralia/dea-config/tree/master/products
4. Index datasets into your product for example refer to https://datacube-ows.readthedocs.io/en/latest/usage.html

    ::

      aws s3 ls s3://deafrica-data/jaxa/alos_palsar_mosaic/2017/ --recursive \
      | grep yaml | awk '{print $4}' \
      | xargs -n1 -I {} datacube dataset add s3://deafrica-data/{}

5. Write an ows config file to identify the products you want available in ows, see example here: https://github.com/opendatacube/datacube-ows/blob/master/datacube_ows/ows_cfg_example.py
6. Run `python3 https://github.com/opendatacube/datacube-ows/blob/master/update_ranges.py --schema` to create ows specific tables
7. Run update_ranges.py to generate ows extents `python3 update_ranges.py PRODUCT`

Apache2 mod_wsgi
----------------

Getting things working with Apache2 mod_wsgi is not trivial and probably not the best
approach in most circumstances, but it may make sense for you.

If you use the ``pip install --pre`` approach described above, your OS's
pre-packaged python3 apache2-mod-wsgi package should suffice.

* Activate the wsgi module:

::

  cd /etc/apache2/mods-enabled
  ln -s ../mods-available/wsgi.load .
  ln -s ../mods-available/wsgi.conf .

* Add the following to your Apache config (inside the
  appropriate `VirtualHost` section):

  ::

        WSGIDaemonProcess datacube_ows processes=20 threads=1 user=uuu group=ggg maximum-requests=10000
        WSGIScriptAlias /datacube_ows /path/to/source_code/datacube-ows/datacube_ows/wsgi.py
        <Location /datacube_ows>
                WSGIProcessGroup datacube_ows
        </Location>
        <Directory /path/to/source_code/datacube-ows/datacube_ows>
                <Files wsgi.py>
                        AllowOverride None
                        Require all granted
                </Files>
        </Directory>

  Note that `uuu` and `ggg` above are the user and group of the owner of the Conda virtual environment.

* Copy `datacube_ows/wsgi.py` to `datacube_odc/local_wsgi.py` and edit to suit your system.

* Update the url in the configuration

Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

