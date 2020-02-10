=================
OWS Configuration
=================

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

The global section is always required.

The "wms" section can be omitted if only the WCS service is activated (specified in the "global" section).

The "wcs" section can be omitted if the WCS service is deactivated.

There is no separate section for WMTS as WMTS is implemented as a thin wrapper around the WMS implementation.

The layers section contains a list of layer configurations.  The configured layers define the
layers (in WMS and WMTS) and coverages (in WCS) that the instance serves, and their behaviour.

Global Section
--------------

The "global" section of the root configuration object contains config entries that apply
to all services and all layers/coverages.

The Global section is always required and contains the following entries:

Service Title (title)
=====================

The "title" entry in the global section is a user-readable title that describes the server.
This is written verbatim to the various Capabilities documents and is displayed to users
by most clients.

This entry is a string and is required.  E.g.:

::

   "title": "My organisation's OpenDatacube OGC services.",

Information URL (info_url)
==========================

The "info_url" entry in the global section is a URL providing information about the service
or the organisation providing it.  It will be written to the Capabilities documents and will
likely be presented to users browsing the service.

This entry is required and should be a valid URL.  E.g.:

::

   "info_url": "https://my.domain.com/about_us",


Service Selection (services)
============================

The "services" entry in the global section declares which supported services this server instance
will respond to.  It should be a dictionary containing boolean members labelled with the lower case
names of the services.  E.g. to activate all supported services:

::

    "services": {
       "wms": True,
       "wmts": True,
       "wcs": True
    },

The services section may be omitted, in which case WCS will be deactivated, and WMS and WMTS
will be active.

The server will not start if all services are set to False.

Response Headers (response_headers)
===================================

The "response_headers" entry in the global section defines HTTP headers that will be added to ALL
server responses. It should be a dictionary mapping header names to values.

This entry is optional, and if omitted no special response headers are added.

This example shows a simple CORS header, and is strongly recommended as a minimum (unless
you are handling CORS elsewhere in your deployment).

::

   "response_headers": {
       "Access-Control-Allow-Origin": "*",
   },

Allowed URLS (allowed_urls)
===========================

The "allowed_urls" entry in the global section defines allowed base URLs for service.

It should be a list of strings containing base URLs, and is required.

Requests received which do not match a Base URL in this list will return an error.

E.g.:

::

   "allowed_urls": [
       # Common local dev URLs
       "http://localhost",
       "http://localhost:5000",
       "http://localhost/odc_ows",

       "http://unsecure.domain.com/odc",
       "https://secure.domain.com/ows",
   ]

Co-ordinate Reference Systems (published_CRSs)
==============================================

The "published_CRSs" entry in the global sections declares the list of Co-ordinate
Reference Systems supported by the server instance.

It should be a dictionary of dictionaries, with the labels being recognised by GDAL and Proj4
(ideally EPSG codes, as in the example).  The configuration for each Co-ordinate Reference System
contains the following entries:

geographic
   Boolean indicating whether the projection is geographic, i.e. uses degrees latitude and longitude
   as it's co-ordinates. Required.  Note that at least one geographic CRS must be published.

horizontal_coord
   The label of the horizontal coordinate.  Defaults to "longitude".

vertical_coord
   The label of the vertical coordinate.  Defaults to "latitude".

vertical_coord_first:
   Boolean, indicates whether the CRS expects the vertical coordinate to be given first. Defaults
   to False (horizontal coordinate first).

This section is required and must contain at least one geographical coordinate system (EPSG:4326 -
aka WGS-84 is strongly recommended, but any geographical coordinate system will do).  The
non-geographic Web Mercator CRS (EPSG:3857) is also strongly recommended.

E.g.:

::

   "published_CRSs": {
       "EPSG:3857": {  # Web Mercator
            "geographic": False,
            "horizontal_coord": "x",
            "vertical_coord": "y",
       },
       "EPSG:4326": {  # WGS-84
           "geographic": True,
           "vertical_coord_first": True
       },
       "EPSG:3577": {
           # GDA-94, An Albers projection with good equal-area properties over Australia.
           # Heavily used by Geoscience Australia
           "geographic": False,
           "horizontal_coord": "x",
           "vertical_coord": "y",
       },

   },


Optional Metadata
=================

The remainder of the "global" section contains various metadata entries that are written
directly to the various Capabilities documents.  All metadata in the "global" section
applies to both WMS/WMTS and WCS.  Some further WMS/WMTS-specific server-wide metadata
can be configured in the "wms" section.

All entries listed here are optional and default to blank, or similar, as documented
in the comments to this example:

::

        # Abstract - longer description of the service (Note this text is used for both WM(T)S and WCS)
        # Optional - defaults to empty string.
        "abstract": """This web-service serves georectified raster data from our very own special Open Datacube instance.""",
        # Keywords included for all services and products
        # Optional - defaults to empty list.
        "keywords": [
            "satellite",
            "australia",
            "time-series",
        ],
        # Contact info.
        # Optional but strongly recommended - defaults to blank.
        "contact_info": {
            "person": "Firstname Surname",
            "organisation": "Acme Corporation",
            "position": "CIO (Chief Imaginary Officer)",
            "address": {
                "type": "postal",
                "address": "GPO Box 999",
                "city": "Metropolis",
                "state": "North Arcadia",
                "postcode": "12345",
                "country": "Elbonia",
            },
            "telephone": "+61 2 1234 5678",
            "fax": "+61 2 1234 6789",
            "email": "test@example.com",
        },
        # If fees are charged for the use of the service, these can be described here in free text.
        # If blank or not included, defaults to "none".
        "fees": "",
        # If there are constraints on access to the service, they can be described here in free text.
        # If blank or not included, defaults to "none".
        "access_constraints": "",

