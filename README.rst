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

* Run `create_tables.sql` database script to create schema and tables used
  by WMS server.

* Run `python update_ranges.py` (in the Datacube Conda environment).  This
  script will need to be re-run every time additional datasets are added to
  the Datacube.

* Edit `datacube_wms/wms_cfg.py` as required. If you are using git, you should
  create a branch first.

* Launch flask app.  Either use your preferred WSGI-enabled web server, or
  the Flask dev server.


Credits
---------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage

