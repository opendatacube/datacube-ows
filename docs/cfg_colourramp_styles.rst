=================
OWS Configuration
=================

.. contents:: Table of Contents


Colour-Ramp Styles
------------------

Colour-ramp Styles are `styles <cfg_styling.rst>`_ where
a single continuous index value is calculated from the raw data for
each pixel, and that index value is mapped to a graduated colour ramp
for display.

Colour-ramp styles support the
`elements common to all styles <cfg_styling.rst#common-elements>`_.

Colour-ramp styles support automatic legend generation. Specialised
legend configuration is described `below <#legend-configuration>`__.

Note on spelling: I am Australian and spell it "colour".  Most software
packages use the US spelling "color".  Within the configuration file
format we use the software conventional spelling, but within the text
of this documentation, I use the UK/Australian spelling.


---------------------------
Calculating the Index Value
---------------------------

The `index_function <#index-function>`__ entry defines how the
index is calculated at each pixel.  The bands needed for the calculation
must be declared in the `needed_bands list <needed-bands-list>`__
entry.

index_function
==============

The `index_function` allows the user to declare a callback function
to calculate the index value using OWS's
`function configuration format <cfg_functions.rst>`_.
The function is expected to take an xarray Dataset containing all the
bands in the `needed_bands list <needed-bands-list>`__ (plus any additional
arguments handled by the
`function configuration format <cfg_functions.rst>`_); and returns
an xarray Dataset containing the index value.

A `small library <cfg_functions.rst#band-utils-functions>`_
of general purpose band math functions
are provided in `datacube_ows.band_utils`.

needed_bands list
=================

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

   To use a MatPlotLib colouor ramp, use the `mpl_ramp <#mpl-ramp>`__
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
entry.  `color_ramp` should be a list of `colour point definitions <#colour-point-definitions>`_.
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

Colour Point Definitions
++++++++++++++++++++++++

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
            "colour": "#000",
            "alpha": 0.0
        },
        {
            "value": 0.0,
            "colour": "#000",
        },
        {
            "value": 1.0,
            "colour": "#F00",
        },
        {
            "value": 10.0,
            "colour": "#00F",
        }
     ],

--------------------
Legend Configuration
--------------------

Colour-ramp styles support automatic legend generation.
