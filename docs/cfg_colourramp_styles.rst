=======================================
OWS Configuration - Colour-Ramp Styles
=======================================

.. contents:: Table of Contents


Colour-Ramp Styles
------------------

Colour-ramp Styles are `styles <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html>`_ where
a single continuous index value is calculated from the raw data for
each pixel, and that index value is mapped to a graduated colour ramp
for display.

Colour-ramp styles support the
`elements common to all styles <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html#common-elements>`_.

Colour-ramp styles support automatic legend generation. Specialised
legend configuration is described `below <#legend-configuration>`__.

Note on spelling: I am Australian and spell it "colour".  Most software
packages use the US spelling "color".  Within the configuration file
format we use the software conventional spelling, but within the text
of this documentation, I use the UK/Australian spelling.


---------------------------
Calculating the Index Value
---------------------------

There are two methods to specify the calculation of the index value:

Expressions (simple calculations)
=================================

index_expression
++++++++++++++++

The ``index_expression`` entry takes a string written in a simple
expression language.  Lexical units are floating point or integer
constants, or band names (alias-aware).  Simple operators (+, -, /, *, **)
and parentheses work in the usual manner. Note that you
do NOT need to explicitly specify ``needed_bands`` when using
an ``index_expression``.

E.g.

::

   # Simple nir/red NDVI
   "index_expression": "(nir-red)/(nir+red)",


Functions (complex calculations)
=================================

For more complex calculations than are supported by the expression
syntax, The `index_function <#index-function>`__ entry can define how the
index is calculated at each pixel using an arbitrary Python function.
The bands needed for the calculation must be declared in
the `needed_bands list <#needed-bands-list>`__
entry.

index_function
++++++++++++++

The `index_function` allows the user to declare a callback function
to calculate the index value using OWS's
`function configuration format <https://datacube-ows.readthedocs.io/en/latest/cfg_functions.html>`_.
The function is expected to take an xarray Dataset containing all the
bands in the `needed_bands list <#needed-bands-list>`__ (plus any additional
arguments handled by the
`function configuration format <https://datacube-ows.readthedocs.io/en/latest/cfg_functions.html>`_); and returns
an xarray Dataset containing the index value.

A `small library <https://datacube-ows.readthedocs.io/en/latest/cfg_functions.html#band-utils-functions>`_
of general purpose band math functions
are provided in `datacube_ows.band_utils`.

needed_bands list
+++++++++++++++++

The `needed_bands` entry must list the names (or aliases) of
all the bands required by the
`index_function <#index-function>`__.

E.g.::

   # Simple nir/red NDVI
   "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "pass_product_cfg": True,
        "kwargs": {
            "band1": "nir",
            "band2": "red"
        }
   },
   "needed_bands": [ "red", "nir" ]

------------
Colour Ramps
------------

There are three ways to define the colour map:

1. Use the default colour ramp (A fairly garish rainbow ramp
   running from dark purple through blue, green, yellow,
   orange to dark red.)

   To use the default colour ramp, just use the `range <#ramp-scale-range>`__
   style config entry.

2. Use a pre-defined MatPlotLib colour ramp.

   To use a MatPlotLib colour ramp, use the `mpl_ramp <#mpl-ramp>`__
   and `range <#ramp-scale-range>`__ style config entries.

3. Define your own colour ramp.

    To define a custom colour ramp, use the `color_ramp <#manual-color-ramp>`__
    style config entry.

Ramp Scale (Range)
==================

For the Matplotlib colour ramps and the default colour ramp, you need to specify
a value range over which the colour ramp is applied. The `range` element can be set
to a tuple containing the index function values that should be mapped to the lowest
and highest colour ramp values.

Values outside the configured range are clipped to the closest extreme of the colour
ramp.

E.g.::

    "range": [-1.0, 1.0]

mpl_ramp
========

You can use any named matplotlib colour ramp, see
`the matplotlib documentation <https://matplotlib.org/examples/color/colormaps_reference.html>`_ for details.
for a list of supported ramps.

