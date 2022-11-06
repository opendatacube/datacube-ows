==========================
OWS Configuration - Layers
==========================

.. contents:: Table of Contents

Layers Section
==============

The "layers" section of the `root configuration object
<https://datacube-ows.readthedocs.io/en/latest/configuration.html>`_
contains definitions of the various layers (WMS/WMTS)
and coverages (WCS) that installation serves.

The "layers" section is always required and should include
at least one named layer (defined below).

The "layers" section is a list of Layer configurations.

A layer may be either:

* A `named layer <#named-layers>`_ which represents a queryable
  WMS layer and a corresponding WCS coverage

* A `folder layer <#folder-layers>`_ which represents
  a folder in WMS, allowing layers to be organised in a
  hierarchical way. Folder layers are not themselves queryable but
  themselves contain a list of further child layers, which in
  turn may be named layers or folders.

Note that Folder layers are
only used by WMTS and WMS.  WCS has no concept of a
hierarchy of coverages, and so simply uses a flattened
list of all declared named layers for it's list of
coverages.

Common Elements
===============

The following configuration entries and sections apply to both
`named layer <#named-layers>`_ and `folder layer <#folder-layers>`_.

------------------
Title and Abstract
------------------

The "title" entry provides a short human-readable title for the layer
and is required for all layers.

The "abstract" entry provides a longer human-readable description
of the layer.  "Abstract" is required for top-level layers -
layers directly included in the "layers" section. Layers that are
included via a `folder layer <#folder-layers>`_ can omit the abstract,
in which case the abstract of the parent layer is used.

E.g.

::

    "title": "Landsat-8 Daily Images",
    "abstract": """Landsat is a satellite.  8 is a number. Daily means
    once per day.  Images are visual depictions of data.  This is an
    abstract of a layer.  I hope that's all clear, thanks for taking
    the time to read this helpful and informative abstract.
    """,

--------
Keywords
--------

Keywords may be defined at the layer level.  Keywords are hierarchical
and cumulative.  A layer will advertise all of:

* The keywords defined explicitly for the layer.

* The keywords defined for all parent folder layers in the layer hierarchy.

* The keywords defined in the `global keywords <https://datacube-ows.readthedocs.io/en/latest/cfg_global.html#optional-metadata>`_ section.

E.g.:

::

    "keywords": [
        "landsat",
        "landsat8",
    ],

-----------
Attribution
-----------

Attribution is optional and is used by WMS only.

Attribution is hierarchical - if not supplied the setting from the closest parent
layer that has an attribution is used.  Or if no parent layers supply an attribution
either then the default value defined in `the wms section <https://datacube-ows.readthedocs.io/en/latest/cfg_wms.html#default-attribution-attribution>`_
is used.  Or if there is no default value defined either, no attribution will be
reported.

The structure of the attribution section is the same as described in
`the wms section <https://datacube-ows.readthedocs.io/en/latest/cfg_wms.html#default-attribution-attribution>`_.

Folder Layers
=============

In addition to the `common elements <#common-elements>`_ described
above, folder layers have a "layers" element which is a list of child
layers (which may be named layers, folder layers with their own
child layers).

A folder layer may also have a ``label`` element which is used only
for
`metadata separation and internationalisation
<https://datacube-ows.readthedocs.io/en/latest/configuration.html#metadata-separation-and-internationalisation>`_.
Each folder's layer
must be globally unique.  A unique label based on the folder's position
in the folder hierarchy is generated if one is not supplied.

E.g.

::

    "layers": [
        {
            "title": "Parent Folder",
            "abstract": "...",
            "layers": [
                {
                    # A named child layer
                    ...
                },
                {
                    "title": "Child Folder",
                    "layers": [
                        # Grand-child layers
                        ...
                    ]
                }
            ]
        }
    ]

Named Layers
============

A named layer describes a queryable layer (WMS/WMTS) and the corresponding
coverage (WCS).

In addition to the `common elements <#common-elements>`_ described
above, named layers have the following configuration elements:

----
Name
----

Named layers must have a name. (Hopefully no surprises there.)

The name is a symbolic identifier for the layer. Two layers in the
one config file cannot share a common name.  The name is used by WMS,
WMTS and WCS queries to identify the layer of interest, but is otherwise
not exposed to users.

E.g.

::

    {
        "title": "Landsat 8 Daily Images",
        "abstract": "...",
        "name": "ls8_daily"
        ...
    }

--------------------------------------
Product Layers and Multiproduct Layers
--------------------------------------

