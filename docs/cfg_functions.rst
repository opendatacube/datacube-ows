=================
OWS Configuration
=================

.. contents:: Table of Contents

--------------------------
Functions in Configuration
--------------------------

Several entries in the OWS configuration allow to specify
behaviour in an arbitrary way by specifying a Python function
that may be written by the user.  All these functions can be
specified using either the `simple <#simple>`_ or
`advanced <#advanced>`_ formats described below.

Simple
======

Simply provide the fully qualified path to the function as
a string.  Note that if you use your own custom function it
is your responsibility to ensure it is in the python path of
the execution environment.

The configured function must take the arguments expected by
the configuration system for that entry.

E.g.

::

    "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val"

Advanced
========

More detailed control over the calling of the function is possible
using a function section.  Function sections MUST contain
a "function" entry which works the same as the simple format
described above.

E.g. This is equivalent to the simple format example above:

::

    "extent_mask_func": {
        "function": "datacube_ows.ogc_utils.mask_by_val"
    }

All other entries are optional and allow other arguments to
be passed to the function in addition to the ones documented
as expected for that entry.

Passing Additional Arguments
----------------------------

You may want to pass additional arguments to the
function than those are explicitly used by that
configuration entry.

For example you may want to used one generic function
for multiple layers or styles, but tweak its behaviour
for some layers/styles by passing optional arguments
to the function.

This technique is particularly useful for
`style index functions <https://datacube-ows.readthedocs.io/en/latest/cfg_colourramp_styles.html#index-function>`__
and `component callback functions <https://datacube-ows.readthedocs.io/en/latest/cfg_component_styles.html#callback-function-components>`_,
but will work for any function in the configuration format.

args and kwargs
+++++++++++++++

The "args" and "kwargs" entries allow the configuration files
to pass constant values to additional positional and keyword
arguments of the function in the standard python manner.

pass_product_cfg
++++++++++++++++

A common use case passing band names to generic band-math
functions for
`component callback functions <https://datacube-ows.readthedocs.io/en/latest/cfg_component_styles.html#callback-function-components>`_
and
`style index functions <https://datacube-ows.readthedocs.io/en/latest/cfg_colourramp_styles.html#index-function>`__.
In order for this to work with
`band aliases <https://datacube-ows.readthedocs.io/en/latest/cfg_layers.html#band-dictionary-bands>`_,
it it necessary for the function
to have access to the band alias dictionary to convert aliases
to native band names.  This can be accomplished with the
"pass_product_cfg" entry, which causes the OWSLayer configuration
object for the layer to be passed to the function as an
additional keyword argument "product_cfg".  Refer to the
source code for the band_utils functions discussed below
for examples.

band_utils functions
++++++++++++++++++++

Several general purpose functions are provided in
`datacube_ows.band_utils` allow you to perform common
band calculations without defining your own python
functions.

Most take the names (or aliases) of the bands they are
to operate on as keyword arguments.  If you use aliases you
must set `pass_product_cfg <#pass-product-cfg>` to
True.

datacube_ows.band_utils.sum_bands
    Sums two bands, passed as keyword arguments "band1" and "band2".

datacube_ows.band_utils.delta_bands
    Sums two bands, passed as keyword arguments "band1" and "band2".

    (band2 is subtracted from band1.  i.e. band1 - band2)

datacube_ows.band_utils.norm_diff
    Calculates the normalised difference of two bands, passed
    as keyword arguments "band1" and "band2".

    Also has a "scale_from" argument allowing it to be used in
    component callback function.

datacube_ows.band_utils.single_band
    Returns the raw value of a band as an index datasets. Takes
    keyword argument "band".

datacube_ows.band_utils.constant
    Returns a constant.  Still needs a band (takes a band, multiplies
    by zero and adds the constant), but it can be any band.  Arguments
    are "band" and "const".

datacube_ows.band_utils.band_quotient
    Divides two bands, passed as keyword arguments "band1" and "band2".

    (band1 is divided by from band2)

datacube_ows.band_utils.band_quotient_sum
    Takes 4 bands, divides and adds them as follows:

    (band1a / band1b) + (band2a / band2b)

E.g. This is an index function that will compute NDVI on any
layer that has both an "nir" and "red" band name or alias
in the band dictionary:

::

    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "pass_product_cfg": True,
        "kwargs": {
            "band1": "nir",
            "band2": "red"
        }
    }

And this is a component callback function that uses NDVI
scaled from -0.1 to 1.0 in the red channel:

::

    "components": {
        "red": {
            "function": "datacube_ows.band_utils.norm_diff",
            "pass_product_cfg": True,
            "kwargs": {
                "band1": "nir",
                "band2": "red",
                "scale_from": [-0.1, 1.0]
            }
        },
        ...


Direct insertion of callables not supported
===========================================

In previous versions it was possible to specify functions directly,
either by importing a callable object into the configuration file and
referencing it directly, or with a lambda.  These methods are no
longer supported to ensure that configuration objects are always
serialisable and that the json and python configuration formats
are equivalent.

