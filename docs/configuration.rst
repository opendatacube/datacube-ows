=================
OWS Configuration
=================

.. toctree::
   :maxdepth: 2
   :hidden:

   cfg_global
   cfg_wms
   cfg_wcs
   cfg_functions
   cfg_layers
   cfg_styling
   cfg_*_styles

.. contents:: Table of Contents

.. _introduction:

Introduction
------------

The behaviour of a datacube_ows server instance can be controlled, customised and extended by configuration files.

Datacube OWS configuration files can be written in Python (as a static serialisable python dictionary) or as JSON.
All examples in this documentation will always be presented in Python syntax.  JSON syntax is almost identical, but
note that there are some important differences:

1. JSON string literals must always be delimited with double quotes - so no Python-style single quote strings!
2. JSON boolean literals are all lowercase (`true`, `false`) and Python boolean literals are title case (e.g.
   `True`, `False`)
3. JSON does not allow commas after the last element of lists and objects (dictionaries in Python terms).
4. JSON does not support comments of any kind.

`This general introductory stuff is boring.  Take me straight to the description of the
configuration file. <#general-config-structure>`_

.. _location:

Where is Configuration Read From?
---------------------------------

Configuration is read by default from the ``ows_cfg object`` in ``datacube_ows/ows_cfg.py``
but this can be overridden by setting the ``$DATACUBE_OWS_CFG`` environment variable.

Configuration can be read from a python file, a json file, or a collection of python
and/or json files.

.. _DATACUBE_OWS_CFG:

The DATACUBE_OWS_CFG Environment Variable
=========================================

The environment variable ``$DATACUBE_OWS_CFG`` is interpreted as follows (first matching
alternative applies):

1. Has a leading slash, e.g. ``/opt/odc_ows_cfg/odc_ows_cfg_prod.json``

   Config loaded as **json** from absolute file path.

2. Contains a slash, e.g. ``configs/prod.json``

   Config loaded as **json** from relative file path.

3. Begins with an open brace "{", e.g. ``{...}``

   Config loaded directly from the environment variable as **json** (not recommended)

4. Ends in ".json", e.g. ``cfg_prod.json``

   Config loaded from **json** file in working directory.

5. Contains a dot (.), e.g. ``package.sub_package.module.cfg_object_name``

   Imported as python object (expected to be a dictionary).

   N.B. It is up to you to ensure that the Python file in question is in your Python path and
   that all package directories have a ``__init__.py`` file, etc.

6. Valid python object name, e.g. ``cfg_prod``

   Imported as **python** from named object in ``datacube_ows/ows_cfg.py``

7. Blank or not set

   Default to import ows_cfg object in ``datacube_ows/ows_cfg.py`` as described above.

.. _inclusion:

Inclusion: Breaking Up Config Into Multiple Files
-------------------------------------------------

The root configuration can include configuration content from other Python or JSON files,
allowing cleaner organisation of configuration and facilitating reuse of common configuration
elements across different layers within the one configuration and between different
configurations or deployment environments.

N.B. The examples here illustrate the inclusion directives only, and are not valid Datacube OWS configuration!

If you are simply loading config as a Python object, this can be directly achieved by normal programmatic techniques,
e.g.:

::

  handy_config = {
     "desc": "This is a piece of config that might want to use in multiple places",
     "handy": True,
     "reusable": True,
     "difficulty": 3
  }

  "layers": [
    {
       "name": "first_layer",
       "handyness": handy_config,
    },
    {
       "name": "second_layer",
       "handyness": handy_config,
    }
  ]


If you want to reuse chunks of config in json, or wish to combine json with and python in your configuration,
the following convention applies in both Python and JSON:

Any JSON or Python element that forms the full configuration tree or a subset of it,
can be supplied in any of the following ways:

1. Directly embed the config content.

   Don't use inclusion at all, simply provide the config:

   ::

       {
           "a_cfg_entry": 1,
           "another_entry": "llama"
       }

2. Include a python object (by FQN - fully qualified name):

   ::

      {
           "include": "path.to.module.object",
           "type": "python"
      }

   Where  the object named ``object`` in the Python file ``path/to/module.py`` contains the code in example 1.

   The path must be fully qualified.  Relative Python imports are not supported.

   N.B. It is up to you to ensure that the Python file in question is in your Python path and
   that all package directories have a ``__init__.py`` file, etc.


3. Include a JSON file (by absolute or relative file path):

   ::

       {
           "include": "path/to/file.json",
           "type": "json"
       }

   N.B. Resolution of relative file paths is done in the following order:

   a) Relative to the working directory of the web app.

   b) If a JSON file is being included from another JSON file, relative to
      directory in which the including file resides.

Note that this does not just apply when the included python or json entity is a dictionary/object.
Any of the above include directives could expand to an array, or even to single integer or string.

General Config Structure
------------------------

At the top level, the Datacube OWS configuration is a single dictionary with the following elements:

::

  ows_cfg = {
     "global": {
         # Configuration to the whole server across all supported services goes here.
     },
     "wms": {
         # Configuration specific to the WMS and WMTS services goes here.
     },
     "wcs": {
         # Configuration specific to the WCS service goes here.
     },
     "layers: [
         # A list of configurations for layers (WMS/WMTS) (or coverages (WCS)) to be served.
     ]
  }

The `global <https://datacube-ows.readthedocs.io/en/latest/cfg_global.html>`_ section contains configuration that
applies to the whole server across all services and layers.
The `global <https://datacube-ows.readthedocs.io/en/latest/cfg_global.html>`_ section is always required.

The `wms <https://datacube-ows.readthedocs.io/en/latest/cfg_wms.html>`_ section contains configuration that applies to the WMS/WMTS
services aross all layers.
The `wms <https://datacube-ows.readthedocs.io/en/latest/cfg_wms.html>`_ section can be omitted if only the WCS service is
activated (specified in the `global services <https://datacube-ows.readthedocs.io/en/latest/cfg_global.html#service-selection-services>`_
section), or if the default values for all entries are acceptable.

The `wcs <https://datacube-ows.readthedocs.io/en/latest/cfg_wcs.html>`_ section must be supplied if the WCS service is
activated (specified in the `global services <cfg_global#service-selection-services>`_
section).

There is no separate section for WMTS as WMTS is implemented as a thin wrapper around the WMS implementation.

The `layers <cfg_layers.html>`_ section contains a list of layer configurations.  The configured layers define the
layers (in WMS and WMTS) and coverages (in WCS) that the instance serves, and their behaviour. The layers section
is always required.