Named layers can map to either a single Open Data Cube product
(a `Product Layer <#product-layer-configuration-product-name>`_), or
to several Open Data Cube products with identical band and
metadata structure (e.g. matching Sentinel-2A and Sentinel-2B
products) (a `Multiproduct Layer <#multiproduct-configuration-multi-product-product-names>`_).

It also possible to combine bands with differing
bands, but only bands common to both products can be accessed.
(e.g. Landsat-7 and Landsat-8 data could be combined, but the
coastal_aerosol band which is only available on Landsat-8 could
not be used.)

Combining products from different platforms or product families is possible
as long as the following rules are obeyed for all supported bands:

1) Each band must have at least one ODC alias in common across all included products
2) Each band must have the same datatype (``numpy.dtype``) and nodata value across all included products.

------------------------------------------
Product Layer Configuration (product_name)
------------------------------------------

For a product layer, the "multi_product" entry must be set to
False or omitted (False is the default), and the ODC product name
should be supplied in the "product_name" entry.

E.g.

::

    {
        "title": "Landsat 8 Daily Images",
        "abstract": "...",
        "name": "ls8_daily",
        "product_name": "ls8_ard",
        ...
    }

---------------------------------------------------------------
Multiproduct Layer Configuration (multi_product, product_names)
---------------------------------------------------------------

For a multiproduct layer, the "multi_product" entry must be set to
True, and the ODC product names should be supplied as a list in the
"product_names" entry.

E.g.

::

    {
        "title": "Sentinel 2A/B Combined Daily Images",
        "abstract": "...",
        "name": "s2_daily",
        "multi_product": True,
        "product_names": ["s2a_ard", "s2b_ard"],
        ...
    }

If the
`manual merge option in the
image_processing section discussed below<#manual-merge-manual-merge>`_
is set to ``True``, then overlapping products are layered according to the priority
order specified in ``product_names``

E.g. the following config offers a combined landsat/sentinel-2 layer, with Sentinel-2 data used in
preference to Landsat where both are available:

::

    {
        "title": "Sentinel 2/Landsat Combined Daily Images",
        "abstract": "...",
        "name": "ls_s2_daily",
        "multi_product": True,
        "product_names": [
            "s2a_ard", "s2b_ard",
            "ls5_ard", "ls7_ard", "ls8_ard", "ls9_ard",
        ],
        "image_processing": {
            "manual_merge": True,
            ...
        },
        ...
    }

---------------------------------------------------------
Low-Resolution Summary Products - low_res_product_name(s)
---------------------------------------------------------

If available, a parallel low-resolution summary product can be configured to
be used for heavily zoomed-back queries that would require excessive
Disk or S3 I/O to access from the main high-resolution product.

This is done with the optional low_res_product_name entry (or for
multi-product layers, the low_res_product_names entry) which is
set to the ODC product name of the summary product (or list of ODC product
names for multi-product layers)
For multi-product
layers, the low_res_product_names list must map directly to the product_names
list, if provided.

E.g.

::

    "product_name": "main_product",
    "low_res_product_name": "summary_product",

or for multi-product layers:

::

    "product_names": ["main_product_1", "main_product_2"]
    "low_res_product_names": ["summary_product_1", "summary_product_2"]

The conditions under which to switch to the low-resolution product(s)
are defined in the `resource_limits <#resource-limits-resource-limits>`_
section, discussed below.

---------------------------------
Time Resolution (time_resolution)
---------------------------------

The "time_resolution" specifies how data timestamps on the data
are mapped to user-accessible dates. The acceptable values are:

* "raw" (default)
  Data is expected to have a center-time reflecting when
  the data was captured.  This is mapped to a local solar day.
  (i.e. the date below the satellite at the time, not relative
  to a single fixed timezone.)

* "day"
  Data has time dimension with absolute (non-local) day resolution.

* "month"
  Data is expected to be monthly summary data, with a begin-time
  corresponding to the start of the month (UTC).

* "year"
  Data is expected to be annual summary data, with a begin-time
  corresponding to the start of the year (UTC).

(All datacube_ows services currently only accept requests by
date.  Any time component in the request will be ignored.)

Note that it will usually be necessary to rerun `datacube-ows-update
<https://datacube-ows.readthedocs.io/en/latest/database.html#updating-range-tables-for-individual-layers>`_
for the layer after changing the time resolution.

-------------------------------------
WMS Default Time Value (default_time)
-------------------------------------

Specifies which time value to use by default if not specified in request.  Applies to WMS, WMTS and WCS1.

Optional (default = "latest")

Allowed values:

