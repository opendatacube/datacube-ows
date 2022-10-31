=============================
OWS Configuration - Functions
=============================

.. contents:: Table of Contents

--------------------------
Functions in Configuration
--------------------------

Several entries in the OWS configuration allow to specify
behaviour in an arbitrary way by specifying a Python function
that may be written by the user.  All these functions can be
specified using either the `simple <#simple-function-format>`_ or
`advanced <#advanced-function-format>`_ function formats described below.

Simple Function Format
======================

Simply provide the fully qualified path to the function as
a string.  Note that if you use your own custom function it
is your responsibility to ensure it is in the python path of
the execution environment.

The configured function must take the arguments expected by
the configuration system for that entry.

E.g.

::

    "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val"

Advanced Function Format
========================

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

mapped_bands
++++++++++++

A common use case is passing band names to generic band-math
functions for
`component callback functions <https://datacube-ows.readthedocs.io/en/latest/cfg_component_styles.html#callback-function-components>`_
and
`style index functions <https://datacube-ows.readthedocs.io/en/latest/cfg_colourramp_styles.html#index-function>`__.
In order for this to work with
`band aliases <https://datacube-ows.readthedocs.io/en/latest/cfg_layers.html#bands-dictionary-bands>`_,
it it necessary for the function
to have access to the band alias dictionary to convert aliases
to native band names.  This can be accomplished with the
"mapped_bands" entry, which causes a function that maps
band aliases to native band names the layer to be passed
to the function as an additional keyword argument "band_mapper".

Refer to the source code for the band_utils functions discussed below
for examples.

band_utils functions
++++++++++++++++++++

Several general purpose functions are provided in
`datacube_ows.band_utils` allow you to perform common
band calculations without defining your own python
functions.

Most take the names (or aliases) of the bands they are
to operate on as keyword arguments.  If you use aliases you
must set `mapped_bands <#mapped-bands>` to
True.

1. datacube_ows.band_utils.sum_bands
    Sums two bands, passed as keyword arguments "band1" and "band2".

#. datacube_ows.band_utils.delta_bands
    Subtracts a band from another, passed as keyword arguments "band1" and "band2".

    (band2 is subtracted from band1.  i.e. band1 - band2)

#. datacube_ows.band_utils.norm_diff
    Calculates the normalised difference of two bands, passed
    as keyword arguments "band1" and "band2".

    `Scalable <#scaleable-band-utilities>`_.

#. datacube_ows.band_utils.pre_scaled_band
    Pre-scale a band with a scale factor and offset.

    (The scaling function is ``data[band] * scale + offset``)

#. datacube_ows.band_utils.pre_scaled_sum_bands
    Sums two bands after pre-scaling them, each with a scale factor and offset. The
    keyword arguments are "band1" and "band2", along with the corresponding "scale1",
    "offset1" and "scale2", "offset2".

#. datacube_ows.band_utils.delta_bands
    Subtracts a band from another, after pre-scaling them, each with a scale factor and
    offset. The keyword arguments are "band1" and "band2", along with the corresponding
    "scale1", "offset1" and "scale2", "offset2".

    (band2 is subtracted from band1.  i.e. band1 - band2)

#. datacube_ows.band_utils.pre_scaled_norm_diff
    Calculates the normalised difference of two bands, after pre-scaling them, each with
    a scale factor and offset. The keyword arguments are "band1" and "band2", along with
    the corresponding "scale1", "offset1" and "scale2", "offset2".

    `Scalable <#scaleable-band-utilities>`_.

#. datacube_ows.band_utils.single_band
    Returns the raw value of a band as an index datasets. Takes
    keyword argument "band".

    `Scalable <#scaleable-band-utilities>`_.

#. datacube_ows.band_utils.constant
    Returns a constant.  Still needs a band (takes a band, multiplies
    by zero and adds the constant), but it can be any band.  Arguments
    are "band" and "const".

    `Scalable <#scaleable-band-utilities>`_.

#. datacube_ows.band_utils.band_quotient
    Divides two bands, passed as keyword arguments "band1" and "band2".

    (band1 is divided by from band2)

    `Scalable <#scaleable-band-utilities>`_.

#. datacube_ows.band_utils.band_quotient_sum
    Takes 4 bands, divides and adds them as follows:

    (band1a / band1b) + (band2a / band2b)

    `Scalable <#scaleable-band-utilities>`_.

