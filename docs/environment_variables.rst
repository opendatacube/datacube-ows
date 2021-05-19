Environment  Variables and Datacube_OWS
=======================================

The behaviour of datacube_ows can be modified by a number of environment
variables.

.. contents:: Table of Contents

Datacube_ows configuration
--------------------------

The location of the `datacube configuration object <configuration.rst>`_
is set via the ``$DATACUBE_OWS_CFG`` environment variable as described
`here <configuration.rst>`_. To enable the retrieval of a json configuration file from AWS S3,
the ``$DATACUBE_OWS_CFG_ALLOW_S3`` environment variable needs to be set to ``YES``.

Open DataCube Database Connection
---------------------------------

The preferred method of configuring the ODC database is with the ``$DB_*``
environment variables:

DB_HOSTNAME:
    The hostname or IP address of the database server. Defaults to ``localhost``.

DB_PORT:
    The port number of the database server. Defaults to ``5432``.

DB_DATABASE:
    The database name.

DB_USERNAME:
    The database user to connect as.

DB_PASSWORD:
    The database password.

Other valid methods for configuring an OpenDatacube instance (e.g. a ``.datacube.conf`` file)
should also work.

Configuring AWS Access
----------------------

Environment variables for AWS access are mostly read through the boto3 library - please
refer to their documentation for details.

Of particular note are:

AWS_DEFAULT_REGION:
    S3 access by datacube_ows will be disabled unless this is set.

AWS_NO_SIGN_REQUEST:
    S3 access will be unsigned if this environment variable is set
    to a non-empty value other than "n", "f", "no", "false" or "0".

    N.B. Unsigned requests is the default behaviour - explicitly
    set ``$AWS_NO_SIGN_REQUEST`` to an empty string to sign requests
    (and set the ``$AWS_ACCESS_KEY_ID`` and
    ``$AWS_SECRET_ACCESS_KEY`` environment variables - refer to
    the boto3 documentation for more information).

AWS_REQUEST_PAYER:
    Set to "requester" if accessing requester-pays S3 buckets.
    Default behaviour is to prevent access to requester-pays buckets.

Configuring Flask
-----------------

Datacube_ows uses the
`Flask web application framework <https://palletsprojects.com/p/flask>`_
which can read from several environment variables, most notably:

FLASK_APP:
      Should point to the ``datacube_ows/ogc.py`` file in your deployment.

The ``$FLASK_ENV`` environment variable also has a significant
effect on the way datacube_ows runs. Refer to the Flask documentation
for further details.

Dev-ops Tools
-------------

The following deployment tools are configured via environment variables:

SENTRY_KEY and SENTRY_PROJECT:
    The `Sentry application monitoring and error tracking system <https:/sentry.io>`_
    system is activated and configured with the ``$SENTRY_KEY`` and ``$SENTRY_PROJECT``
    environment variables.

prometheus_multiproc_dir:
    The `Prometheus event monitoring system <https://prometheus.io>`_ is activated by
    setting this lower case environment variable.

Dev Tools
---------

PYDEV_DEBUG:
    If set, activates PyDev remote debugging.

DEFER_CFG_PARSE:
    If set, the configuration file is not read and parsed at startup.  This
    is mostly useful for creating test fixtures.

Docker and Docker-compose
-------------------------

The provided ``Dockerfile`` and ``docker-compose.yaml`` read additional
environment variables at build time.  Please refer to the `README <https://datacube-ows.readthedocs.io/en/latest/readme.html>`_
for further details.
