=================
OWS Configuration
=================

.. contents:: Table of Contents

Global Section
--------------

The "global" section of the `root configuration object
<configuration.rst>`_
contains config entries that apply
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


.. _services:

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

