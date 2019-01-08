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

From sources
------------

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


.. _datacube-core: https://datacube-core.readthedocs.io/en/latest/
.. _Github repo: https://github.com/opendatacube/datacube-ows
.. _zip: https://github.com/opendatacube/datacube-ows/archive/master.zip