1. "latest" (the default).   Use most recent available date.
2. "earliest".   Use earliest available date.
3. ISO Format date (e.g. "2021-05-26").  If the specified date is not available, a warning is raised and the latest
   available date is used instead.

E.g.

::

    "default_time": "latest",
    # "default_time": "earliest",
    # "default_time": "2020-07-25",

-----------------------------
Regular Time Axis (time_axis)
-----------------------------

The time axis is how OWS publishes the dates for which data is available.  The default
behaviour (``time_axis`` not specified or ``None``) is to use an irregular time axis, where the available dates
(as cached in `the OWS range tables <datacube-ows-update <https://datacube-ows.readthedocs.io/en/latest/database.html>`_)
are listed individually.  These long lists of dates lead to unncessarily large capabilities documents
for all supported protocols.

A regular time axis is where the available dates are published as a start date, an end date and an interval size. This
can result in a dramatic reduction in capabilities document sizes and can be useful for certain types of composite
products.

Specify a regular time axis by declaring a ``time_interval``, which is a positive integer, measured in days:

::

    "time_axis": {
        "time_interval": 14,  # data every 14 days.
    },

The default behaviour is to use the earliest and latest date for the layer from the range tables as the
start and end date.  This can be over-ridden by manually specifying a ``start_date`` and/or an ``end_date``
(using ISO date format). If either is omitted, the earliest or latest (as appropriate) date from the range table
is used.

::

    "time_axis": {
        "time_interval": 1,  # daily data
        "start_date": "1988-01-07", # Data from 1st July 1988 to 31st December 2019
        "end_date": "2019-12-31",
    },


---------------------------
Dynamic Data Flag (dynamic)
---------------------------

