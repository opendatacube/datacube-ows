=================
OWS Configuration
=================

.. contents:: Table of Contents

Functions in Configuration
--------------------------

Several entries in the OWS configuration allow to specify
behaviour in an arbitrary way by specifying a Python function
that may be written by the user.  All these functions can be
specified using either the `simple <#simple>`_ or
`advanced <#advanced>`_ formats described below.

Simple
++++++

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
++++++++

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
as expected for that entry.  These are particularly used
for style index_functions, but will work for any function
in the configuration format.

The "args" and "kwargs" entries allow the configuration files
to pass constant values to additional positional and keyword
arguments of the function in the standard python manner.

One of the main use cases for this is passing band names to
style index functions.  In order for this to work with
`band aliases <cfg_layers.rst#band-dictionary-bands>`_ however,
it it necessary for the function
to have access to the band alias dictionary to convert aliases
to native band names.  This can be accomplished with the
"pass_product_cfg" entry, which causes the OWSLayer configuration
object for the layer to be passed to the function as an
additional keyword argument "product_cfg".  For examples
of how to use this see the functions in the ``datacube_ows.band_utils``
module.

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

Direct insertion of callables not supported
+++++++++++++++++++++++++++++++++++++++++++

In previous versions it was possible to specify functions directly,
either by importing a callable object into the configuration file and
referencing it directly, or with a lambda.  These methods are no
longer supported to ensure that configuration objects are always
serialisable and that the json and python configuration formats
are equivalent.

