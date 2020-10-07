=================
OWS Configuration
=================

.. contents:: Table of Contents

Layers Section
--------------

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
(a `Product Layer <#product-layer-configuration-product_name>`_), or
to several Open Data Cube products with identical band and
metadata structure (e.g. matching Sentinel-2A and Sentinel-2B
products) (a `Multiproduct Layer <#multiproduct-configuration-multiproduct-product_names>`_).

It also possible to combine bands with differing
bands, but only bands common to both products can be accessed.
(e.g. Landsat-7 and Landsat-8 data could be combined, but the
coastal_aerosol band which is only available on Landsat-8 could
not be used.)

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

* "month"
  Data is expected to be monthly summary data, with a begin-time
  corresponding to the start of the month (UTC).

* "year"
  Data is expected to be annual summary data, with a begin-time
  corresponding to the start of the year (UTC).

(All datacube_ows services currently only accept requests by
date.  Any time component in the request will be ignored.)

Note that it will usually be necessary to rerun update_ranges.py
for the layer after changing the time resolution.

---------------------------
Dynamic Data Flag (dynamic)
---------------------------

The "dynamic" entry is an optional boolean flag (defaults to
False.  If True then range values for the layer are not cached,
meaning calls to update_ranges.py for the layer take effect
immediately.

------------------------
Bands Dictionary (bands)
------------------------

The "bands" section is required for all named layers.
It contains a dictionary of supported bands and alises:

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
Open Data Cube instance for all the ODC products configured for the layer.
Band aliases must be unique within a layer, and must not match any of the
native band names in the dictionary.

Band aliases are useful:

* when the native band names are long, cumbersome or obscure.

* when you wish to share configuration chunks that reference
  bands between layers but the native band names do not match.

---------------------------------
Resource Limits (resource_limits)
---------------------------------

Some requests require more CPU and memory resources than are
available (or that the system administrator wishes to make
available to a single request).  Datacube-ows provides several
mechanisms to help allow expensive requests to terminate
early, avoiding excessive resource consumption.

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
            "min_zoom_factor: 500.0,
            "max_datasets": 6
        },
        "wcs": {
            "max_datasets": 16
        }
    }

Resource Limits (wms)
+++++++++++++++++++++

When a WMS GetMap (WMTS GetTile) request exceeds a configured resource
limit setting, a tile containing a shaded polygon indicating where data
is available but not the actual data.

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

+++++++++++++++
min_zoom_factor
+++++++++++++++

The first WMS/WMTS resource limit is min_zoom_factor.  It
gives a more consistent transition for users when zooming
and is generally the preferred way to constrain resource
limits.

The zoom factor is a (floating point) number calculated from
the request in a way that is independent
of the CRS. A higher zoom factor corresponds to a more
zoomed in view.

If the zoom factor of the request is less than the
configured minimum zoom factor (i.e. is zoomed out too far)
then the resource limit is triggered.

(If you want a more technical explanation, it is the inverse
of the determinant of the affine matrix representing the
transformation from the source data to the output image.)

Values around 250.0-800.0 are usually appropriate.  min_zoom_factor
is optional and defaults to 300.0.

++++++++++++
max_datasets
++++++++++++

The second WMS/WMTS resource limit is max_datasets.  It is an integer that
specifies the maximum number of Open Datacube datasets that can be read
from during the request.  A value of zero is interpreted to mean "no maximum
dataset limit" and is the default.

Resource Limits (wcs)
+++++++++++++++++++++

When a WCS GetCoverage request exceeds a configured resource
limit setting, an error is returned to the user.

The only resource limit available to WCS currently is max_datasets,
which works the same as in wms, `described above <#max_datasets>`_.

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
    ]

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
data for each dataset is fused in OWS outside of ODC.  This is rarely what
you want, but is required for solar angle corrections.

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
related product, or in some cases a completely independent product.

Some entries have corresponding entries in
the `image processing section <#image-processing-section-image_processing>`_
described above.  Items in this section only affect WMS/WMTS.

E.g.

::

    "flags": {
        "band": "pixelquality",
        "product": "ls8_pq",
        "fuse_func": "datacube.helpers.ga_pq_fuser",
        "manual_merge": False,
        "ignore_info_flags": ["noisy"],
        "ignore_time": False
    }

Flag Band (band)
++++++++++++++++

The name of the measurement band to be used for style-based masking.

Pixel-quality bitmask bands or flag bands can be used.

Required, unless the whole "flags" section is empty or None.

Flag Product(s) (product/products)
++++++++++++++++++++++++++++++++++

The Flag Band is assumed to belong to the main layer product/products but this
can be over-ridden with the "product" (for Product Layers) or "products"
(for Multiproduct Layers) entry.

