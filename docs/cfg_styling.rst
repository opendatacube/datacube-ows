=================
OWS Configuration
=================

.. contents:: Table of Contents

Styling Section
---------------

The "styling" sub-section of a `layer configuration section
<https://datacube-ows.readthedocs.io/en/latest/cfg_layers.html>`_
contains definitions of the various styles
that layer supports.

Styles officially only apply to WMS and WMTS
requests. Datacube-OWS WCS GetCoverage requests will accept
a styles parameter, but this is not compliant with the
standard.  (I.e. an unofficial extension to the WCS standard).
Consequently, the "styling" section is always required,
even if WMS and WMTS services are deactivated.

The "styling" section has two entries: styles and default_style.

styles and default_style
========================

The "styles" list must be supplied, and must contain at least
one style.  There are several different possible style, each
with a slightly different syntax, these are discussed below.

The "default_style" entry is optional and identifies the style
that will be used by default if no style is specified in the
request.  If not supplied, it defaults to the first style in the
"styles" list.

E.g. Here the second style "another_style" is the default. If the
"default_style" entry is removed from this snippet, then the first
style "a_style" will be the default.

::

    "styling": {
        "default_style": "another_style",
        "styles": [
            { "name": "a_style", ... },
            { "name": "another_style", ... },
        ]
    }

multi_date
==========

The WMS and WMTS specs allow queries over multiple date
values.  Datacube OWS will generally reject such queries as it
is generally not clear what such a query means in the
context of raster satellite data.

Datacube OWS does allow the user to define custom
extensions for individual styles to define the behaviour
of multi-date requests.  For example, selecting two
dates within a particular style might return a representation
of the difference between the data for those two dates.

Multi-date behaviour is configured using the ``multi_date``
entry which is a list of multi-date handlers.  `multi_date``
is optional and defaults to an empty list (no multi-date
handlers, single date requests supported only).

The format of a multi-date handler varies depending on the
`style type <#style-types>`__ but a multi-date handler must
always contain a ``allowed_count_range`` entry which specifies
the values for which the handler applies. The ``allowed_count_range``
is a tuple of two integers corresponding the minimum and maximum
number of dates accepted by that handler.  The allowed count ranges
of declared multi-date handlers cannot overlap and a multi-date handler
cannot handle a request with 1 (or 0) dates.

E.g. ::

    "multi_date": [
        {
            # This multi-date handler handles requests with 2 dates.
            "allowed_count_range": [2, 2],
            ...
        },
        {
            # This multi-date handler handles requests with between 3 and 5 dates.
            "allowed_count_range": [3, 5],
            ...
        },
        {
            # ERROR: 1 is not allowed, and 2 is already handled.
            "allowed_count_range": [1, 2],
            ...
        }
    ],

Currently multi_date is only supported
for `Colour Ramp styles <https://datacube-ows.readthedocs.io/en/latest/cfg_colourramp_styles.html#multi-date>`__.

Style Types
===========

There are four distinct possible types of style.

1. `Component Styles <https://datacube-ows.readthedocs.io/en/latest/cfg_component_styles.html>`_

   Each component channel of the image (red, green, blue and optionally
   alpha) is calculated independently from the data for that pixel.

2. `Colour Map Styles <https://datacube-ows.readthedocs.io/en/latest/cfg_colourmap_styles.html>`_

   Each pixel is mapped to one particular colour from a fixed pallet
   by applying a logical decision tree to the date for that pixel.

3. `Colour Ramp Styles <https://datacube-ows.readthedocs.io/en/latest/cfg_colourramp_styles.html>`_

   A single continuous index value is calculated from the data for
   each pixel, and that index value mapped to a graduated colour ramp
   for display.

4. `Hybrid Styles <https://datacube-ows.readthedocs.io/en/latest/cfg_hybrid_styles.html>`_

   A linear combination of a component style and a colour ramp style.

   This can allow for a more easily visually interpreted image, but
   there are usually better ways to achieve the same effect on the
   client side.

Each style type has its own specific config entries as described in the
pages linked above.

---------------
Common Elements
---------------

The following configuration elements are common to all style
types.

Name
++++

It is always required and must be unique within the layer.

E.g.::

    "styles": [
        {"name": "a_style", ...},       # Good.
        {"name": "My Style", ...},      # Poor. (Legal, but the space will need to
                                        # be escaped in URLs.
        {"name": "a_style", ...},       # Error - not unique in layer.
        {"name": "my_style_which_is_mine_and_nobody_elses", ...},
                                        # Poor. (Legal, but not concise)
    ]

Name, Title and Abstract
++++++++++++++++++++++++

The "name" is a symbolic name for the style, for use in request URLs and internally.

The "title" entry provides a short human-readable title for the style.

The "abstract" entry provides a longer human-readable description
of the style.

All three are always required and must be unique within the layer.

E.g.::

    "styles": [
        {
            "name": "simple_rgb",
            "title": "Simple RGB",
            "abstract": "Simple true-colour image, using the red, green and blue bands",
            ...
        },
        {
            "name": "ndvi",
            "title": "NDVI (red, nir)",
            "abstract": "Normalised Difference Vegetation Index - a derived index that correlates well with the existence of vegetation",
            ...
        },
    ]

Bit-flag Masks (pq_masks)
+++++++++++++++++++++++++

The "pq_masks" section allows a style to mask the output image
by the bit flags defined in the `Flag Processing Section <https://datacube-ows.readthedocs.io/en/latest/cfg_layers.html#flag-processing-section-flags>`_ for the layer.

The pq_masks section is a list of mask sections, which are OR'd together.  i.e. A pixel
becomes transparent if it would be made transparent by any of the masks in the list
acting individually.

Mask Sections
@@@@@@@@@@@@@

Each mask section contains a "flags" dictionary and an optional "invert" flag, which
is False by default.

The flags dictionary is passed directly to ``datacube.utils.masking.make_mask``.
The entries of the dictionary represent bitflag comparisons that
are ANDed together.  i.e. A pixel is DISPLAYED if the bitflags
for the pixel match ALL of the entries specified in the "flags" dictionary.

specified by the index match.
The keys of the dictionary are the flag names as used in the ODC metadata

If the "invert" flag is True, then the output inverted (logically NOTed). I.e.
A pixel is MADE TRANSPARENT if the bitflags
for the pixel match ALL of the entries specified in the "flags" dictionary.

E.g.

::

    # Remove pixels
    "pq_masks": [
        {
            "flags": {
                "cloud": "no_cloud",
                "cloud_shadow": "no_cloud_shadow"
            }
        },
        {
            "invert": True,
            "flags": {
                "water": "no_water"
            }
        }
    ],

Legend
++++++

Describes the legend for the style.  Many options only apply for some
of the styles types and are discussed below with the relevant style type.

The following legend options are supported for all styles:

show_legend
@@@@@@@@@@@

If True, a legend url is returned for this style. If False, no legend
url is returned for the style.  Optional - defaults to True if a the
style type supports auto-legend generation, false otherwise.

If false no other legend configuration entries have any effect.

url
@@@

An external url pointing to an image file containing the legend. This
url will not be exposed directly to users, the image file will be
proxied behind an internal url.

A url is required if `show_legend` is True and the style type does NOT
support auto-legend generation.

If the style type DOES support auto-legend generation, setting a url
deactivates legend generation.

E.g.::

     "legend": {
         "show_legend": True,
         "url": "https://somedomain.com/path/to/legend_image.png",
     }


