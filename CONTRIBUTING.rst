.. highlight:: shell

============
Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given.

We have a `code of conduct<code-of-conduct.md>`_, so please follow it in all your interactions with the project.

You can contribute in many ways:

Types of Contributions
----------------------

Report Bugs
~~~~~~~~~~~

Report bugs at https://github.com/opendatacube/datacube-ows/issues.

If you are reporting a bug, please include:

* Your operating system name and version.
* Any details about your local setup that might be helpful in troubleshooting.
* Detailed steps to reproduce the bug.

Fix Bugs
~~~~~~~~

Look through the GitHub issues for bugs. Anything tagged with "bug"
and "help wanted" is open to whoever wants to implement it.

Implement Features
~~~~~~~~~~~~~~~~~~

Look through the GitHub issues for features. Anything tagged with "enhancement"
and "help wanted" is open to whoever wants to implement it.

Write Documentation
~~~~~~~~~~~~~~~~~~~

datacube-ows could always use more documentation, whether as part of the
official datacube-ows docs, in docstrings, or even on the web in blog posts,
articles, and such.

Submit Feedback
~~~~~~~~~~~~~~~

The best way to send feedback is to file an issue at https://github.com/opendatacube/datacube-ows/issues .

If you are proposing a feature:

* Explain in detail how it would work.
* Keep the scope as narrow as possible, to make it easier to implement.
* Remember that this is a volunteer-driven project, and that contributions
  are welcome :)

Get Started!
------------

1. Fork the `datacube-ows` repo on GitHub.
2. Clone your fork locally::

    $ git clone git@github.com:your_name_here/datacube-ows.git

3. Follow the instructions in `README.rst<https://datacube-ows.readthedocs.io/en/latest/readme.html>`_  to build a working python environment.

4. Create a branch for local development::

    $ git checkout -b name-of-your-bugfix-or-feature

   Now you can make your changes locally.

5. When you're done making changes, check that your changes pass flake8 and the tests, including testing other Python versions with tox::

    $ flake8 datacube-ows tests
    $ python setup.py test or py.test
    $ tox

   To get flake8 and tox, just pip install them into your virtualenv.

6. Commit your changes and push your branch to GitHub::

    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature

7. Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Before you submit a pull request, check that it meets these guidelines:

1. The pull request should include tests (and should pass them - and all pre-existing tests!)
2. If the pull request adds or modifies functionality, the docs should be updated.
3. The pull request should work for Python 3.7+. Check the results of
   the github actions and make sure that your PR passes all checks and
   does not decrease test coverage.


Integration test data and cfg update
------------------------------------

setting a NEW db dump
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

    # bring up indexing and db container
    docker-compose -f docker-compose.index.yaml -f docker-compose.cleandb.yaml up


building on top of existing db dump
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

  docker-compose -f docker-compose.yaml -f docker-compose.index.yaml -f docker-compose.db.yaml up

checkpoint
~~~~~~~~~~
by this point, there should be `3` docker container running:
- 1 for database
- 1 for indexing
- 1 for ows

to check the containers that are running use `docker ps`

indexing and create db dump
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: console

  # start by going to index container
  docker exec -ti datacube-ows-index-1 bash
  datacube system init # OPTIONAL: no need to run this command if building off existing db
  datacube product add https://raw.githubusercontent.com/digitalearthafrica/config/master/products/esa_s2_l2a.odc-product.yaml
  stac-to-dc --bbox='123.92427299922684,-14.559406653491095,124.94716787178676,-13.560932176423318' --collections='sentinel-s2-l2a-cogs' --datetime='2021-12-20/2022-01-10'
  ... # anything extra to index
  exit # after indexing is complete, exit

  # now go to ows container
  docker exec -it datacube-ows_ows_1 bash
  datacube-ows-update --schema --role <db_read_role>
  datacube-ows-update --views
  datacube-ows-update
  exit

  # return to index container
  docker exec -it index_index_1 bash # if using chained docker-compose the container name is datacube-ows_index_1
  pg_dump -U localhost -p 5432 -h localhost odc > dump.sql
  # enter password on prompt: mysecretpassword or check .env file
  exit


  # copy the new dump to datacube-ows/docker/database folder
  docker cp datacube-ows_ows_1:/dump.sql datacube-ows/docker/database

If the integration test is based on a new product and require new config translation, continue the following.

.. code-block:: console

  # enter ows container
  docker exec -it datacube-ows_ows_1 bash
  datacube-ows-cfg extract -m /tmp/messages.po
  datacube-ows-cfg translation -n -D ows_cfg -d /tmp/translations -m /tmp/messages.po en de


manually modify translation for `de` for `assert` test to pass, then create `ows_cfg.mo`

.. code-block:: console

  datacube-ows-cfg compile -D ows_cfg -d /tmp/translations en de
  exit
  # from outside of the container, cp all the translation files to local.
  docker cp datacube-ows_ows_1:/tmp/translations datacube-ows/integrations/cfg/


Generating database relationship diagram
----------------------------------------

.. code-block:: console

    docker run -it --rm -v "$PWD:/output" --network="host" schemaspy/schemaspy:snapshot -u $DB_USERNAME -host localhost -port $DB_PORT -db $DB_DATABASE -t pgsql11 -schemas wms -norows -noviews -pfp -imageformat svg

Merge relationship diagram and orphan diagram

.. code-block:: console

    python3 svg_stack.py --direction=h --margin=100 ../wms/diagrams/summary/relationships.real.large.svg ../wms/diagrams/orphans/orphans.svg > ows.merged.large.svg

    cp svg_stack/ows.merged.large.svg ../datacube-ows/docs/diagrams/db-relationship-diagram.svg


Links
-----

In case you haven't found them yet, please checkout the following resources:

* `Documentation <https://datacube-ows.readthedocs.io/en/latest>`_
* `Slack <http://slack.opendatacube.org>`_
