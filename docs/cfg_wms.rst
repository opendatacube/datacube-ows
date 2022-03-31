===============================
OWS Configuration - WMS Section
===============================

.. contents:: Table of Contents

WMS Section
--------------

The "wms" section of the `root configuration object
<https://datacube-ows.readthedocs.io/en/latest/configuration.html>`_
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

GetCapabilities Cache Control Headers (caps_cache_maxage)
=========================================================

The ``caps_cache_maxage`` entry in the ``wms`` section controls the value of the
``Cache-control`` HTTP header returned with WMS/WMTS GetCapabilities responses.

``caps_cache_maxage`` is an optional integer value that defaults to 0, and represents
the maximum age in seconds that the Capabilities document should be cached.

Note that OWS does not manage any caching itself, this entry controls a standard HTTP
header that instructs upstream cache layers (e.g. AWS Cloudfront) how to behave.

A value of zero means that OWS will recommend that the Capabilities document not be
cached at all, and is the default.  Note that setting this entry to a non-zero value
will introduce additional delays between new data being added to the datacube index
and that data being advertised as available through the service. This value should therefore
be kept fairly short (e.g. a few hours at most).

E.g.

    "wms": {
        "caps_cache_maxage": 3600,   # 3600 seconds = 1 hour
        ...
    }
