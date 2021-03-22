==============================
OWS Configuration - Components
==============================

.. contents:: Table of Contents

Component Styles
----------------

Component Styles are `styles <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html>`_ where
each component channel of the image (red, green, blue and optionally
alpha) is calculated independently from the data for that pixel.

Component styles support the
`elements common to all styles <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html#common-elements>`_.

There are three additional settings specific to component styles:
`scale_range <#style-scale-range>`, `components <#components>`
and `additional_bands <#additional-bands-additional-bands>`_.

Component styles do NOT support automatic legend generation. If you
want a legend you must provide an external
`url <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html#url>`__ to a pre-prepared image.

----------
components
----------

The components section contains one component definition per
component channel of the output image::

  * "red" (required)
  * "green" (required)
  * "blue" (required)
  * "alpha" (optional)

Alpha is the opacity of each pixel.  When alpha is 0 the image pixel is
fully transparent, when 255 fully opaque.  If not provided, the alpha channel
is assumed to be always fully opaque (unless otherwise masked, e.g. by
the `extent mask <https://datacube-ows.readthedocs.io/en/latest/cfg_layers.html#extent-mask-function-extent-mask-func>`_
or `style masking <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html#bit-flag-masks-pq-masks>`_).

Calculating the value for each pixel has two steps:

1. Calculate an unscaled channel value.

   Each component definition defines either a
   `linear combination of raw channel data <#linear-combination-components>`_
   or a
   `callback function <#callback-function-components>`_
   (as discussed in detail below) to determine the unscaled value
   for that channel for each pixel.

2. Scale the unscaled value to unsigned 8-bit value (0-255).

   This is defined by the `scale_range <#component-scale-range>`_
   entry for the channel if it exists, or the style-wide
   `scale_range <#style-scale-range>`__.


Linear Combination Components
+++++++++++++++++++++++++++++

In a linear combination component, every entry (apart from
`scale_range <#component-scale-range>`__) maps a band name or
alias from the `band dictionary <https://datacube-ows.readthedocs.io/en/latest/cfg_layers.html#bands-dictionary-bands>`_
to a floating point multiplier.  The pixel data values from these bands
are then multiplied by these multipliers and summed to produce the
unscaled channel value.

The unscaled channel value is then scaled to the
to an unsigned 8-bit value (0-255) according to
the  `scale_range <#component-scale-range>`__
entry for the channel if it exists, or the style-wide
`scale_range <#style-scale-range>`__.

Component scale_range
@@@@@@@@@@@@@@@@@@@@@

Defines the raw band value range that will be compressed
to an 8 bit range for the output image.  Band values outside
this range are clipped to 0 or 255.

The component scale_range is optional and if not present defaults
to the `style-side scale_range <#style-scale-range>`_.

E.g.::

    # raw values less than 15 are clipped to 0 and raw values greater than 3100
    # are clipped to 255.  Raw values from 15 to 3100 are linearly scaled to the
    # 8 bit range 0 to 255.

    "scale_range": [15, 3100],

Linear Combination Examples
@@@@@@@@@@@@@@@@@@@@@@@@@@@

::

   # Example 1.  Data is a single band called "data" with
   # most pixel values falling between 50 and 3000.
   # (Uses a style-wide scale_range).

   "components": {
       "red": {
            "data": 1.0
       },
       "green": {
            "data": 1.0
       },
       "blue": {
            "data": 1.0
       },
   },
   "scale_range": (50, 3000),

::

   # Example 2.  Real colour representation of red, green and blue
   # channels.  Separate scale_ranges defined per channel.
   "components": {
       "red": {
            "red": 1.0,
            "scale_range": (20, 2800)
       },
       "green": {
            "green": 1.0,
            "scale_range": (30, 3000)
       },
       "blue": {
            "blue": 1.0,
            "scale_range": (25, 2450)
       },
   },

::

    # Example 3. False colour image combining red, green, blue, and
    # near and shortwave infrared bands
    "components": {
       "red": {
            # red channel comprises 30% swir2 band, 30% swir1 and 40% nir
            # Uses a component scale range
            "swir2": 0.3,
            "swir1": 0.3,
            "nir": 0.4,
            "scale_range": (50, 3400)
       },
       "green": {
            # green channel comprises 20% nir, 40% red and 40% green bands
            # Uses the default style-wide scale_range.
            "nir": 0.2,
            "red": 0.4,
            "green": 0.4,
       },
       "blue": {
            # green channel comprises 20% green, 80% blue bands
            # Uses the default style-wide scale_range.
            "green": 0.2,
            "blue": 0.8,
       },
    },
    # The default style-wide scale_range, used by the green and blue
    # channels in this example.
    "scale_range": (30, 3000)