#. datacube_ows.band_utils.single_band_arcsec
    Takes one band, and returns the arcsec of that band.

    `Scalable <#scaleable-band-utilities>`_. `Band Modulator <#band-modulators>`_.

#. datacube_ows.band_utils.single_band_offset_log
    Takes a single band and an optional offset, and an optional scale.

    Returns:

        log( ( band * scale ) + offset )

    The scale and offset both default to 1.0.  If offset is not supplied
    the more efficient log1p function is used.

    `Scalable <#scaleable-band-utilities>`_. `Band Modulator <#band-modulators>`_.

E.g. This is an index function that will compute NDVI on any
layer that has both an "nir" and "red" band name or alias
in the band dictionary:

::

    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "mapped_bands": True,
        "kwargs": {
            "band1": "nir",
            "band2": "red"
        }
    }

This can also be computed for bands that need scaling, e.g., for Landsat 8 C2 L2 SR:

::

    "index_function": {
        "function": "datacube_ows.band_utils.pre_scaled_norm_diff",
        "mapped_bands": True,
        "kwargs": {
            "band1": "nir08",
            "band2": "red",
            "scale1": 0.0000275,
            "offset1": -0.2,
            "scale2": 0.0000275,
            "offset2": -0.2,
        }
    }

Scalable band utilities
@@@@@@@@@@@@@@@@@@@@@@@

Many band utilities are noted in the list above as "scalable".  This means
that they can take two additional optional parameters: ``scale_from`` and ``scale_to``,
which may each be set to a tuple of two floating point numbers.

After the underlying utility function is called, the output is linearly scaled with ``scale_from``
and ``scale_to`` providing the input and output ranges. i.e. given:

::

    "scale_from": [0.0, 1.0],
    "scale_to": [-2500.0, 2500.0],

A raw result from the utility of 0.0 will be scaled to -2500 and a raw result of 1.0 will be
scaled to +2500. A raw result of 0.5 (exactly half between 0 and 1) will be scaled to 0 (exactly
half way between -2500 and +2500), and so on.

No scaling is performed if ``scale_from`` is not set.  ``scale_to`` defaults to [0,255] (i.e.
suitable for use in per-rgb-component indexes.

And this is a component callback function that uses NDVI
scaled from -0.1 to 1.0 in the red channel:

::

    "components": {
        "red": {
            "function": "datacube_ows.band_utils.norm_diff",
            "mapped_bands": True,
            "kwargs": {
                "band1": "nir",
                "band2": "red",
                "scale_from": [-0.1, 1.0]
            }
        },
        ...

Band Modulators
@@@@@@@@@@@@@@@

Some band utilities are noted in the list above as being "band modulators".  This means
that they can take an additional optional ``mult_band`` value.

The value passed to  ``mult_band`` must be an available band (or band alias if ``mapped_bands``
is True.)  If set, the value of the band function (after scaling) is multiplied by the raw value
of mult_band for the final result.  With appropriate use of scaling, this can be used to allow
a function to be used as a "dimmer" for a data band.

E.g. Using arcsec of the sdev band as a local brightness control for an rgb image.
The raw red,green,blue bands go to 3000.

::
    "components": {
        "red": {
            "function": "datacube_ows.band_utils.single_band_arcsec",
            "mapped_bands": True,
            "kwargs": {
                "band": "sdev",
                "mult_band": "red",
                "scale_from": [0.02, 0.18],
                "scale_to": [0.0, 255.0/3000.0],
            },
        },
        "green": {
            "function": "datacube_ows.band_utils.single_band_arcsec",
            "mapped_bands": True,
            "kwargs": {
                "band": "sdev",
                "mult_band": "green",
                "scale_from": [0.02, 0.18],
                "scale_to": [0.0, 255.0/3000.0],
            },
        },
        "blue": {
            "function": "datacube_ows.band_utils.single_band_arcsec",
            "mapped_bands": True,
            "kwargs": {
                "band": "sdev",
                "mult_band": "blue",
                "scale_from": [0.02, 0.18],
                "scale_to": [0.0, 255.0/3000.0],
            },
        },



Direct insertion of callables not supported
===========================================

In previous versions it was possible to specify functions directly,
either by importing a callable object into the configuration file and
referencing it directly, or with a lambda.  These methods are no
longer supported to ensure that configuration objects are always
serialisable and that the json and python configuration formats
are equivalent.
