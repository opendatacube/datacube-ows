==================================
OWS Configuration - Global Section
==================================

.. contents:: Table of Contents

Global Section
--------------

The "global" section of the `root configuration object
<https://datacube-ows.readthedocs.io/en/latest/configuration.html>`_
contains config entries that apply
to all services and all layers/coverages.

The Global section is always required and contains the following entries:

Metadata Separation and Internationalisation
============================================

The following global configuration items are relevant to
`metadata separation and internationalisation
<https://datacube-ows.readthedocs.io/en/latest/configuration.html#metadata-separation-and-internationalisation>`_.

Message File (message_file)
+++++++++++++++++++++++++++

The "message_file" entry gives the path to the message file.

Any metadata fields supplied in the metadata file will over-ride the values
supplied in the configuration.

This is also used as the default message template file location by the ``datacube-ows-cfg (cfg_parser.py)`` utility
when either extracting metadata from config or creating or updating translation templates.

The default is None/null, meaning no message file is used.

Note: the `message_file` configuration entry is not required (except as an intermediate step)
if `translations_directory` is set.  The order of metadata resolution is:

1) If Internationalisation is active via the `translations_directory` config entry, take the
   value from the *.mo file corresponding to the best available language match for the request
   headers.
2) If a translation for the metadata entry is not available, or if internationalisation is not
   active, get the value from the `message_file` if it is configured.
3) Otherwise, fallback to the value in the main body of the config.

Message Domain (message_domain)
+++++++++++++++++++++++++++++++

The message domain used by internationalisation.  Defaults to "ows_cfg".


Translations Directory (translations_directory)
+++++++++++++++++++++++++++++++++++++++++++++++

The path to the directory containing translation subdirectories.  Traditionally known as "locales".
Defaults to None, meaning no translation support.

Required for internationalisation.



Supported Languages (supported_languages)
+++++++++++++++++++++++++++++++++++++++++

A list of supported languages for internationalisation.  Defaults to English only (``['en']``).
The first language listed is treated as the default language, and it is assumed that all metadata
in the main configuration and in the message file are in this default language, with all other
supported languages being translations derived from the default.

List members should be two or three letter ISO-639 language code.

Internationalisation is activated if ``translations_directory`` points to a valid locales
directory structure and ``supported_languages`` includes more than one language.

E.g.

::

    "message_file": "my_project_messages.po",
    "message_domain": "my_project",
    "translations_directory": "/config/translations",
    "supported_languages": [
        "en", # English  - the default language, the language used in the untranslated metadata.
        "fr", # French
        "de", # German
        "sw", # Swahili
        "egy", # Ancient Egyptian - 3 letter ISO-639-2 codes are fine!
    ]

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

It should be a dictionary of dictionaries, with the labels being recognised by Proj4
(ideally EPSG codes, as in the example).  Other CRS formats (i.e. ESRI style WKID)
can be supported by adding them as aliases in your proj4 configuration.

The configuration for each Co-ordinate Reference System
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
non-geographic Web Mercator CRS (EPSG:3857) is also strongly recommended, and is required
if WMTS is activated.

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

If unsure of an `EPSG` code, search in http://epsg.io/


Default Attribution (attribution)
=================================

Attributions can be declared at any level of the layer hierarchy, and are
inherited by child layers from the parent layer unless over-ridden.  An
over-all default attribution may also be declared in the ``wms`` section,
which will serve as the attribution for top-level layers that do not declare
their own attribution section.

All attribution sections are optional.

If provided, the attribution section should be a dictionary containing
the following members:

title
   A user-readable title for the attribution (e.g. the name of the attributed
   organisation.)

url
   A url for the attribution (e.g. the website address of the attributed organisation)

logo
   A dictionary (structure described below) describing a logo for the attribution
   (e.g. the logo of the attributed organisation.)

All of the above elements are optional, but at least one must be
provided if the attribution section exists.

----------------
Attribution Logo
----------------

The structure of the logo section is as follows:

url
   URL of the logo image.  (Required if a logo is specified)

format
   The MIME type of the logo image.  Should match the file type of
   the image pointed to by the url.  (Required if a logo is specified)

width
   The width (in pixels) of the logo image (optional)

height
   The height (in pixels) of the logo image (optional)

E.g.

::

       "attribution": {
            "title": "Acme Satellites",
            "url": "http://www.acme.com/satellites",
            "logo": {
                "width": 370,
                "height": 73,
                "url": "https://www.acme.com/satellites/images/acme-370x73.png",
                "format": "image/png",
            }
        },

Other Optional Metadata
=======================

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