::

    # Example 4: Alpha channel.
    # Data consists of a bands: "population_density", "vegetation" and
    # "urban". This style displays pure vegetation as green, and urban
    # land as red with combinations as various shades of yellow (green + red).
    # In addition, the style will have opacity according to population
    # density, so that densely populated pixels are opaque and sparsely
    # populated pixels are more transparent.
    "channels": {
        "red": {
            "urban": 1.0,
            "scale_range": (0, 500),
        },
        "green": {
            "vegetation": 1.0,
            "scale_range": (0, 500),
        },
        "blue": {
            # Blue channel not used - always zero.
        },
        "alpha": {
            "population_density": 1.0,
            "scale_range": (4, 500)
        }
    }

Band Names That Are Reserved Words
@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@

If you are unfortunate enough to have raw data with a band named "scale_range"
(or "function" which would cause the component to be treated as a
`callback function component <#callback-function-components>`_), you can
still access it here by defining an alias for the band in the
`band dictionary <https://datacube-ows.readthedocs.io/en/latest/cfg_layers.html#bands-dictionary-bands>`_.

E.g.::

    "bands": {
        "red": [],
        "scale_range": ["scale_rng"],
        "function": ["func"]
    }
    ...
        "components": {
            "red": {
                "red": 1.0
            },
            "green": {
                # Cannot use "scale_range" to refer to band, so
                # use alias.
                "scale_rng": 1.0
            },
            "blue": {
                # Cannot use "function" to refer to band, so
                # use alias.
                "func": 1.0
            },
        }

Callback Function Components
+++++++++++++++++++++++++++++

In a callback function component, the user declares a callback function
using OWS's `function configuration format <https://datacube-ows.readthedocs.io/en/latest/cfg_functions.html>`_.

The function must take an xarray Dataset containing the raw band data
and return a xarray DataArray containing the channel data.  It is
the responsibility to scale it's output to the range 0-255.

The bands needed for callback function components cannot always be
determined directly from the component definition, so if any component
in the style is a callback function component, you should ensure all
needed bands are retrieved by
using the `additional_bands <#additional-bands>`__ config item if necessary.

E.g.::

    "components": {
        "red": {
            # Red channel is red/blue normalised difference (Ferric Iron index)
            "function": "datacube_ows.band_utils.norm_diff",
            "pass_product_cfg": True,
            "kwargs": {
                "band1": "red",
                "band2": "blue",
                "scale_from": [-0.1, 1.0],
            }
        },
        "green": {
            # Green channel is nir/swir1 normalised difference (Bare Soil index)
            "function": "datacube_ows.band_utils.norm_diff",
            "pass_product_cfg": True,
            "kwargs": {
                "band1": "nir",
                "band2": "swir1",
                "scale_from": [-0.1, 1.0],
            }
        },
        "blue": {
            # Blue channel is swir1/swir2 normalised difference (Clay/Mica index)
            "function": "datacube_ows.band_utils.norm_diff",
            "pass_product_cfg": True,
            "kwargs": {
                "band1": "swir1",
                "band2": "swir2",
                "scale_from": [-0.1, 1.0],
            }
        },
        "additional_bands": [ "red", "blue", "nir", "swir1", "swir2" ]
    },

-----------------------------------
Additional Bands (additional_bands)
-----------------------------------

The bands needed for a linear combination component can be trivially
determined from the component definition.  This is not the case for callback
function components, so if any component in the style is a callback
function component, (and if any bands needed by the callback function
component(s) are not already being used by any lineat combination
components), then these additional required bands must be declared
with the `additional_bands` list.

The `additional_bands` should be a list of band names or aliases from
the `band dictionary <https://datacube-ows.readthedocs.io/en/latest/cfg_layers.html#bands-dictionary-bands>`__.  It is
optional (defaults to an empty list).  It is safe (but not
necessary) to declare bands in `additional_bands` that are used
directly by a linear combination component in the style.

E.g.::

    "components": {
        "red": {
            # Red channel is red/blue normalised difference (Ferric Iron index)
            "function": "datacube_ows.band_utils.norm_diff",
            "pass_product_cfg": True,
            "kwargs": {
                "band1": "red",
                "band2": "blue",
                "scale_from": [-0.1, 1.0],
            }
        },
        "green": {
            "green": 1.0
        },
        "blue": {
            "blue": 1.0
        },
    },
    "additional_bands": [
            # The "Red" band must be declared in the additional bands or the
            # the Ferric Iron Index will not be able to be calculated.
            "red",
            # The "Blue" band is already used by the linear combination
            # for the blue channel, so it could be left out, but it is
            # safe to include.
            "blue"
    ]

-----------------
Style scale_range
-----------------

Defines the raw band value range that will be compressed
to an 8 bit range for the output image.  Band values outside
this range are clipped to 0 or 255.

The style-level scale_range applies to all linear combination
component channels that do not set their own component-level
scale_range.

The style-level scale_range is required unless all component
channels satisfy the exceptions above.

See the `component scale_range <#component-scale-range>`_
section for examples.
