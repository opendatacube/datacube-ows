=================
OWS Configuration
=================

.. contents:: Table of Contents

WMS Section
--------------

The "wms" section of the `root configuration object
<configuration.rst>`_
contains config entries that apply
to the WMS/WMTS services for all layers.

All entries apply identically to both WMS and WMTS services unless
stated otherwise. All entries in the WMS section are optional and the
entire section can therefore be omitted.

Max Tile Size (max_height/max_width)
=======================================

Tile size is fixed for WMTS requests, so these entries only apply to
WMS requests.   Requests for tiles larger than the configured maximum
height and width will result in an error.  Note that many WMS clients
do not honour the maximum width and height.  For these clients, please
consider using WMTS instead.

The ``max_width`` and ``max_height`` config entries in the ``wms`` section
should be integers.  Both entries are optional, and default to 256 if
not set.

E.g.:

::

   "max_height": 512,
   "max_width": 512,

S3 Data URL Elements
====================

These entries are used for constructing S3 data urls for use in GetFeatureInfo
responses.  This feature is restricted to data stored in AWS S3 and is fairly
specialised to DEA requirements and may not be suitable for other use cases.  All
these entries are optional.

s3_url
   The base url exposing the public S3 bucket containing the data.

s3_bucket
   The name of the S3 bucket.

s3_aws_zone
   The AWS zone where the data is stored.

E.g.

::

        "s3_url": "http://data.au",
        "s3_bucket": "s3_bucket_name",
        "s3_aws_zone": "ap-southeast-2",

Identifier Authorities (authorities)
====================================

The ``authorities`` entry in the ``wms`` section defines URLs for the Identifier
Authorities that can be used in the layer definitions.  If you wish to declare
identifiers for any of your layers, you must define the corresponding Identifier
Authorities here.

This entry is optional. If not provided, no identifier authorities are declared
and no identifiers can be assigned to layers.

Identifiers and Authorities only apply to WMS (not WMTS).

If provided, this entry should be a dictionary mapping authority labels to URLs.

E.g.

::

        "authorities": {
            "auth": "https://authoritative-authority.com",
            "idsrus": "https://www.identifiers-r-us.com",
        },

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

