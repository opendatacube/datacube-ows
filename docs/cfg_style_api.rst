==========================================
OWS Configuration - OWS Styling Python API
==========================================

.. contents:: Table of Contents

Motivation
----------

OWS configuration is complex, and for large deployments refining stylings can quickly
get bogged down in a constant back and forth between the Dev Ops engineers responsible
for the configuration as a whole, and the scientific staff responsible for individual
products/layers within that configuration.

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

   Style inheritance is an OWS feature that allows styles to be extended from existing styles
   in the configuration hierarchy.

   As stand-alone style objects exist outside of the configuration hierarchy, style inheritance
   is not applicable.

3. The various OWS-specific band-aliasing techniques are not available.

    It is up to the the user of the API to ensure the band names in the style definition exactly
    match the data variable names in the XArray Dataset being styled.

    Make sure you reference measurement bands from the source product using the same names
    that you requested in the `dc.load()` statement.

4. Function objects/callables can be used directly in stand-alone style definitions.

    Full OWS Configurations must be serialisable, so fuctions can only be embedded as
    fully qualified python names.  For stand-alone styles, raw callable functions can be
    used.  Some examples are shown below.

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

    from datacube import Datacube
    from datacube_ows.styles.api import StandaloneStyle
    from datacube_ows.styles.api import apply_ows_style, apply_ows_style_cfg
    from datacube_ows.styles.api import xarray_image_as_png

    # Given:

    cfg = {
        # Some style config ...
    }
    style = StandaloneStyle(cfg)

    # and data (an Xarray Dataset as returned by ODC load_data method);
    dc = Datacube()
    data = dc.load( ...query parameters... )

    # The following are equivalent:

    image = apply_ows_style_cfg(cfg, data)
    image = apply_ows_style(style, data)

    # Examples with mask:

    mask = data["extent"] != 0

    image = apply_ows_style_cfg(cfg, data, valid_data_mask=mask)
    image = apply_ows_style(style, data, valid_data_mask=mask)

For more detailed examples,
refer to the
`styling how-to guide <https://datacube-ows.readthedocs.io/en/latest/styling_howto.html>`_.

Saving or Displaying Images
---------------------------

A helper method is provided to convert a uint8 RGBA Xarray (such as are returned by
the ``apply_ows_style`` methods discussed above) into a PNG image:

::

    with open("filename.png", "wb") as fp:
        fp.write(xarray_image_as_png(image)


Helper methods are also supplied to display uint8 RGBA Xarray images via matplotlib
(e.g. for JupyterHub and similar environments):

::

    # Displaying an xarray image (assumes coordinates are called "x" and "y")
    plot_image(image)

    # Displaying an xarray image, specifying the horizontal and vertical coordinate names
    plot_image(image, x="Longitude", y="Latitude")

    # Displaying an xarray image, specifying image height in inches (defaults to 10)
    plot_image(image, size=4)

Shortcut methods are also available for applying a style to some data and displaying the image in
one step:

::

    # Using a standalone style object
    plot_image_with_style(style, data, x="long", y="lat", size=7.5)

    # Using a style configuration dictionary
    plot_image_with_style_cfg({
                "index_expression": "(nir-red)/(nir+red)",
                "mpl_ramp": "ocean_r",
                "range": [0,1],
            }, data, x="long", y="lat", size=7.5)

Bulk Processing
---------------

Bulk processing over a non-spatial dimension of the input data (usually time) is supported via the
optional ``loop_over`` parameter to ``apply_ows_style``, ``apply_ows_style_cfg``, and
``xarray_image_as_png``:

::

    from datacube import Datacube
    from datacube_ows.styles.api import StandaloneStyle
    from datacube_ows.styles.api import apply_ows_style, apply_ows_style_cfg
    from datacube_ows.styles.api import xarray_image_as_png

    cfg = {
        # Some style config ...
    }
    style = StandaloneStyle(cfg)

    # This ODC query returns data for multiple dates.
    dc = Datacube()
    data = dc.load( ...query parameters... )

    # images is an xarray.Dataset with same time dimension coordinates as the input data.
    # Each time slice is styled independently.
    images = apply_ows_style(style, data, loop_over="time")

    # This code will write out the images to the local filesystem as `filename00.png`, `filename01.png`, etc.

    pngs = xarray_image_as_png(images, loop_over="time")
    for i, png in enumerate(pngs):
        with open(f"filename{i:02}.png", "wb") as fp:
            fp.write(xarray_image_as_png(image)


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

PIL objects are well supported by Notebookes. Simply calling any of the method below, and/or evaluating the returned
PIL Image object will display the image in JupyterHub, Notebooks, etc.

::

    from datacube_ows.styles.api import StandaloneStyle, generate_ows_legend_style_cfg, generate_ows_legend_style

    cfg = {
        # Some style config ...
    }
    style = StandaloneStyle(cfg)

    # Generate a normal (single date) legend:

    image = generate_ows_legend_style_cfg(cfg)
    # or
    image = generate_ows_legend_style(style)

    # Generate a multi-date legend (and display if in JupyterHub/notebook type environment):

    image = generate_ows_legend_style_cfg(cfg, 2)
    # or
    image = generate_ows_legend_style(style, ["yesterday", "today"])

    # Write out as PNG:
    with open("filename.png", "wb") as fp:
        image.save(fp)
