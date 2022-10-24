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

.. image:: https://img.shields.io/pypi/v/datacube?label=datacube
   :alt: PyPI

Datacube Open Web Services
--------------------------

Datacube-OWS provides a way to serve data indexed in an Open Data Cube as visualisations, through
open web services (OGC WMS, WMTS and WCS).

* Free software: Apache Software License 2.0
* Documentation: https://datacube-ows.readthedocs.io.

Features
--------

* Leverages the power of the Open Data Cube, including support for COGs on S3.
* Fully supports WMS v1.3.0. Partial support (GetMap requests only) for v1.1.1.
* Supports WMTS 1.0.0
* Supports WCS versions 1.0.0, 2.0.0 and 2.1.0.
* Richly featured styling engine for serving data visualisations via WMS and WMTS.

Community
---------

This project welcomes community participation.

`Join the ODC Slack <http://slack.opendatacube.org>`__ if you need help
setting up or using this project, or the Open Data Cube more generally.
Conversation about datacube-ows is mostly concentrated in the Slack
channel ``#wms``.

Please help us to keep the Open Data Cube community open and inclusive by
reading and following our `Code of Conduct <code-of-conduct.md>`__.

Setup
-----

Datacube_ows (and datacube_core itself) has many complex dependencies on particular versions of
geospatial libraries.  Dependency conflicts are almost unavoidable in environments that also contain
other large complex geospatial software packages.  We therefore strongly recommend some kind of
containerised solution and we supply scripts for building appropriate Docker containers.

Linting
-------

.. code-block::

    flake8 . --exclude Dockerfile --ignore=E501 --select=F401,E201,E202,E203,E502,E241,E225,E306,E231,E226,E123,F811
    isort --check --diff **/*.py
    autopep8  -r  --diff . --select F401,E201,E202,E203,E502,E241,E225,E306,E231,E226,E123,F811


Configuration and Environment
-----------------------------

The configuration file format for OWS is `fully documented here <https://datacube-ows.readthedocs.io/en/latest/configuration.html>`_.

And example configuration file `datacube_ows/ows_cfg_example.py` is also provided, but
may not be as up-to-date as the formal documentation.

Environment variables that directly or indirectly affect the running of OWS
are `documented here<https://datacube-ows.readthedocs.io/en/latest/environment_variables.html>`_.

Docker-Compose
--------------

setup env by export
^^^^^^^^^^^^^^^^^^^

We use docker-compose to make development and testing of the containerised ows images easier.

Set up your environment by creating a `.env` file (see below).

To start OWS with flask connected to a pre-existing database on your local machine: ::

  docker-compose up

The first time you run docker-compose, you will need to add the `--build` option: ::

  docker-compose up --build

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

setup env with .env file
^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: console

    cp .env_simple .env # for a single ows config file setup
    cp .env_ows_root .env # for multi-file ows config with ows_root_cfg.py
    docker-compose up

Docker
------
To run the standard Docker image, create a docker volume containing your ows config files and use something like: ::

  docker build --tag=name_of_built_container .

  docker run --rm \
        -e DATACUBE_OWS_CFG=datacube_ows.config.test_cfg.ows_cfg   # Location of config object
        -e AWS_NO_SIGN_REQUEST=yes                                 # Allowing access to AWS S3 buckets
        -e AWS_DEFAULT_REGION=ap-southeast-2 \                     # AWS Default Region (supply even if NOT accessing files on S3! See Issue #151)
        -e SENTRY_DSN=https://key@sentry.local/projid \            # Key for Sentry logging (optional)
        -e DB_HOSTNAME=172.17.0.1 -e DB_PORT=5432 \                # Hostname/IP address and port of ODC postgres database
        -e DB_DATABASE=datacube \                                  # Name of ODC postgres database
        -e DB_USERNAME=cube -e DB_PASSWORD=DataCube \              # Username and password for ODC postgres database
        -e PYTHONPATH=/code                                        # The default PATH is under env, change this to target /code
        -p 8080:8000 \                                             # Publish the gunicorn port (8000) on the Docker
        \                                                          # container at port 8008 on the host machine.
        --mount source=test_cfg,target=/code/datacube_ows/config \ # Mount the docker volume where the config lives
        name_of_built_container

The image is based on the standard ODC container.

Installation with Conda
------------

The following instructions are for installing on a clean Linux system.

* Create a conda python 3.8 and activate conda environment::

    conda create -n ows -c conda-forge python=3.8 datacube pre_commit postgis
    conda activate ows

* install the latest release using pip install::

    pip install datacube-ows[all]

* setup a database::

    pgdata=$(pwd)/.dbdata
    initdb -D ${pgdata} --auth-host=md5 --encoding=UTF8 --username=ubuntu
    pg_ctl -D ${pgdata} -l "${pgdata}/pg.log" start # if this step fails, check log in ${pgdata}/pg.log

    createdb ows -U ubuntu

* enable postgis extension::

    psql -d ows
    create extension postgis;
    \q

* init datacube and ows schema::

    export DATACUBE_DB_URL=postgresql:///ows
    datacube system init

    # to create schema, tables and materialised views used by datacube-ows.

    export DATACUBE_OWS_CFG=datacube_ows.ows_cfg_example.ows_cfg
    datacube-ows-update --role ubuntu --schema


* Create a configuration file for your service, and all data products you wish to publish in
  it.
  `Detailed documentation of the configuration format can be found here.<https://datacube-ows.readthedocs.io/en/latest/configuration.html>`_

* Set environment variables as required.
  Environment variables that directly or indirectly affect the running of OWS
  are `documented here<https://datacube-ows.readthedocs.io/en/latest/environment_variables.html>`_.


* Run ``datacube-ows-update`` (in the Datacube virtual environment).

* When additional datasets are added to the datacube, the following steps will need to be run::

    datacube-ows-update --views
    datacube-ows-update

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
6. Run `datacube-ows-update --schema --role <db_read_role>` to create ows specific tables
7. Run `datacube-ows-update` to generate ows extents.

Apache2 mod_wsgi
----------------

Getting things working with Apache2 mod_wsgi is not trivial and probably not the best
approach in most circumstances, but it may make sense for you.

If you use the ``pip install`` approach described above, your OS's
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
