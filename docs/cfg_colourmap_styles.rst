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

For details, refer to the
`OWS Masking Syntax <https://datacube-ows.readthedocs.io/en/latest/cfg_masks.html>`_.

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

Legend Title
============

A title can be added to the top of the legend.  The default is no title.

E.g.::

        "legend": {
            # Legend title will be display as "This is a nice legend"
            "title": "This is a nice legend"
        }

Number of columns (ncols)
=========================

By default, the patches and labels are laid out in the legend in a single column.  You can specify
as multi-column format with the ``ncols`` legend entry to the number of desired columns.

Note: You may need to adjust the width of your legend to fit the number of columns (see below).

E.g.::

    "legend": {
        # Use a two column legend layout.
        "ncols": 2,
    }

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

The image size defaults to 4 inches wide by 1.25 inches tall.  The default
dpi for MatPlotLib is 100, so this corresponds to 400x125 pixels unless you
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

-------------------
Multi-Date Requests
-------------------

Colour Map Styles support three approaches to
`multi-date requests <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html#multi-date>`_.

In addition to `standard animated handlers <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html#multi-date>`_
as supported by all style types, Colour Map Styles support two additional approaches
to produce an non-animated image from a multi-date request:

1. Using a variant of the `value_map`_ entry used for the single-date case. This
   is a much simpler way of achieving most use cases.
2. Using an aggregator function, which allows for fully customisable behaviour but
   requires writing Python code.

Multi-date value_map
====================

A value_map in a multi-date handler has the same general structure as the
single date `value_map`_ described above.  The handler must serve a single
number of date values.  The discussion here will assume an `allowed_count_range``
of ``[2, 2]``, but higher values should work.

The ``flags`` or ``values`` (and invert) entry for each rule is replaced by a list of
single-date entries.  A rule is matched for a pixel in the output image
if the pixel matches the provided rules at all date values.  Additionally
an empty rule set of either type for a particular date means
"matches everything for that date that hasn't matched already".

See this simple example using enumeration type rules:

E.g.:

::

    style_example = {
        "name": "multi_date_example",
        "title": "Multidate enumeration example",
        "abstract": "This uses enumeration type rules, but bitflag rules can be used in a similar manner",
        # This is the single date value map.
        "value_map": {
            "band_name": [
                {'title': "A", 'values': [0], 'color': '#000000', 'alpha': 0},
                {'title': "B", 'values': [1], 'color': '#FF0000', 'alpha': 1},
                {'title': "C", 'values': [2], 'color': '#00FF00', 'alpha': 1},
                {'title': "D", 'values': [3], 'color': '#0000FF', 'alpha': 1},
            ]
        },
        "multi_date": [
            {
                "animate": False,
                "preserve_user_date_order": True,
                "allowed_count_range": [2, 2],
                #
                # This is multi-date value-map for a handler with allowed count of 2,
                # so instead of being a list of integers, the values section of each
                # rule is a list of two lists of integers.
                #
                "value_map": {
                    "band_name": [
                        # Simple example rules
                        {'title': "A (unchanged)", 'values': [[0], [0]], 'color': '#000000', 'alpha': 1},
                        {'title': "B -> A", 'values': [[1], [0]], 'color': '#300000', 'alpha': 1},

                        # This matches all remaining cases that end in type A, so C->A and D->A
                        {'title': "Other -> A", 'values': [[], [0]], 'color': '#003030', 'alpha': 1},

                        # This covers C->C, D->D, C->D and D->C
                        {'title': "C/D -> C/D", 'values': [[2, 3], [2, 3]], 'color': '#00A0A0', 'alpha': 1},

                        # B to anything - except A, as that has already been matched by a previous rule.
                        {'title': "B -> Other", 'values': [[1], []], 'color': '#A00000', 'alpha': 1},

                        # Matches all remaining combinations
                        {'title': "Everything else", 'values': [[], []], 'color': '#FFFFFF', 'alpha': 1},
                    ]
                },
            }
        ]
    }

This fanciful example from the test suite illustrates the syntax for
bitflag type rules:

::

    "multi_date": [
        {
            "animate": False,
            "preserve_user_date_order": True,
            "allowed_count_range": [2, 2],
            "value_map": {
                "pq": [
                    {
                        "title": "Bland to Tasty",
                        "flags": [
                            {"flavour": "Bland"}, # Rules for first date
                            {"flavour": "Tasty"}, # Rules for second date
                        ],
                        "color": "#8080FF"
                    },
                    {
                        "title": "Was ugly, is splodgy",
                        "flags": [
                            {"ugly": True,},
                            {"splodgy": "Splodgy"}
                        ],
                        "color": "#FF00FF"
                    },
                    {
                        "title": "Woah!",
                        "flags": [
                            {}, # Empty date rule = matches all remaining pixels for that date
                            {"impossible": "Woah!"}
                        ],
                        "color": "#FF0080"
                    },
                    {
                        "title": "Everything else",
                        "abstract": "The rest of what's left",
                        "flags": [{}, {}],
                        "color": "#808080"
                    }
                ]
            }
        }
    ]

Aggregator function
===================

Alternately, you can define an aggregator function using OWS's
`function configuration format <https://datacube-ows.readthedocs.io/en/latest/cfg_functions.html>`_.

The function is passed a multi-date Xarray Dataset and is expected to return a timeless Dataset,
which can then be rendered using either the single-date value-map, or a separate single-date value-map
defined for the handler.

This approach is infinitely flexible, and may be more efficient for some use cases than
using the multidate value map approach.

As a simple example, given the following callback function:

::

    def detect_equals(data: xr.Dataset) -> xr.Dataset:
        # Split data in two date slices
        data1, data2 = (data.sel(time=dt) for dt in data.coords["time"].values)

        equality_mask = data1["level4"] != data2["level4"]

        # Set pixels that are equal in both date slices to 255, set all
        # other pixels at the second date-slice value.
        data1["level4"] = data2["level4"].where(equality_mask, other=255)
        return data1

You can access this with:

::

    "multi_date": [
        {
            "animate": False,
            "preserve_user_date_order": True,
            "allowed_count_range": [2, 2],
            "aggregator_function": {
                "function": "my_module.my_package.detect_equals",
            },
            "value_map": {
                "level4": [
                    {'title': "Unchanged", 'abstract': "Equal", 'values': [255], 'color': '#000000'},
                    # ... Other rules, as per the single-value colour map, not shown.
                ]
            }
        }
    ],

The multi-date value_map is expected to act as single-date value map on the time-flattened
data as returned by the aggregator function.