Matplotlib colour ramps run from 0.0 to 1.0 to scale them
to the output of your index function, define a `range <#ramp-scale-range>`__.

E.g.::

    "mpl_ramp": "RdBu",
    "range": [0.0, 1200.0]

Manual color_ramp
=================

A colour ramp can be created manually using the `color_ramp` style configuration
entry.  `color_ramp` should be a list of `colour point definitions <#colour-point-definition>`_.
Each colour point definition describes a mapping from a value to a colour.

The list should be sorted in order of ascending value. If the index function value
for a pixel exactly matches the first colour point
definition value, then that definition's colour is used.   A pixel with a value
less than the lowest value in the ramp
will be the colour of the first colour point.  A pixel with a value greater than than
the highest value in the ramp will be the colour of the last colour point.

Pixels with index function value in between two colour point values will have
be coloured a average of the rgb values of those two colour points, weighted
by the difference between the pixel index function value and the values of the
two colour points.

Colour Point Definition
+++++++++++++++++++++++

Each Colour Point Definition must have a numeric ``value`` and a ``color`` in
html hex format  (e.g. ``#FFFFFF``, ``#ffffff``, ``#FFF`` and ``#fff`` all refer to pure white).

A Colour Point may also optionally have an ``alpha`` entry
which should be a floating point entry between 0.0 (fully
transparent) and 1.0 (fully opaque).  If not provided,
alpha defaults to fully opaque.

A Colour Point may also have an optional "legend" section
which affects automatic legend generation, and is discussed below.

E.g.::

     # <0: transparent
     # 0: black
     # 0-1: ramping from black to red
     # 1-10: ramping from red to blue
     # >10: blue
     "color_ramp": [
        {
            "value": -0.00000000001,
            "color": "#000",
            "alpha": 0.0
        },
        {
            "value": 0.0,
            "color": "#000",
        },
        {
            "value": 1.0,
            "color": "#F00",
        },
        {
            "value": 10.0,
            "color": "#00F",
        }
     ],

--------------------
Legend Configuration
--------------------

Colour-ramp styles support automatic legend generation.

Automatic legend generation can be deactivated using the
`show_legend` and `url` legend elements
`common to all styles <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html#legend>`_.
(`show_legend` is `True` by default for colour-ramp styles.)

Legend Title
============

The legend title defaults to the style name, but can be over-ridden:

E.g.::

        "legend": {
            # Legend title will be display as "This is a nice legend"
            "title": "This is a nice legend"
        }

You can optionally set ``units`` for the legend, which are placed in
parentheses after the title.  The default is to not display units::

        "legend": {
            # Legend title will be display as "This is a nice legend(%)"
            "title": "This is a nice legend",
            "units": "%"
        }

Legend Range
============

The legend range defaults to the
`range <#ramp-scale-range>`_  for the default colour ramp
or `MatPlotLib color ramps <#mpl_ramp>`_.

For `manual colour ramps <#manual-color-ramp>`_, the default
range is between the values of first and last colour point
definitions in the ramp, **excluding** any leading or trailing
colour points that are full transparent (alpha=0.0).

To override the default range, use the ``begin`` and/or ``end`` entries
in the ``legend`` section.  They may be set using integers, numeric strings
or floats.  The vaguries of floating point arithmetic can cause unexpected
behaviour with tick generation (discussed below), so it is strongly recommended to use
numeric strings or integers.

E.g.::

    # Integers, OK
    "legend": {
        "begin": 0,
        "end": 99,
    },

    # Non-integers
    # avoid floats as they may cause issues with tick generation.
    # Use numeric strings instead, like this:
    "legend": {
        "begin": "0.0",
        "end": "0.3",
    },

Legend Ticks
============

"Ticks" are the labeled points along the ramp legend. The default behaviour is to
have exactly two ticks, at the minimum and maximum values.  This can be over-ridden
by any of the following alternative methods:

Regularly spaced ticks, by size (ticks_every)
+++++++++++++++++++++++++++++++++++++++++++++

Ticks are placed at steps of the indicated size, starting from the beginning of the
legend range.  As with "begin" and "end", numeric strings should be used
in preference to floats.

E.g.::

    "legend": {
        # Ticks at 0.0, 0.5 and 1.0
        "begin": "0.0",
        "end": "1.0",
        "ticks_every": "0.5",
    }

    "legend": {
        # Ticks at 0.0, 0.3, 0.6 and 0.9
        # Note that there will be no tick at the maximum position (1.0)
        "begin": "0.0",
        "end": "1.0",
        "ticks_every": "0.3",
    }

Regularly spaced ticks, by count (tick_count)
+++++++++++++++++++++++++++++++++++++++++++++

The indicated number of ticks are spread evenly along the legend.  The count includes the
"end" tick but not the "begin" tick.

E.g.::

    "legend": {
        # Tick at 0.0 only
        "begin": "0.0",
        "end": "1.0",
        "ticks_count": 0,
    }

    "legend": {
        # Ticks at 0.0 and 1.0
        # This is the default behaviour if no tick generation
        # option is specified
        "begin": "0.0",
        "end": "1.0",
        "ticks_count": 1,
    }

    "legend": {
        # Ticks at 0.0, 0.2, 0.4, 0.6, 0.8, 1.0
        "begin": "0.0",
        "end": "1.0",
        "ticks_count": 5,
    }

Explicit ticks (ticks)
++++++++++++++++++++++

Tick locations can also be specified explicitly by setting ``ticks`` to a
list of values.  Again, please use numeric strings rather than floats.

E.g. the following are not possible with tick_count or ticks_every::

        "legend": {
            # No ticks at all
            "begin": "0.0",
            "end": "1.0",
            "ticks": []
        }

        "legend": {
            # Evenly spaced ticks with no ticks on the extremes of the range.
            "begin": "0.0",
            "end": "1.0",
            "ticks": ["0.2", "0.4", "0.5", "0.6", "0.8"]
        }

        "legend": {
            # Unevenly spaced ticks
            "begin": "-5.0",
            "end": "5.0",
            "ticks": ["-5.0", "-1.0", "0.0", "1.0", "5.0"],
        }

Tick Labels
===========

Tick labels can be customised as follows:

decimal_places
++++++++++++++

The number of decimal places to display in tick labels.  The default is one.

E.g.::

        "legend": {
            # Tick labels: "0.00", "0.25", "0.50", "0.75", "1.00"
            "begin": "0.00",
            "end": "1.00",
            "ticks_every": "0.25",
            "decimal_places": 2
        }

        "legend": {
            # Tick labels: "0", "1", "2", "3", "4", "5"
            "begin": "0.0",
            "end": "5.0",
            "ticks_every": "1.0",
            "decimal_places": 0
        }

Prefixes and suffixes
+++++++++++++++++++++

The "default" entry in the "tick_labels" table can set prefixes and suffixes to
be added to all tick labels.

E.g.::

    "legend": {
        "begin": "0.0",
        "end": "1.0",
        "ticks_every": "0.2",
        "decimal_places": 1,
        "tick_labels": {
            # Surround every tick label in square brackets
            "default": {
                "prefix": "[",
                "suffix": "]",
            }
        }

Over-riding labels for individual ticks
+++++++++++++++++++++++++++++++++++++++

If a tick's default label (with no prefix or suffix) appears as a key
in the `tick_labels` dictionary then the prefix, suffix or label of
that tick label can be overridden.

E.g.::

    "legend": {
        "begin": "0.0",
        "end": "1.0",
        "ticks_every": "0.2",
        "decimal_places": 1,
        "tick_labels": {
            # Surround every tick label in square brackets
            "default": {
                "prefix": "[",
                "suffix": "]",
            },
            # There is no "0.0" entry, so the 0.0 tick will be labelled "[0.0]"
            # The 0.2 tick will be labelled "(0.2)"
            "0.2": {
                "prefix": "(",
                "suffix": ")",
            },
            # The 0.4 tick will be labelled "[foo]"
            # (Note the default prefix and suffix are still applied)
            "0.4": {
                "label": "foo",
            },
            # The 0.6 tick will be labelled "bar" with no prefix or suffix
            "0.6": {
                "prefix": "",
                "label": "bar",
                "suffix": "",
            },
            # The 0.8 tick will be labelled ":-)"
            "0.8": {
                "prefix": ":",
                "label": "-",
                "suffix": ")",
            },
            # There is no "1.0" entry, so the 1.0 tick will be labelled "[1.0]"
        }

Values passed to MatPlotLib
===========================

Colour ramp auto-legends are created using the MatPlotLib library. The following
values are passed directly to the MatPlotLib library. Please refer to the
`MatPlotLib documentation <https://matplotlib.org/contents.html>`_ for
further information.

Image Size
++++++++++

The `width` and `height` values are passed to matplotlib to specify the size
of the generated image.

The image size defaults to 4 inches wide by 1.25 inches tall.  The default
dpi for MatPlotLib is 100, so this corresponds to 400x125 pixels unless you
have over-ridden the default dpi.

E.g.::

    "legend": {
        "width": 4.5,
        "height": 2.1
    }

strip_location
++++++++++++++

The location of the coloured ramp strip within the legend image can be
customised with the `strip_location` element.  This should be a tuple
of four floats which is passed directly to the MatPlotLib Figure.add_axes
function.

The four floats are expressed as fractions of the width or heigth (i.e.
are numbers between 0.0 and 1.0).  The values are interpreted as follows:
[left, bottom, width, height].

The default value is [ 0.05, 0.5, 0.9, 0.15 ]

E.g.::

    "legend": {
        "strip_location": [ 0.1, 0.4, 0.8, 0.2 ]
    }

MatPlotLib rc params
++++++++++++++++++++

Other MatPlotLib customisations (as they would appear in a .matplotlibrc file)
can be specified with the optional `rcParams` element, defaulting to {}, meaning
the MatPlotLib defaults for all options.

For a full list of possible options refer to
`the MatPlotLib documentation <https://matplotlib.org/stable/tutorials/introductory/customizing.html>`__

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

Colour Ramp Styles support customised non-animated handlers for
`multi-date requests <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html#multi-date>`_
by providing for an aggregator function that converts the multi-date index data
into a dateless index, and apply either the style's colour ramp (i.e. the same
as the single-date case), or a separate colour ramp.

aggregator_function
===================

The `aggregator_function` entry is required for colour ramp style
multi-date handlers.  It is a function defined using OWS's
`function configuration format <https://datacube-ows.readthedocs.io/en/latest/cfg_functions.html>`_.

The function is assumed to take a single xarray Dataset with a time dimension.
The value at each time slice is the output of the `index function <#index-function>`__
at that time.  The function should return an xarray Dataset with no time
dimension, containing the data used as an input to the
`multi-date handler's colour ramp <#multi-date-colour-ramps>`__.

Multi-Date Colour Ramps
=======================

Each multi-date handler has it's own colour ramp.  It may be defined by
any of the `colour ramp definition methods <#colour-ramps>`__ described
above.

Multi-Date Legend
=================

A legend can be automatically generated for a multi-date
handler. The ``legend`` section of a colour ramp style
multi-date handler behaves the same as the single-date
`legend section <#legend-configuration>`__ described above.

feature_info_label
==================

The multi-date aggregator function value will be returned in
multi-date GetFeatureInfo requests for this style, using the
label declared by the ``feature_info_label`` entry.

E.g. ::

    # A simple index delta (difference) multi-date handler
    "multi_date": {
        # Only 2 dates makes sense for delta.
        "allowed_count_range": [2,2],
        # Calculating the difference
        "aggregator_function": {
            "function": "datacube_ows.band_utils.multi_date_delta",
        },
        # The delta colour ramp.
        "mpl_ramp": "RdBu",
        "range": [-1.0, 1.0],
        "legend": {
            # Ticks at -1.0, -0.5, 0.0, 0.5, 1.0
            "begin": "-1.0",
            "end": "1.0",
            "ticks_every": "0.5"
        },
        # The feature info label.
        "feature_info_label": "ndvi_delta",
    }
