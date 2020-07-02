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

---------------------------
Calculating the Index Value
---------------------------

The `index_function <#index-function>`__ entry defines how the
index is calculated at each pixel.  The bands needed for the calculation
must be declared in the `needed_bands list <needed-bands-list>`__
entry.

index_function
++++++++++++++

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

TODO

--------------------
Legend Configuration
--------------------

TODO