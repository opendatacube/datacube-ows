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
(a `Product Layer <#product-layer-configuration>`_), or
to several Open Data Cube products with identical band and
metadata structure (e.g. matching Sentinel-2A and Sentinel-2B
products) (a `Multiproduct Layer <#multiproduct-configuration>`_).

It also possible to combine bands with differing
bands, but only bands common to both products can be accessed.
(e.g. Landsat-7 and Landsat-8 data could be combined, but the
coastal_aerosol band which is only available on Landsat-8 could
not be used.)

---------------------------
Product Layer Configuration
---------------------------

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

--------------------------------
Multiproduct Layer Configuration
--------------------------------

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


