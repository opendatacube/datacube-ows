=====
Usage
=====

As a Python Module
------------------

To use datacube-ows in a project::

    import datacube_wms

As a Web-Service in Docker with Layers deployed
-----------------------------------------------

Access a sample product definition. This playbook uses ALOS-PALSAR
product definitions in the Digital Earth Africa deployment.

.. code-block:: console

    $ wget https://raw.githubusercontent.com/digitalearthafrica/config/master/products/alos_palsar_mosaic.yaml

Inject the sample product into datacube using datacube commands.
These should be available in the OWS docker image.

.. code-block:: console

    $ datacube product add https://raw.githubusercontent.com/digitalearthafrica/config/master/products/alos_palsar_mosaic.yaml

Index all the ``YAML`` files for a particular year of ALOS-PALSAR
using a classic Unix toolchain style,
with `AWS CLI <https://aws.amazon.com/cli/>`_ grabbing them from S3.

.. code-block:: console

    $ aws s3 ls s3://deafrica-data/jaxa/alos_palsar_mosaic/2017/ --recursive \
    | grep yaml | awk '{print $4}' \
    | xargs -n1 -I {} datacube dataset add s3://deafrica-data/{}

Index a dataset when ``yaml`` file is not available and ONLY ``.json`` file is available.

.. code-block:: console

    # How to index Sentinel-2 cogs

    ## Tooling
    pip install --upgrade --extra-index-url="https://packages.dea.ga.gov.au" odc-apps-dc-tools odc-index datacube

    ## Find the files

    s3-find s3://sentinel-cogs/sentinel-s2-l2a-cogs/2019/**/*.json > sentinel-cogs-2020.txt

    ## Tar them up

    s3-to-tar sentinel-cogs-2020.txt sentinel-cogs-2020.tar

    ## Install the fresh indexing tools (if not already installed)

    `pip install --upgrade --extra-index-url="https://packages.dea.ga.gov.au" odc-apps-dc-tools odc-index`

    ## And index

    dc-index-from-tar --stac --product=s2_l2a < sentinel-cogs-2020.tar

.. note:: The next step will be superseded soon by an OWS sub-command.

Update extents of products in Datacube to make it easier for OWS to create getcapabilities documents where the `ows_cfg.py` file is within the code directory.

.. code-block:: console

    $ python3 update_ranges.py alos_palsar_mosaic

Update extents of products in Datacube to make it easier for OWS to create getcapabilities documents where the `ows_cfg.py` file is outside of the code directory, i.e. `/opt`.

.. code-block:: console

    $ PYTHONPATH=/opt python3 update_ranges.py --product alos_palsar_mosaic --no-calculate-extent


Deploy the Digital Earth Africa OWS config available `here <https://github.com/digitalearthafrica/config/blob/master/services/ows.py>`_
by copying to wms_cfg.py. Ideally load the config outside
a docker container to iterate faster.

Run GetCapabilities via curl to ensure data is present.
Perform GetMap via Qgis to ensure data is visible.

.. code-block:: console

    $ curl "localhost:8000/?service=wms&request=getcapabilities"