The "dynamic" entry is an optional boolean flag (defaults to
False.  If True then range values for the layer are not cached,
meaning calls to update_ranges.py for the layer take effect
immediately.

----------------------
Hiding layers from WCS
----------------------

If WCS is activated globally, by default all named layers are automatically included as WCS coverages.

If you want to support WCS for some layers only, you can disable individual layers from WCS using either of
the following methods:

::

    "wcs": False,

or

::

    "wcs": {
        "disable": True
    },

------------------------
Bands Dictionary (bands)
------------------------

The "bands" section is required for all named layers.
It contains a dictionary of supported bands and aliases:

::

    "bands": {
        "red": ["crimson", "scarlet"],
        "green": ["antired"],
        "blue": []
    }

The snippet above tells OWS that this layer has three bands: red,
green and blue.  Even if the underlying ODC knows about other bands
for the product, they will not be accessible to OWS.

Additionally, this creates three band aliases: crimson and scarlet
for red; and antired for green.  The aliases may then be used elsewhere
in the layer configuration in place of the native band names.  (i.e.
within the config for this layer "red", "crimson" and "scarlet" all
refer to the band with native name "red".)

Band names must be unique within a layer, and must exist in the underlying
Open Data Cube instance (as either canonical band names or ODC band aliases)
for all the ODC products configured for the layer.  Band aliases must refer
to a unique band within a layer.

Band aliases are useful:

* when the native band names are long, cumbersome or obscure.

* when you wish to share configuration chunks that reference
  bands between layers but the native band names do not match.

--------------------------
URL patching (patch_url_function)
--------------------------

An arbitrary function can be supplied to patch data urls for the layer.  URLs from the
ODC database are passed through the patching function before loading.  This can be
used to access data held by commercial data providers that require cryptographic signing
of data urls for authentication (e.g. Microsoft Planetary Computer).  They may also be used
to handle various network proxying or data-migration scenarios where the URLs visible to the
OWS server are different to the URLs at indexing time.

The "patch_url_function" config element is set using OWS's `function configuration format
<https://datacube-ows.readthedocs.io/en/latest/cfg_functions.html>`_.
The function is expected to take a string containing an unpatched url and return a
string containing the patched url.

"patch_url_function" is optional, the default is None, meaning use ODC urls unpatched.

Note that the same function is applied to all products for the layer.  Multi-product
(or separate masking product) scenarios that require a different patching paradigm
per product must depend on the patching function to identify from the unpatched url
which paradigm to apply.

------------------------------------------------------------------------------------
Native Coordinate Reference System and resolution (native_crs and native_resolution)
------------------------------------------------------------------------------------

In many cases, OWS can determine the native coordinate system
and resolution directly from the ODC metadata. In such cases
they need not be explicitly provided (and indeed, will be ignored
if they are.)

However some ODC products do not have a product wide CRS,
but rather define a native CRS from for each dataset from a family
of related CRSs. (e.g. Sentinel-2 data is usually packaged like this.)
In this case you must manually declare a "native" CRS. Similarly,
if the native resolution is included in product-level metadata in
the ODC, it must be declared explicitly.

The "native" CRS and resolution
allows OWS to treat the entire layer as a single coverage, and
are used for calculating request resource limits.

The native_crs can be any CRS
declared in the `global published_CRSs section
<https://datacube-ows.readthedocs.io/en/latest/cfg_global.html#co-ordinate-reference-systems-published-crss>`_
and need not be related to the CRSs that the data is actually
stored in.

The native_resolution is
the number of native CRS units (e.g. degrees, metres) per pixel in
the horizontal and vertical directions.

E.g. for EPSG:3577 (measured in metres) you would use (25.0, 25.0)
for Landsat and (10.0, 10.0) for Sentinel-2.

Depending on the native CRS and the way the data has been processed,
Landsat resolution may be closer to 30m. If the native CRS is measured
in degrees, then the native resolution must also be measured in
degrees, not metres.

E.g.

::

        "native_crs": "EPSG:3577",
        "native_resolution": [25.0, 25.0],

---------------------------------
Resource Limits (resource_limits)
---------------------------------

Some requests require more CPU and memory resources than are
available (or that the system administrator wishes to make
available to a single request).  Datacube-ows provides several
mechanisms to avoid excessive resource consumption by either:

1. progressively increasing the cache-control header max-age value to
allow expensive requests to be cached for longer and prevent cheap
requests from flooding the cache; and/or

2. terminating potentially expensive queries early, preventing them
from consuming excessive resources.

These mechanisms are configured in the "resource_limits" section,
which is a dictionary with two independent sub-sections
`wms <#resource-limits-wms>`_ (for WMS and WMTS) and
`wcs <#resource-limits-wcs>`_ (for WCS), described in
detail below.

E.g.

::

    "resource_limits": {
        "wms": {
            "zoomed_out_fill_colour": [150, 180, 200, 160],
            "min_zoom_level": 7,
            "max_datasets": 12,
            "dataset_cache_rules": [
                {
                    "min_datasets": 5,
                    "max_age": 60*60*24,
                },
                {
                    "min_datasets": 9,
                    "max_age": 60*60*24*14,
                }
            ],
        },
        "wcs": {
            "max_datasets": 18,
            "max_image_size": 2000 * 2000 * 3 * 2,
            "describe_cache_maxage": 60 * 5,
            "dataset_cache_rules": [
                {
                    "min_datasets": 5,
                    "max_age": 60*60*24,
                },
                {
                    "min_datasets": 9,
                    "max_age": 60*60*24*14,
                }
            ],
        }
    }

Resource Limits (wms)
+++++++++++++++++++++

When a WMS GetMap (WMTS GetTile) request exceeds a configured resource
limit setting, one of the following will occur depending on the value
of the `low-resolution summary product(s) <#low-resolution-summary-products-low-res-product-name-s>`_
setting.

If a low-resolution summary product has been defined, then requests that exceed
any configured resource limits will be served from the low-resolution summary
product instead of the main data product.

If no low-resolution summary product is defined, then requests that exceed
any configured resource limits will return a tile containing a shaded polygon
indicating where data is available but not the actual data.

The user experience is typically that a shaded polygon showing the extent
of available data is displayed when zoomed out to the full product extent,
but imagery starts to appear after an appropriate amount of zooming in.

++++++++++++++++++++++
zoomed_out_fill_colour
++++++++++++++++++++++

The "zoomed_out_fill_colour" entry specifies the colour of
the shaded polygon (shown when WMS/WMTS resource limits are exceeded).
It should be list of integers between 0 and 255.  There should be either
three (red, green, blue) or four (red, green, blue, alpha) integers in
the list.  The entry is optional and defaults to (150, 180, 200, 160) -
a semi-transparent light blue.

Note that this entry has no effect if
`low-resolution summary product(s) <#low-resolution-summary-products-low-res-product-name-s>`_
have been declared for the product.

++++++++++++++
min_zoom_level
++++++++++++++

The recommended way to set resource limits is with ``min_zoom_level``.  This refers to
the "GoogleMap" zoom level. i.e. zoom level 0 is the entire world map (EPSG:3857, Web Mercator)
in a single tile, zoom level 1 covers the world in 4 tiles, and so on, with each tile of a
given zoom level made up of 4 tiles of previous level.

The min_zoom_level you set is for a "standard request", as defined below.  The effective
minimum zoom level for actual request is adjusted to correct for the following factors
that can influence I/O and memory resource usage:

* Number of time slices in the request
* Number of bands required by the style (and the size of the datatypes of those bands)
* The number of pixels in the image tile.
* The native resolution of the source data

A "standard request" is considered to be:

* One time slice
* Requiring three 16-bit measurement bands
* 256x256 image tile.
* Native resolution of 25m x 25m.

For example, if ``min_zoom_level`` is set to 6, then a standard request will trigger the resource-limited
behaviour from zoom levels 0 to 5, and fully render from zoom levels 6 and up. Requests that differ from a
standard request will have their effective minimum zoom level automatically adjusted so
that the maximum  memory and I/O resources required for a request is approximately conserved.

Reducing the zoom level by one corresponds to 4 times the resource requirements, so for example:

* Increasing the tile size from 256x256 to 512x512 will *increase* the effective minimum zoom
  level by one.
* A style accessing four time slices instead of one will *increase* the effective minimum zoom
  level by one.
* A request that accesses data with 100m x 100m resolution would *decrease* the effective minimum zoom
  by two.

++++++++++++++++++
max_datasets (WMS)
++++++++++++++++++

The simplest WMS/WMTS resource limit is ``max_datasets``.  It is an integer that
specifies the maximum number of Open Datacube datasets that can be read
from during the request.  A value of zero is interpreted to mean "no maximum
dataset limit" and is the default.

This is typically not a suitable method for managing tiled maps of multi-dataset
products as tiles straddling dataset boundaries will have very different dataset count
to those that don't at the same map zoom level.  If you want the resource limit to
cut in at a consistent zoom level, you should use one of the other resource limits.
However, ``max_datasets`` maybe be a useful fallback to use in conjunction with ``min_zoom_level``
or ``min_zoom_factor`` in some situations.

+++++++++++++++
min_zoom_factor
+++++++++++++++

The other WMS/WMTS resource limit is min_zoom_factor.  It
also gives a more consistent transition for users when zooming
but does not account for the relative resource requirements
like ``max_zoom_level``. It is no longer recommended and will be
deprecated in a future release.

The zoom factor is a (floating point) number calculated from
the request in a way that is independent of the CRS. A higher
zoom factor corresponds to a more zoomed in view. If the
zoom factor of the request is less than the
configured minimum zoom factor (i.e. is zoomed out too far)
then the resource limit is triggered.

(If you want a more technical explanation, it is the inverse
square root of the determinant of the affine matrix representing the
transformation from the source data to the output image.)

Values around 250.0-800.0 are usually appropriate.  ``min_zoom_factor`` is optional and
defaults to None, which means the limit is not applied.

+++++++++++++++++++
dataset_cache_rules
+++++++++++++++++++

Caching behaviour is based purely on the number of datasets (not zoom factor)
and is controlled using the ``dataset_cache_rules`` element.

If the dataset_cache_rules element is not supplied, no cache-control header
is issued on any GetMap/GetTile responses.

If supplied, it consists of a list of cache rule dictionaries.  Each cache rule
dictionary consists of two elements: ``min_datasets`` - an integer declaring the minimum
number of retrieved datasets the rule applies to, and ``max_age`` - an integer declaring the
cache-control max-age value (in seconds) that will be returned for responses covered by
the rule. Cache rules must be declared in ascending order of the min_datasets element.
The min_datasets element must be less than the max_datasets resource limit if one is defined.

GetMap/GetTile requests that either load no datasets (i.e. a blank transparent tile) or exceed
either of the resource limits (i.e. return either a shaded extent polygon or hit
the low-resolution summary product)


E.g.
::

    {
        "max_datasets": 12,
    }

No dataset_cache_rules element.  No cache-control headers are returned on any GetMap requests.

::

    {
        "max_datasets": 12,
        "dataset_cache_rules": [
        ]
    }

Dataset_cache_rules set to an empty list.  Cache-control header will be "no-cache" on all GetMap requests.
Note that this is different behaviour to not including a dataset_cache_rules element at all.

::

    {
        "max_datasets": 12,
        "dataset_cache_rules": [
            {
                "min_datasets": 4,
                "max_age": 86400,  # 86400 seconds = 24 hours
            },
        ]
    }

Cache-control header is returned according to the number of datasets hit:

* 0-3 datasets: no-cache
* 4-12 datasets: max-age: 86400
* 13+ datasets:  no-cache   (high resource fallback - polygons or low-res summary product)


::

    {
        "max_datasets": 12,
        "dataset_cache_rules": [
            {
                "min_datasets": 4,
                "max_age": 86400,  # 86400 seconds = 24 hours
            },
            {
                "min_datasets": 8,
                "max_age": 604800,  # 604800 seconds = 1 week
            },
        ]
    }

Cache-control header is returned according to the number of datasets hit:

* 0-3 datasets: no-cache
* 4-7 datasets: max-age: 86400
* 8-12 datasets: max-age: 604800
* 13+ datasets:  no-cache   (high resource fallback - polygons or low-res summary product)

Resource Limits (wcs)
+++++++++++++++++++++

The considerations for WCS resource limits are different to WMS/WMTS because
WCS is not tiled and the output file properties (e.g. number of pixels, number of bands,
type of bands) therefore vary widely between requests in ways that WMS/WMTS requests
do not.

When a WCS GetCoverage request exceeds a configured resource
limit setting, either an error is returned to the user, or the
request is satisfied from the
`low-resolution summary product(s) <#low-resolution-summary-products-low-res-product-name-s>`_
depending on which limit(s) have been exceeded, and whether a low-resolution
summary product has been defined. See the documentation for each limit below for details.

+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
Cache Control (dataset-cache-rules and describe_cache_maxage)
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

The `dataset_cache_rules <#dataset-cache-rules>`_ element is also
supported for WCS.  It behaves for WCS GetCoverage requests as
documented above for WMS GetMap and WMTS GetTile requests.

An additional element, ``describe_cache_maxage`` is also provided,
which controls the cache control headers for WCS DescribeCoverage requests
for the coverage/layer.  This element is optional, and defaults
to the value set in the
`top-level WCS section<https://datacube-ows.readthedocs.io/en/latest/cfg_wcs.html#describeconverage-default-cache-control-headers-default-desc-cache-maxage>`_

++++++++++++
max_datasets
++++++++++++

``max_datasets`` is an integer that
specifies the maximum number of Open Datacube datasets that can be read
from during the request.  A value of zero is interpreted to mean "no maximum
dataset limit" and is the default.

If a request exceeds this limit, the data is read from the low resolution
summary product. If no low resolution summary product is defined, an error
is returned.

++++++++++++++++
max_image_size
++++++++++++++++

``max_image_size`` is optional and defaults to no limit. If set, ``max_image_size``
specifies a maximum size in bytes for the uncompressed image raster.

E.g. a 4096x2048 pixel image, containing three ``int16`` type data-bands
corresponds to an image size of:

::

    pixel_count = 4096 * 2048 = 8388608
    pixel_bytes = 3 * 2 = 6
    image_size = pixel_count * pixel_bytes = 50331648

If the image requested exceeds the ``max_image_size``, an error is always returned.


-------------------------------------------
Image Processing Section (image_processing)
-------------------------------------------

The "image_processing" section is required.  It contains
entries that control the dataflow of raster image data
from the ODC to the styling engine.

E.g.::

    "image_processing": {
        "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
        "always_fetch_bands": "pixel_qa",
        "fuse_func": None,
        "manual_merge": True,
        "apply_solar_corrections": True
    }

Extent Mask Function (extent_mask_func)
+++++++++++++++++++++++++++++++++++++++

The "extent_mask_func" determines what portions of
a dataset are potentially meaningful data.

Many metadata formats (including EO3) support a "nodata"
value to be defined for each band.  To use this flag simply
use:

::

    "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",

If this is not appropriate or possible for your data, you can
set an alternative function using OWS's `function configuration format
<https://datacube-ows.readthedocs.io/en/latest/cfg_functions.html>`_.  Some sample functions are included in ``datacube_ows.ogc_utils``.

The function is assumed to take two arguments, data (an xarray Dataset) and
band (a band name).  (Plus any additional arguments you may be passing in
through configuration).

Additionally, multiple extent mask functions can be specified as a list of any of
supported formats.  The result is the **intersection** of all supplied mask functions -
the masks are ANDed together.

E.g.

::

    "extent_mask_func: [
        "datacube_ows.ogc_utils.mask_by_quality",
        "datacube_ows.ogc_utils.mask_by_val",
    ],