For Product Layers, specify a single ODC product name, for Multiproduct Layers,
specify a list of ODC product names, which should map one-to-one to the main
`product_names <#multiproduct-layer-configuration-multi_product-product_names>`_ list.

E.g. Product Layer, flag band is in the main layer product:

::

    "product_name": "ls8_combined",
    "flags": {
        "band": "pixelquality"
    }

Product Layer, flag band is in a separate product:

::

    "product_name": "ls8_data",
    "flags": {
        "band": "pixelquality",
        "product": "ls8_flags"
    }

Multiproduct Layer, flag band is in separate products mapping to main layer products:

::

    "multi_product": True,
    "product_names": ["s2a_data", "s2b_data"],
    "flags": {
        "band": "pixelquality",
        "products": ["s2a_flags", "s2b_flags"]
    }

Multiproduct Layer, flag band is in a single separate product:

::

    "multi_product": True,
    "product_names": ["s2a_data", "s2b_data"],
    "flags": {
        "band": "pixelquality",
        "products": ["s2_combined_flags", "s2_combined_flags"]
    }

Flag Fuse Function (fuse_func)
++++++++++++++++++++++++++++++

Only applies if the flag band is read from a separate product
(or product).  Equivalent to the `fuse function in the
image_processing section <#fuse-function-fuse_func>`_.
Always optional - defaults to None.

Manual Flag Merge (manual_merge)
++++++++++++++++++++++++++++++++

Only applies if the flag band is read from a separate product
(or product).  Equivalent to the `manual merge in the
image_processing section <#manual-merge-manual_merge>`_.
Optional - defaults to False.

Ignore Time (ignore_time)
+++++++++++++++++++++++++

Optional boolean flag. Defaults to False and only applies if
the flag band is read from a separate product.

If true, OWS assumes that flag product has no time dimension
(i.e. the same flags apply to all times).

Ignore Info Flags (ignore_info_flags)
+++++++++++++++++++++++++++++++++++++

An optional list of flags which should be excluded from
GetFeatureInfo responses.  Defaults to an empty list, meaning
all flags defined in the ODC metadata will be included
in WMS and WMTS GetFeatureInfo responses.

-----------------------
Layer WCS Section (wcs)
-----------------------

This section is optional, but if the WCS service is
active and this section is omitted, then this layer
will not appear as a coverage in WCS (but will still
appear as a layer in WMS/WMTS).

E.g.

::

    "wcs": {
        "native_crs": "EPSG:3577",
        "native_resolution": [25.0, 25.0],
        "default_bands": ["red", "green", "blue"]
    }

Native Coordinate Reference System (native_crs)
+++++++++++++++++++++++++++++++++++++++++++++++

In many cases, OWS can determine the native coordinate system
directly from the ODC metadata. In such cases the native_crs
need not be explicitly provided (and indeed, will be ignored
if it is.)

However some ODC products do not have a product wide CRS, but
rather define a native CRS from for each dataset from a family
of related CRSs. (e.g.
Sentinel-2 data is usually packaged like this.)  In this case
you must manually declare a "native" CRS (if WCS is active).
This can be any CRS
declared in the `global published_CRSs section
<https://datacube-ows.readthedocs.io/en/latest/cfg_global.html#co-ordinate-reference-systems-published_CRSs>`_
and need not be related to the CRSs that the data is actually
stored in.

Native Resolution (native_resolution)
+++++++++++++++++++++++++++++++++++++

In many cases, OWS can determine the native resolution
directly from the ODC metadata. In such cases the native_resolution
need not be explicitly provided (and indeed, will be ignored
if it is.)

A native_resolution is required for WCS-enabled layers where
is cannot be determined from ODC metadata.  It is
the number of native CRS units (e.g. degrees, metres) per pixel in
the horizontal and vertical directions.

E.g. for EPSG:3577 (measured in metres) you would use (25.0, 25.0)
for Landsat and (10.0, 10.0) for Sentinel-2.

Depending on the native CRS and the way the data has been processed,
Landsat resolution may be closer to 30m. If the native CRS is measured
in degrees, then the native resolution must also be measured in
degrees, not metres.

Default WCS Bands (default_bands)
+++++++++++++++++++++++++++++++++

List the bands included in response to a WCS request that does not
explicitly specify a band list.

Must be provided if WCS is active, and must contain at least one band.
Bands must be declared in the layer's `bands dictionary <#bands-dictionary-bands>`_
and may use native band names or aliases.

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
`inherited <https://datacube-ows.readthedocs.io/en/latest/configuration.html#configuration_inheritance>`_
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