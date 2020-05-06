=================
OWS Configuration
=================

.. contents:: Table of Contents

Layers Section
--------------

The "layers" section of the `root configuration object
<configuration.rst>`_
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

* The keywords defined in the `global keywords <cfg_global.rst#optional-metadata>`_ section.

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
either then the default value defined in `the wms section <cfg_wms.rst#default-attribution-attribution>`_
is used.  Or if there is no default value defined either, no attribution will be
reported.

The structure of the attribution section is the same as described in
`the wms section <cfg_wms.rst#default-attribution-attribution>`_.

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

-------------------------------
Flag Processing Section (flags)
-------------------------------

--------------------------
WCS Coverage Section (wcs)
--------------------------

---------------------------------
Identifiers Section (identifiers)
---------------------------------

------------------
URL Section (urls)
------------------

-----------------------------------
Feature Info Section (feature_info)
-----------------------------------

-----------------------------------
Styling Section (styling)
-----------------------------------