To use NO extent mask function, set:

::

    "extent_mask_func: [],


Always Fetch Bands (always_fetch_bands)
+++++++++++++++++++++++++++++++++++++++

"always_fetch_bands" is an optional list of bands that are always
loaded from the Data Cube (defaults to an empty list).  This is
useful if the extent mask function requires a particular band
or bands to be present.

E.g.



    "extent_mask_func": "datacube_ows.ogc_utils.mask_by_quality",
    "always_fetch_bands": ["quality"],

Fuse Function (fuse_func)
+++++++++++++++++++++++++

Determines how multiple dataset arrays are compressed into a
single time array. Specified using OWS's `function configuration
format <https://datacube-ows.readthedocs.io/en/latest/cfg_functions.html>`_.

The fuse function is passed through to directly to the datacube
load_data() function - refer to the Open Data Cube documentation
for calling conventions.

Optional - default is to not use a fuse function.

Manual Merge (manual_merge)
+++++++++++++++++++++++++++

"manual_merge" is an optional boolean flag (defaults to False).  If True,
data for each dataset is fused in OWS outside of ODC.

Manual_merging is always slower than native ODC fusing, but is required
for solar angle corrections, and also for multi-product layers that combine
products from multiple product families and require e.g. one product family
to always be rendered over the top of the other.

