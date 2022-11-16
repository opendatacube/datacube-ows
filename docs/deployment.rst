Deploying
=========

Deploying with Helm Chart
--------------------------

Prerequisites
^^^^^^^^^^^^^

Make sure you have Helm `installed <https://helm.sh/docs/using_helm/#installing-helm>`_.

Get Repo Info
^^^^^^^^^^^^^^

.. code::

    helm repo add datacube-charts https://opendatacube.github.io/datacube-charts/charts/
    helm repo update


See `helm repo <https://helm.sh/docs/helm/helm_repo/>`_ for command documentation.


Deploy with default config
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code::

    helm upgrade --install datacube-ows datacube-charts/datacube-ows


Deploy in a custom namespace
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code::

    helm upgrade --install datacube-ows --namespace=web datacube-charts/datacube-ows

Chart values
^^^^^^^^^^^^

.. code::

    helm show values datacube-charts/datacube-ows
