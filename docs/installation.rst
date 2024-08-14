.. highlight:: shell

============
Installation
============

Datacube core
-------------

datacube-ows depends on `datacube-core`_.  Ensure you have a
working version of the OpenDatacube (including ingested data products)
before attempting to install and configure datacube-ows.

Stable release
--------------

datacube-ows is released to PyPI and the latest release can be found on https://pypi.org/project/datacube-ows/.

Install PostGIS
----------------
In addition to the database installed for `Datacube Core`, `datacube-ows` also requires PostGIS_ installed.

.. code-block:: console

    $ sudo apt-get install postgis

Download datacube-ows source
----------------------------
The sources for datacube-ows can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/opendatacube/datacube-ows

Or download the `zip`_:

.. code-block:: console

    $ curl  -OL https://github.com/opendatacube/datacube-ows/archive/master.zip

From sources ( Natively )
--------------------------
Once you have a copy of the source, you need to create a local version
of the config file, and edit it to reflect your requirements.

.. code-block:: console

    $ cp datacube_ows/ows_test_cfg.py datacube_ows/ows_local_cfg.py
    $ DATACUBE_OWS_CFG=ows_local_cfg.ows_cfg

* We currently recommend using pip with pre-built binary packages. Create a
  new python 3.10+ virtualenv and run pip install against the supplied
  requirements.txt::

    pip install -e .[all]

To install datacube-ows, run:

.. code-block:: console

    $ python3 setup.py install


.. _datacube-core: https://datacube-core.readthedocs.io/en/latest/
.. _Github repo: https://github.com/opendatacube/datacube-ows
.. _zip: https://github.com/opendatacube/datacube-ows/archive/master.zip
.. _PostGIS: https://postgis.net/

Update_range natively
---------------------

Refer to the :doc:`database documentation <database>` documentation
for information on how to setup and maintain a Datacube OWS database.

From sources ( within Docker )
------------------------------

Build a docker image in the local registry:

.. code-block:: console

    $ docker build -t ows-dev .

Run docker image to start gunicorn with ows. Here the DB
parameters noted previously are forwarded to the docker image entrypoint.
Note: the default ``PYTHONPATH`` is pointed to ``/env``, place ``ows_cfg.py`` here.

.. code-block:: console

    $ docker run -e DB_DATABASE=datacube -e DB_HOSTNAME=localhost -e DB_USERNAME=ubuntu -e DB_PASSWORD=ubuntu -e DATACUBE_OWS_CFG=config.ows_cfg.ows_cfg --network=host --mount type=bind,source=/pathtocfg/ows_local_cfg.py,target=/env/config/ows_cfg.py ows-dev


From sources ( with Docker Compose and local db)
------------------------------------------------

Once you have a copy of the source, you need to create a local version
of the config file, and edit it to reflect your requirements.

.. code-block:: console

    $ vi .env

Create an external PostgreSQL Database for OWS use. (See
the :doc:`database documentation <database>` for
more information.)  jUse this as a
sidecar docker or natively on the host system. The following
steps assume the database is on the host system for networking
purposes. Take note of the credentials of the database for
use as parameters to run OWS.

Run docker compose to start gunicorn with ows. Here the DB
parameters noted previously are forwarded to the docker image entrypoint.

.. code-block:: console

    $ docker-compose up

Update_range via docker
-----------------------

Connect to the running docker to run datacube-ows-update/update_range.py
commands (see the :doc:`database documentation <database>` for more
information).

E.g. to set up a new database:

.. code-block:: console

    $ docker exec -it datacube-ows_ows_1 bash
    ows_1$ datacube system init
    ows_1$ datacube-ows-update --schema --write-role ubuntu
    ows_1$ datacube-ows-update


Validate setup
--------------

Exit the docker environment and use curl to validate the
GetCapabilities form OWS works:

.. code-block:: console

    $ curl "localhost:8000/?service=wms&request=getcapabilities"