Apply Solar Corrections (apply_solar_corrections)
+++++++++++++++++++++++++++++++++++++++++++++++++

"apply_solar_corrections" is an optional boolean flag (defaults to False).
If True, corrections for local solar angle at the time of image
capture are applied to all bands.

This should not be used on "Level 2" or analysis-ready datacube products.

"apply_solar_corrections" requires manual_merge to also be set.

-------------------------------
Flag Processing Section (flags)
-------------------------------

Data may include flags that mark which pixels have missing or poor-quality data,
or contain cloud, or cloud-shadow, etc.  This section describes the
dataflow for such flags from the ODC to the styling engine.
The entire section may be omitted if no flag masking is to be
supported by the layer.

Flag data may come from the same product as the image data, a separate but
related product, a completely independent product, or from any combination
of these.

Some entries have corresponding entries in
the `image processing section <#image-processing-section-image-processing>`_
described above.  Items in this section only affect WMS/WMTS.

The flags section generally consists of a list of flag-band definitions.

Backwards compatibility note:  If there is only one flag-band definition,
it can be supplied directly (i.e. not as a the sole member of a list).
This was the old format from when only a single flag-band definition was
supported and is deprecated and will be removed from a future release.

E.g.

::

    "flags": [
        {
            "band": "pixelquality",
            "product": "ls8_pq",
            "fuse_func": "datacube.helpers.ga_pq_fuser",
            "manual_merge": False,
            "ignore_time": False
        },
        {
            "band": "oceanmask",
            "product": "ls8_coast_detection",
            "fuse_func": "datacube.helpers.ga_pq_fuser",
            "manual_merge": False,
            "ignore_time": False
        }
    ]

