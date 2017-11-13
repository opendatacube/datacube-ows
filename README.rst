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

* Run `create_tables.sql` database script to create schema and tables used
  by WMS server.

* Run `python update_ranges.py` (in the Datacube Conda environment).  This
  script will need to be re-run every time additional datasets are added to
  the Datacube.

* Edit `datacube_wms/wms_cfg.py` as required.

* Launch flask app.  Either use your preferred WSGI-enabled web server, or
  the Flask dev server.

* In addition to the packages required for the Datacube and Flask, the
  Datacube WMS server requires the skimage package:  `conda install skimage`

Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

