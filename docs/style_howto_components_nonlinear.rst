=================================================
OWS Styling HOW-TO Guide: Components (non-linear)
=================================================

.. contents:: Table of Contents


Non-Linear Components: Functions
--------------------------------

All the examples in the
`previous section <https://datacube-ows.readthedocs.io/en/latest/style_howto_components.html>`_
involved using linearly scaled, linear combinations of bands to calculate channel values.
If we want to evaluate components using more sophisticated calculations, we need to use
python functions.

Again we will start from the base of a simple rgb image:

::

    rgb_cfg = {
        "components": {
            "red": {"red": 1.0},
            "green": {"green": 1.0},
            "blue": {"blue": 1.0},
        },
        "scale_range": (50, 3000),
    }

Example: red-ndvi-blue (full scale)
+++++++++++++++++++++++++++++++++++

Let's say we want the green channel of the output image to encode NDVI instead
of the Landsat green band.

First we need to define our function.   The Styling API will call this function with
the same `xarray.Dataset` that you pass to `apply_ows_style_cfg`.  It should
return an `xarray.DataArray` with the same spatial dimensions and coordinates,
as the input argument.

The returned array is converted to `uint8` in the xarray image returned by
the API.  This means it is up to your function to handle scaling to the (0,255) range.
For example, given this function, containing a simple unscaled implementation of NDVI:

::

    def ndvi(data):
        # Returns data in range (-1, 1)
        return (data["nir"] - data["red"]) / (data["nir"] + data["red"])


Using ``"green": ndvi,`` in the components dictionary would sort of work, but would
return 0 for every pixel after conversion from floating point - which is probably
not what we want. We can add scaling like this:

::

    def ndvi(data):
        # Calculate NDVI (-1.0 to 1.0)
        unscaled = (data["nir"] - data["red"])/(data["nir"] + data["red"])

        # Scale to [-1.0 - 1.0] to [0 - 255]
        scaled = ((unscaled + 1.0) * 255/2).clip(0, 255)

        return scaled

    r_ndvi_b_fullrange_cfg = {
        "components": {
            "red": {"red": 1.0},
            "green": ndvi,
            "blue": {"blue": 1.0},
        },
        "scale_range": (50, 3000),
    }

The ``scale_range`` only applies to the linearly defined channels, red and blue.  The ``ndvi`` function
is responsible for scaling of the green channel.

Note that this example is for illustrative purposes only - there is a much easier way to implement
scaling, discussed later in this chapter.

.. image:: https://user-images.githubusercontent.com/4548530/112403696-00d26800-8d63-11eb-9d16-405b7b972e08.png
    :width: 600

`View full size
<https://user-images.githubusercontent.com/4548530/112403696-00d26800-8d63-11eb-9d16-405b7b972e08.png>`_

Meh, it's *very* green, and kind of saturated.  This is because we are
scaling (-1, +1) to (0, 255) and negative values of NDVI
aren't very interesting.  What we really want is clip (-1,0) to 0 and scale
(0, +1) to (0,255).

But scaling is handled by the function now.  We don't want to have to redefine a function every
time we tweak the scaling.  The API has a solution to this common problem.

Non-Linear Components: OWS Function Syntax and Scalable
-------------------------------------------------------

You can use the ``@scalable`` decorator provided by the API, and OWS's
`extended function syntax <https://datacube-ows.readthedocs.io/en/latest/cfg_functions.html>`_
for a more streamlined solution to scaling:

Example: red-ndvi-blue (half scale)
+++++++++++++++++++++++++++++++++++

::

    from datacube_ows.styles.api import scalable

    @scalable
    def scaled_ndvi(data):
        # Calculate NDVI (-1.0 to 1.0)
        return (data["nir"] - data["red"])/(data["nir"] + data["red"])

    r_ndvi_b_halfrange_cfg = {
        "components": {
            "red": {"red": 1.0},
            "green": {
                "function": scaled_ndvi,
                # In addition to the standard API calling argument (the input data),
                # additional positional or keyword arguments can
                # be passed to the function using an args array and/or a kwargs dictionary.
                "kwargs": {
                    "scale_from": (0.0, 1.0),
                    "scale_to": (0, 255)
                }
            },
            "blue": {"blue": 1.0},
        },
        "scale_range": (50, 3000),
    }

The ``@scalable`` decorator adds ``scale_from`` and ``scale_to`` arguments to the function,
and applies the relevant scaling to the output. Values outside the "scale_from" range are
clipped to the minimum or maximum "scale_to" value.

.. image:: https://user-images.githubusercontent.com/4548530/112408715-67a84f00-8d6c-11eb-82de-8c19b086cde2.png
    :width: 600

`View full size
<https://user-images.githubusercontent.com/4548530/112408715-67a84f00-8d6c-11eb-82de-8c19b086cde2.png>`_

Non-Linear Components: OWS Function Syntax and Scalable
-------------------------------------------------------

Datacube OWS defines a wide range of utility functions in `datacube_ows.band_utils`.  In fact, you
can implement the style above using the supplied normalised difference function ``norm_diff``, all you
have to do is pass in the band names.

A list of available band utility functions can be found
`in the documentation <https://datacube-ows.readthedocs.io/en/latest/cfg_functions.html#band-utils-functions>`_.

Example: red-ndvi-blue (half scale)
+++++++++++++++++++++++++++++++++++

Here's an extended example that replaces Green with NDVI and Blue with NDWI:


::

    r_ndvi_ndwi_halfrange_cfg = {
        "components": {
            "red": {"red": 1.0},
            "green": {
                "function": "datacube_ows.band_utils.norm_diff",
                "kwargs": {
                    "band1": "nir",
                    "band2": "red",
                    "scale_from": (0.0, 1.0),
                    "scale_to": (0, 255)
                }
            },
            "blue": {
                "function": "datacube_ows.band_utils.norm_diff",
                "kwargs": {
                    "band1": "green",
                    "band2": "nir",
                    "scale_from": (0.0, 1.0),
                    "scale_to": (0, 255)
                }
            },
        },
        "scale_range": (50, 3000),
    }

Note that utility functions are referenced by name, rather than importing the name and inserting directly.

.. image:: https://user-images.githubusercontent.com/4548530/112410722-c6bb9300-8d6f-11eb-944f-ce283e922075.png
    :width: 600

`View full size
<https://user-images.githubusercontent.com/4548530/112410722-c6bb9300-8d6f-11eb-944f-ce283e922075.png>`_

`Next up
<https://datacube-ows.readthedocs.io/en/latest/style_howto_colour_ramp.html>`_
we will look at colour ramp styles.