Flag Band (band)
++++++++++++++++

The name of the measurement band to be used for style-based masking.

Pixel-quality bitmask bands or enumeration flag bands can be used, although
bitmask bands are better supported and are recommended where possible.

If the flag product(s) is/are the same as the main data product(s), then
an alias from the `bands dictionary <#bands-dictionary-bands>`_ may be used.

Note that it is not possible to combine flag bands from separate products
if they have the same band name (unless one of the products is the main product
and a band alias is used.)

Required.

Flag Product(s) (product/products)
++++++++++++++++++++++++++++++++++

The Flag Band is assumed to belong to the main layer product/products but this
can be over-ridden with the "product" (for Product Layers) or "products"
(for Multiproduct Layers) entry.

For Product Layers, specify a single ODC product name, for Multiproduct Layers,
specify a list of ODC product names, which should map one-to-one to the main
`product_names <#multiproduct-layer-configuration-multi-product-product-names>`_ list.

E.g. Product Layer, flag band is in the main layer product:

::

    "product_name": "ls8_combined",
    "flags": {
        "ls8_internal": {
            "band": "pixelquality"
        }
    }

Product Layer, flag band is in a separate product:

::

    "product_name": "ls8_data",
    "flags": {
        "ls8_external": {
            "band": "pixelquality",
            "product": "ls8_flags"
        }
    }

Multiproduct Layer, flag band is in separate products mapping to main layer products:

::

    "multi_product": True,
    "product_names": ["s2a_data", "s2b_data"],
    "flags": {
        "s2_external": {
            "band": "pixelquality",
            "products": ["s2a_flags", "s2b_flags"]
        }
    }

Multiproduct Layer, flag band is in a single separate product:

::

    "multi_product": True,
    "product_names": ["s2a_data", "s2b_data"],
    "flags": {
        "s2_external_combined": {
            "band": "pixelquality",
            "products": ["s2_combined_flags", "s2_combined_flags"]
        }
    }

Flag Fuse Function (fuse_func)
++++++++++++++++++++++++++++++

Only applies if the flag band is read from a separate product
(or product).  Equivalent to the `fuse function in the
image_processing section <#fuse-function-fuse-func>`_.
Always optional - defaults to None.

