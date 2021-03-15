==========================================
OWS Configuration - OWS Styling Python API
==========================================

.. contents:: Table of Contents

Motivation
----------

OWS configuration is complex, and for large deployments there can be friction between the needs and
interests of the Dev Ops engineers responsible for the configuration as a whole, and the scientific
staff responsible for individual products/layers within that configuration.

The OWS Styling Python API is intended to allow product owners who intimately familiar with their
product and experienced with using the Open Datacube in a scientific programming environment to
experiment with OWS styling, and to prototype and rapidly iterate new styles and improve existing
ones.

Stand-Alone Style Objects
-------------------------

The OWS Styling API introduces the concept of stand-alone style objects, which are constructed from
a standard OWS configuration
`style definition <https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html#style-definitions>`_
dictionary.

All style definition elements and features that are relevant to rendering an image are supported.
The differences between stand-alone styles and true OWS styles are:

1. "name", "title" and "abstract" are optional.

   As Style objects are stand-alone they do not require metadata, or a unique identifier.

2. Style inheritance cannot be used.

   Style inheritance depends on the context of the enclosing complete OWS Configuration and
   so is not available for stand-alone styles.

3. The various band-aliasing techniques are not available.

    It is up to the the user of the API to ensure the band names in the style definition exactly
    match the data variable names in the XArray Dataset being styled.

4. Function objects/callables can be used directly in stand-alone style definitions.

    Full OWS Configurations must be serialisable, so fuctions can only be embedded as
    fully qualified python names.  For stand-alone styles, raw callable functions can be
    used.

Stand-alone style objects are created by passing a valid style configuration to the
``StandaloneStyle`` constructor:

 ::

    from datacube_ows.styles.api import StandaloneStyle

    style = StandaloneStyle({
        "needed_bands": ["red", "green", "blue"],
        "scale_factor": 1.0,
        "components": {
            "red": {"red": 1.0},
            "green": {"green": 1.0},
            "blue": {"blue": 1.0}
        }
    })


Applying a style to Dataset
---------------------------

A stand-alone style can be applied to an XArray dataset (i.e. as returned by the ODC ``load_data()`` method)
to produce a 24bit RGBA image.

The input is expected to be an ``xarray.Dataset`` object with all of the bands referenced by the style
definition present as data variables.  Furthermore, any bands used as bitflags (either for masking
with ``pq_mask`` or colour-coding in colour-map style using ``value_map``) must have an ODC-compatible
``flag_definition`` attribute.  There must be a ``time`` dimension, although it will normally have only
one value (unless the style you are working with has ``multi_date_handlers``). If you obtain your
Dataset from the ODC ``load_data`` method, then you need only ensure that all bands are present

The output will be a new ``xarray.Dataset`` object with the same ``dims`` and ``coords`` as the input
data (except without the ``time`` dimension), and four uint8 data_vars: red, green, blue and alpha.

You may also optionally provide a valid-data mask: a boolean ``xarray.DataArray`` with the same ``dims`` and coords`` as the input
data.  Pixels that are False in the mask will normally have zero alpha channel in the output.

There are two API functions that provide this functionality: ``apply_ows_style``, ``apply_ows_style_cfg``:

::

    from datacube_ows.styles.api import StandaloneStyle, apply_ows_style, apply_ows_style_cfg

    # Given:

    cfg = {
        # Some style config ...
    }
    style = StandaloneStyle(cfg)

    # and data (an Xarray Dataset as returned by ODC load_data method);
    # The following are equivalent:

    image = apply_ows_style_cfg(cfg, data)
    image = apply_ows_style(style, data)

    # Examples with mask:

    mask = data["extent"] != 0

    image = apply_ows_style_cfg(cfg, data, valid_data_mask=mask)
    image = apply_ows_style(style, data, valid_data_mask=mask)

Auto-generating a legend image
------------------------------

To generate a legend image from a ``StandaloneStyle`` object or a style config, use the
``generate_ows_legend_style_cfg`` or ``generate_ows_legend_style`` functions.  Both take an
optional dates parameter, which can be either an integer or an iterable of date values (in any
representation, only the length is used).

The dates parameter determines whether to use the main style legend, or one of the
multi-date handler legends.  By default, the main style legend is used.

The return value is a PIL Image object.  Note that this is a very different output format
to the Apply OWS Style methods described above.

::

    from datacube_ows.styles.api import StandaloneStyle, generate_ows_legend_style_cfg, generate_ows_legend_style

    cfg = {
        # Some style config ...
    }
    style = StandaloneStyle(cfg)

    # Generate a normal (single date) legend:

    image = generate_ows_legend_style(cfg)
    # or
    image = generate_ows_legend_style_cfg(style)

    # Generate a multi-date legend:

    image = generate_ows_legend_style(cfg, 2)
    # or
    image = generate_ows_legend_style_cfg(style, ["yesterday", "today"])
