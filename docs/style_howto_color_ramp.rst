===========================================
OWS Stying HOW-TO Guide: Colour Ramp Styles
===========================================

.. contents:: Table of Contents

Colour Ramps
------------

A single continuous index is usually best visualised with a Colour Ramp.  We looked at
some unusual visualisations of NDVI (normalised
difference vegetation index) in the last chapter, but a more traditional approach
might look something like this:

Example: Bidirectional NDVI
+++++++++++++++++++++++++++

::

    ndvi_bidirection_cfg = {
        "index_function": {
            "function": "datacube_ows.band_utils.norm_diff",
            "mapped_bands": True,
            "kwargs": {"band1": "nir", "band2": "red"},
        },
        "mpl_range": "RdYlGn",
        "range": [-1.0, 1.0]
    }

Here we applied a MatPlotLib named colour ramp "RdYlGn".  This is a diverging colour ramp
stretching from red through yellow to green, with the central yellow region being the brightest.
The ramp is applied linearly over the ``range`` -1 to 1.
For us this means that areas with negative NDVI will be red, positive areas green and areas close
to zero will be yellow.

The full list of matplotlib named colour ramps can be found in the
`Matplotlib documentation <https://matplotlib.org/2.0.2/examples/color/colormaps_reference.html>`_.
(Note that you can reverse the order of any ramp by adding the suffix ``_r``. E.g. "RdYlGn_r" is the
same as "RdYlGn" except green is the low end of the scale and red the high end.)

.. image https://user-images.githubusercontent.com/4548530/112426051-591d6000-8d8b-11eb-9673-c3efd4463353.png
    :width: 600

`View full size
<https://user-images.githubusercontent.com/4548530/112426051-591d6000-8d8b-11eb-9673-c3efd4463353.png>`_

Example: Unidirectional NDVI
++++++++++++++++++++++++++++

Let's make a few changes based on what we know so far. We shall:

1. Choose a new Matplotlib colour ramp.
1. Reverse the order of the Matplotlib ramp with the ``_r`` suffix.
2. Change the range to [0, 1.0]

The Matplotlib ``ocean`` ramp runs from dark green to dark blue, then fading to white.
so ``ocean_r`` is the reverse - from bright yellow to dark green.
So now we get white in the negative and zero areas, with positive areas
getting darkening blues with close to 1.0 being dark green.

::

    ndvi_unidirection_cfg = {
        "index_function": {
            "function": "datacube_ows.band_utils.norm_diff",
            "mapped_bands": True,
            "kwargs": {"band1": "nir", "band2": "red"},
        },
        "mpl_range": "ocean_r",
        "range": [0.0, 1.0]
    }

.. image https://user-images.githubusercontent.com/4548530/112567708-6e4ec900-8e35-11eb-8c75-a6a1f35ef665.png
    :width: 600

`View full size
<https://user-images.githubusercontent.com/4548530/112567708-6e4ec900-8e35-11eb-8c75-a6a1f35ef665.png>`_

