====================================
OWS Configuration - Colourmap Styles
====================================

.. contents:: Table of Contents

Colour-Map Styles
-----------------

Colour-map Styles are `styles <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html>`_ where
each pixel is mapped to one particular colour from a fixed pallet
by applying a logical decision tree to the flag data for that pixel.

Colour-map styles support the
`elements common to all styles <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html#common-elements>`_.

Colour-map styles also have `value_map <#value-map>`_ entry that describes
how the colour of individual pixels is determined.

Colour-map styles support `automatic legend generation <#legend>`_.

---------
value_map
---------

The ``value_map`` is dictionary mapping bands to a list of `value rules <#value-rule-format>`_.
The key is a name or alias of a bitmap band.  Multiple bands are possible
but it is strongly recommended to use only a single band, because the order in which
rules are processed cannot be guaranteed in a multiple band scenario.

A value rule set is a list of `value rules <#value-rule-format>`_.  The rules are applied in order.  Each pixel
will take the the colour specified by the first value rule in the set that the pixel satisifies.  Any pixel
that does not match any rules will be fully transparent.

E.g.::

    "value_map": {
        "band_1": [
            band1_rule1,
            # A pixel that matches both band1_rule1 AND band2_rule2 will be
            # coloured according to band1_rule1, as it appears first in the
            # list.
            band1_rule2,
            band1_rule3,
            # A pixel that doesn't match any rules will remain transparent.
        ],
        # Multiple bands are strongly discouraged as you have
        # no control over whether the band1 rules or band2 rules
        # will applied first.  Multiple bands can only be safely used
        # where the structure of the data means that no single pixel can
        # match a rule for both bands.
        #
        # "band_2": [
        #   band2_rule1,
        #   band2_rule2,
        # ],
    },

Value Rule Format
=================

Color, Alpha and Mask
+++++++++++++++++++++

Each rule must have a ``color`` entry that specifies the appearance of pixels that
match the rule.  The ``color`` entry is in html RGB hex format.

The ``alpha`` and ``mask`` entries are optional and allow transparency.  ``alpha`` should
be a floating point number between 0.0 (fully transparent) and 1.0 (fully opaque)
and defaults to 1.0 (i.e. fully transparent).  The ``mask`` entry is boolean (default
False).  Setting ``mask`` to true is the same equivalent to setting ``alpha`` to
0.0.  (A third option would be to use the standard style
`pq_masks <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html#bit-flag-masks-pq-masks>`_.
Bit-flag Masks (pq_masks)

syntax.)

to achieve the same effect

``color`` is still required when mask is True, but is not used in this case.

E.g.::

    # fully opaque red
    "color": "#FF0000",

    # 50% transparent green
    "color": "#00FF00",
    "alpha": 0.5,

    # Fully transparent (note that color is required but not used)
    "color": "#999999",
    "mask": True

Title and Abstract
++++++++++++++++++

Each rule must have a title and abstract which is used for automatic legend generation.
The text for the corresponding legend entry will be "<title> - <abstract>".

E.g.::

    "value_map": {
        "bitflag_band": [
            {
                # legend entry text will be "Open Forest - (50% - 80% cover)"
                "title": "Open Forest",
                "abstract": "(50% - 80% cover)",
                ...
            },
        ]
    }


Rules
+++++

Each Value Rule must also specify the rule to evaluate when it applies.

This can be done either by treating the band as a bit-flag (
with the `flags <#bitflag-rules-flags>`_ entry) or as an enumeration (
with the `values <#enumeration-rules-values>`_ entry).

Bitflag Rules (flags)
&&&&&&&&&&&&&&&&&&&&&

For bitflag bands, the actual logic of the Value Rule is contained in the "flags" entry.

The flags entry is a dictionary with one of three possible formats.  Note
that formats cannot be combined.  In particular ``and`` and ``or`` logic cannot
be combined in a single rule.

Refer to the OpenDataCube metadata for the underlying product for the
valid bitflag names.

Simple Rules
@@@@@@@@@@@@

A simple rule allows matching a single bitflag value.
The ``flags`` dictionary contains a single entry, the key is a valid bitflag
for the band, and the value is boolean.

E.g.::

    "value_map": {
        "bitflag_band": [
            ...
            {
                ...
                "flags": {
                    # matches all pixels that have not already matched a previous rule
                    # and have the "open_forest" bit flag set to True.
                   "open_forest": True,
                }
            },
            ...
    ]

And Rules
@@@@@@@@@

And Rules allow a pixel match if all the specified comparisons match. The flags
entry contains an "and" dictionary that in turn contains the individual comparisons.

E.g.::

    "value_map": {
        "bitflag_band": [
            ...
            {
                ...
                "flags": {
                    "and": {
                        # matches all pixels that have not already matched a previous rule
                        # and have the "open_forest" bit flag set to True AND the "underwater"
                        # bit flag set to False.
                       "open_forest": True,
                       "underwater": False,
                    }
                }
            },
            ...
    ]

Or Rules
@@@@@@@@

Or Rules allow a pixel match if any of the specified comparisons match. The flags
entry contains an "or" dictionary that in turn contains the individual comparisons.

E.g.::

    "value_map": {
        "bitflag_band": [
            ...
            {
                ...
                "flags": {
                    "or": {
                        # matches all pixels that have not already matched a previous rule
                        # and have either the "open_forest" or the "closed_forest" bit flag set
                        # to True.
                       "open_forest": True,
                       "closed_forest": True,
                    }
                }
            },
            ...
    ]

Enumeration Rules (values)
&&&&&&&&&&&&&&&&&&&&&&&&&&

For bitflag bands, the actual logic of the Value Rule is contained in the "values" entry.

The "values" entry is a list of integers.  Pixels whose exact value is in this list satisfy
the rule.

E.g.

::

    "value_map": {
        "enum_band": [
            ...
            {
                ...
                # Matches pixels whose value is exactly either 2, 3, 7 or 15.
                "values": [2, 3, 7, 15],
            },
            ...
    ]


------
Legend
------

Colour map styles support automatic legend configuration.

Automatic legend generation can be deactivated using the
``show_legend`` and ``url`` legend elements
`common to all styles <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html#legend>`_.
(``show_legend`` is ``True`` by default for colour-map styles.)

A patch and label is added to the legend for each value rule in the
configuration.  See `title and abstract <#title-and-abstract>`_ for
customising the label of each rule.

Values passed to MatPlotLib
===========================

Colour ramp auto-legends are created using the MatPlotLib library. The following
values are passed directly to the MatPlotLib library. Please refer to the
`MatPlotLib documentation <https://matplotlib.org/contents.html>`_ for
further information.

Image Size
++++++++++

The ``width`` and ``height`` values are passed to matplotlib to specify the size
of the generated image.

The image size defaults to 3 inches wide by 1.25 inches tall.  The default
dpi for MatPlotLib is 100, so this corresponds to 300x125 pixels unless you
have over-ridden the default dpi.

E.g.::

    "legend": {
        "width": 4.5,
        "height": 2.1
    }

MatPlotLib rc params
++++++++++++++++++++

Other MatPlotLib customisations (as they would appear in a .matplotlibrc file)
can be specified with the optional ``rcParams`` element, defaulting to {}, meaning
the MatPlotLib defaults for all options.

For a full list of possible options refer to
`the MatPlotLib documentation <https://matplotlib.org/3.2.2/tutorials/introductory/customizing.html>`__

E.g.::

    "legend": {
        "rcParams": {
                 "lines.linewidth": 2,
                 "font.weight": "bold",
        },
    }