Manual Flag Merge (manual_merge)
++++++++++++++++++++++++++++++++

Only applies if the flag band is read from a separate product
(or product).  Equivalent to the `manual merge in the
image_processing section <#manual-merge-manual-merge>`_.
Optional - defaults to False.

Ignore Time (ignore_time)
+++++++++++++++++++++++++

Optional boolean flag. Defaults to False and only applies if
the flag band is read from a separate product.

If true, OWS assumes that flag product has no time dimension
(i.e. the same flags apply to all times).

---------------------------------
Identifiers Section (identifiers)
---------------------------------

The identifiers section is optional.  It is a dictionary mapping names from the
`WMS authorities section <https://datacube-ows.readthedocs.io/en/latest/cfg_wms.html#identifier-authorities-authorities>`_
to an identifier for this layer, issued by each of those authorities.

E.g.

::

    "identifiers": {
        "auth": "ls8_ard",
        "idsrus": "12345435::0054234::GHW::24356-splunge"
    },

------------------
URL Section (urls)
------------------

The urls section provides the values that are included in the FeatureListURLs and
DataURLs sections of a WMS GetCapabilities document. Multiple of each may be defined
per layer. (WMS only, does not apply to WMTS or WCS.)

The entire section and the "features and "data" subsections within it are optional. The
default is an empty list(s).

Each individual entry must include a url and MIME type format.

FeatureListURLs point to "a list of the features represented in a Layer".
DataURLs "offer a link to the underlying data represented by a particular layer"

E.g.

::

    "urls": {
        "features": [
            {
                "url": "http://domain.tld/path/to/page.html",
                "format": "text/html"
            },
            {
                "url": "http://another-domain.tld/path/to/image.png",
                "format": "image/png"
            }
        ],
        "data": [
            {
                "url": "http://abc.xyz/data-link.xml",
                "format": "application/xml"
            }
        ]
    },

-----------------------------------
Feature Info Section (feature_info)
-----------------------------------

The "feature_info" section is optional and allows some customisation of WMS and WMTS
GetFeatureInfo responses.

UTC Dates (include_utc_dates)
+++++++++++++++++++++++++++++

"include_utc_dates" is optional and defaults to False.

If True, then available dates are supplied in two separate lists in
GetFeatureInfo responses: the
standard list of dates as used by datacube_ows, and a second list of UTC based
days.

This configuration option is provided to allow compatibility with other systems that
do not use solar days and is not recommended for normal use.

Include Custom Info (include_custom)
++++++++++++++++++++++++++++++++++++

Determines how multiple dataset arrays are compressed into a
single time array. Specified using OWS's `function configuration
format <https://datacube-ows.readthedocs.io/en/latest/cfg_functions.html>`_.

"include_custom" allows custom data to be included in GetFeatureInfo responses. It
is optional and defaults to an empty dictionary (i.e. no custom data.)

The keys of the "include_custom" dictionary are the keys that will be included in the
GetFeatureInfo responses.  They should therefore be keys that are not included by
default (e.g. "data", "data_available_for_dates", "data_links") - if you use one of
these keys, the defined custom data will REPLACE the default data for these keys.

The values for the dictionary entries are Python functions specified using
OWS's `function configuration format <https://datacube-ows.readthedocs.io/en/latest/cfg_functions.html>`_.

The specified function(s) are expected to be passed a dictionary of band values
(as parameter "data") and can return any data that can be serialised to JSON.

E.g.

::

    "feature_info": {
        "include_custom": {
            "timeseries": {
                "function": "datacube_ows.ogc_utils.feature_info_url_template",
                "pass_product_cfg": False,
                "kwargs": {
                    "template": "https://host.domain/path/{data['f_id']:06}.csv"
                }
            }
        }
    }

-----------------------------------
Styling Section (styling)
-----------------------------------

The `"styling" section <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html>`_ describes the WMS and WMTS styles for
the layer.


-----------
Inheritance
-----------

Named layers may be
`inherited <https://datacube-ows.readthedocs.io/en/latest/configuration.html#configuration-inheritance>`_
from previously defined layers.

To lookup a layer by name use the "layer" element in the inherits section:

::

    layer2 = {
        "inherits": {
            "layer": "layer1"
        },
        "name": "layer2",
        "title": "Layer 2",
        "abstract": "Layer 2",
        "product_name": "product2"
    }

Note that a layer can only inherit by name from a parent layer that has already been parsed
by the config parser - i.e. it must appear earlier in the layer hierarchy.  This restriction
can be avoided using direct inheritance.
