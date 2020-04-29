===============================
datacube-ows
===============================

.. image:: https://img.shields.io/travis/opendatacube/datacube-ows.svg
        :target: https://travis-ci.org/opendatacube/datacube-ows

Datacube Web Map Service


* Free software: Apache Software License 2.0
* Documentation: https://datacube-ows.readthedocs.io.


Features
--------

* Leverages the power of the Open Data Cube, including support for COGs on S3.
* Supports WMS and WMTS.
* Experimental support for WCS.

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

We use docker-compose to make development and testing of the containerised ows images easier


To start OWS with flask connected to a pre-existing database on your local machine: ::

  export DB_USERNAME=username
  export DB_PASSWORD=password
  export DB_DATABASE=opendatacube
  export DB_hostname=localhost
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

Docker
------
To run the standard Docker image, create a docker volume containing your ows config files and use something like: ::

  docker build --tag=name_of_built_container .

  docker run \
      --rm \
      opendatacube/wms \
      gunicorn -b '0.0.0.0:8000' -w 5 --timeout 300 datacube_ows:ogc

  docker run --rm \
        -e DATACUBE_OWS_CFG=datacube_ows.config.test_cfg.ows_cfg   # Location of config object
        -e AWS_ACCESS_KEY_ID=THISISNOTAREALAWSKEY \                # AWS ACCESS KEY (if accessing files on S3)
        -e AWS_SECRET_ACCESS_KEY=THISisNOTaREALawsSECRETaccessKEY \# AWS SECRET ACCESS KEY (if accessing files on S3)
        -e AWS_DEFAULT_REGION=ap-southeast-2 \                     # AWS Default Region (supply even if NOT accessing files on S3! See Issue #151)
        -e SENTRY_KEY=set5gstgw45gdfgw54t \                        # Key for Sentry logging (optional)
        -e SENTRY_PROJECT=my_datacube_ows_project \                # Project name for Sentry logging (optional)
        -e DB_HOSTNAME=172.17.0.1 -e DB_PORT=5432 \                # Hostname/IP address and port of ODC postgres database
        -e DB_DATABASE=datacube \                                  # Name of ODC postgres database
        -e DB_USERNAME=cube -e DB_PASSWORD=DataCube \              # Username and password for ODC postgres database
        -p 8080:8000 \                                             # Publish the gunicorn port (8000) on the Docker
        \                                                          # container at port 8008 on the host machine.
        --mount source=test_cfg,target=/code/datacube_ows/config \ # Mount the docker volume where the config lives
        name_of_built_container

The image is based on the standard ODC container.

Manual installation
-------------------

The folllowing instructions are for installing on a clean Linux system.

* Follow datacube installation instructions

* Make sure you are using the conda-forge channel.
    Run the following commands::

      conda config --prepend channels conda-forge
      conda update --all
	  
* Clone the repo public repository into your desired destination using `git clone git://github.com/opendatacube/datacube-ows` 

* Datacube OWS requires the scikit-image package:  `conda install scikit-image`

* Manually install dea-proto::

    pip install 'git+https://github.com/opendatacube/dea-proto.git#egg=dea-proto[async]'

* Datacube OWS has some dependencies that cannot be handled by conda.  After doing the conda
  installs, run pip install against the supplied requirements.txt::

    pip install -r requirements.txt

* Run `python update_ranges.py --role *datacube_user_role* --schema` to create schema and tables used
  by datacube-ows.

* Create a configuration file for your service, and all data products you wish to publish in
  it.  See `datacube_ows/ows_cfg_example.py` for examples and documentation of the configuration
  format.  The simplest approach is to make a copy of `ows_cfg_example.py` called `ows_cfg.py`
  and edit as required.  But for production deployments other approaches such as importing
  config as json are possible.

* Run `python update_ranges.py -- product *product_name* --no-calculate-extent` (in the Datacube Conda environment).  This
  script will need to be re-run every time additional datasets are added to
  the Datacube.

* If you are accessing data on AWS S3 and running `datacube_ows` on Ubuntu you may encounter errors with `GetMap`
  similar to:
  `Unexpected server error: '/vsis3/bucket/path/image.tif' not recognized as a supported file format.`.
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

        export FLASK_APP=datacube_wms/ogc.py

* Run the Flask dev server::

        flask run

* If you want the dev server to listen to external requests (i.e. requests
  from other computers), use the `--host` option::

        flask run --host=0.0.0.0

Local Postgres database
-----------------------
1. create an empty database and db_user 
2. run `datacube system init` after creating a datacube config file
3. A product added to your datacube `datacube product add url` some examples are here: https://github.com/GeoscienceAustralia/dea-config/tree/master/dev/products
4. Index datasets into your product for example refer to https://github.com/opendatacube/datacube-ows/blob/master/docs/usage.rst ::
  aws s3 ls s3://deafrica-data/jaxa/alos_palsar_mosaic/2017/ --recursive \
  | grep yaml | awk '{print $4}' \
  | xargs -n1 -I {} datacube dataset add s3://deafrica-data/{}
5. Write an ows config file to identify the products you want available in ows, see example here: https://github.com/opendatacube/datacube-ows/blob/master/datacube_ows/ows_cfg_example.py
6. Run `python3 https://github.com/opendatacube/datacube-ows/blob/master/update_ranges.py --schema` to create ows specific tables
7. Run update_ranges.py to generate ows extents `python3 update_ranges.py --product PRODUCT  --no-calculate-extent`

Apache2 mod_wsgi
----------------

Getting things working with Apache2 mod_wsgi is not trivial and probably not the best
approach in most circumstances, but if it makes sense for you, this how we have got
it working in the past:

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

