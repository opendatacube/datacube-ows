=================================
OWS Configuration - Hybrid Styles
=================================

.. contents:: Table of Contents

Hybrid Styles
-------------

Hybrid styles are an experimental type of `style <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html>`_ that
return a linear combination of a component style and a colour ramp style.

This can allow for a more easily visually interpreted image, but
there are usually better ways to achieve the same effect on the
client side.

Hybrid styles support most [*]_ elements supported by either
`component styles <https://datacube-ows.readthedocs.io/en/latest/cfg_component_styles.html>`_ or
`colour ramp styles <https://datacube-ows.readthedocs.io/en/latest/cfg_colourramp_styles.html>`_ and
define two indepenent styles (one of each type) that
are then blended according to the required `component_ratio` entry.

If `component_ratio` should be a float between 0.0 and 1.0.  A value
of '0.0' means 100% colour ramp style, '1.0' means 100% component style
and a value of '0.5' means a 50/50 blend of the two, etc.

.. [*] Hybrid Styles do NOT support auto-legend generation. All other features
       of component and colour-ramp styles are supported.

E.g.::

    "legend": {
        # Common stuff
        "name": "rgb_ndvi",
        "title": "NDVI plus RGB",
        "abstract": "NDVI combined with RGB for terrain detail",

        # Component Style
        "components": {
            "red": {
                "red": 1.0
            },
            "green": {
                "green": 1.0
            },
            "blue": {
                "blue": 1.0
            }
        },
        "scale_range": [0.0, 3000.0]

        # Colour-Ramp Style
        "index_function": {
            "function": "datacube_ows.band_utils.norm_diff",
            "pass_product_cfg": True,
            "kwargs": {
                "band1": "nir",
                "band2": "red"
            }
        },
        "range": [0.0, 1.0],
        "mpl_ramp": "RdBu",

        #  Does not need to include "green" and "blue".
        # (But no harm in adding them explicitly either.)
        "needed_bands": ["red", "nir"],

        # Blend 60% RGB + 40% ndvi
        "component_ration": 0.6,
    }
