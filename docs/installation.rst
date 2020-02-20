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

datacube-ows is not currently being released to PyPI.

From sources ( Natively )
--------------------------

The sources for datacube-ows can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/opendatacube/datacube-ows

Or download the `zip`_:

.. code-block:: console

    $ curl  -OL https://github.com/opendatacube/datacube-ows/archive/master.zip

Once you have a copy of the source, you need to create a local version
of the config file, and edit it to reflect your requirements.

.. code-block:: console

    $ cp datacube_wms/wms_cfg_example.py datacube_wms/wms_cfg_local.py

To install datacube-ows, run:

.. code-block:: console

    $ python3 setup.py install


.. _datacube-core: https://datacube-core.readthedocs.io/en/latest/
.. _Github repo: https://github.com/opendatacube/datacube-ows
.. _zip: https://github.com/opendatacube/datacube-ows/archive/master.zip



From sources ( within Docker )
------------------------------

The sources for datacube-ows can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/opendatacube/datacube-ows

Or download the `zip`_:

.. code-block:: console

    $ curl  -OL https://github.com/opendatacube/datacube-ows/archive/master.zip

Once you have a copy of the source, you need to create a local version
of the config file, and edit it to reflect your requirements.

.. code-block:: console

    $ cp datacube_wms/wms_cfg_example.py datacube_wms/wms_cfg_local.py

Create an external PostgreSQL Database for OWS use. Use this as a
sidecar docker or natively on the host system. The following
steps assume the database is on the host system for networking
purposes. Take note of the credentials of the database for
use as parameters to run OWS.

Build a docker image in the local registry:

.. code-block:: console

    $ docker build -t ows-dev .

Run docker image to start gunicorn with ows. Here the DB
parameters noted previously are forwared to the docker image entrypoint.

.. code-block:: console

    $ docker run -e DB_DATABASE=datacube -e DB_HOSTNAME=localhost -e DB_USERNAME=ubuntu -e DB_PASSWORD=ubuntu --network=host ows-dev

Connect to the running docker to initialise DB:

.. code-block:: console

    $ docker exec -it beautiful_docker bash
    $ datacube system init
    $ python3 update_ranges.py --schema --role ubuntu

Exit the docker environment and use curl to validate the
GetCapabilities form OWS works:

.. code-block:: console

    $ curl "localhost:8000/?service=wms&request=getcapabilities"
