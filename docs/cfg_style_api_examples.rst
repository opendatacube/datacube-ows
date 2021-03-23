===================================================
OWS Configuration - OWS Styling Python API Examples
===================================================

.. contents:: Table of Contents

Introduction - Testing styles
-----------------------------

We'll start with a quick but complete walk through the process of creating an image with API.

First of all, you'll need some data.  Select a bounding box (in lat/long), a date, a resolution,
and an output CRS, the measurement bands you need, and obtain your data from the Open Data Cube.

(We are selecting all available bands so we can use this data for all the examples on this page.)

::

    from datacube import Datacube
    dc = Datacube()
    data = dc.load(
        product='ls8_nbart_geomedian_annual',
        measurements=['red', 'green', 'blue', 'nir', 'swir1', 'swir2'],
        latitude=(-16.1144, -13.4938),
        longitude=(140.7184, 145.6924),
        time=('2019-01', '2019-01'),
        output_crs="EPSG:3577",
        resolution=(-300,300)
    )

This query results in an xarray dataset, and therefore a final image, with a
pixel resolution of 1128x668.

Now we create a style configuration dictionary.  We'll start with a simple
RGB "true colour" visualisation.

::

    rgb_cfg = {
        "components": {
            "red": {"red": 1.0},
            "green": {"green": 1.0},
            "blue": {"blue": 1.0},
        },
        "scale_range": (50, 3000),
    }

Don't worry about understanding what everything in that, we'll cover that later. For now, we
can apply this style to the data, and write the result to disk as a PNG file:

::

    from datacube_ows.styles.api import StandaloneStyle, apply_ows_style_cfg, xarray_image_as_png

    xr_image = apply_ows_style_cfg(rgb_cfg, data)
    png_image = xarray_image_as_png(xr_image)
    with open("example1.png", "wb") as fp:
         fp.write(png_image)

The resulting image looks like this:

.. image:: https://user-images.githubusercontent.com/4548530/112110854-96f17b80-8c07-11eb-9f21-ab5ff49b9fda.png
    :width: 1128

Other Simple Component Examples
-------------------------------

Now lets look at that configuration in a bit more details:

::

    rgb_cfg = {
        "components": {
            "red": {"red": 1.0},
            "green": {"green": 1.0},
            "blue": {"blue": 1.0},
        },
        "scale_range": (50, 3000),
    }

The ``components`` section lets you specify the three output image RGB channels independently.

It is important not to get confused between the keys of the outer dictionary, which are
the output image channels and should always be "red", "green" and "blue"; and the keys of
the inner dictionaries, which are measurement bands of the ODC data being styled.

For example, here is a popular false-colour style, using optical green and two infrared bands:

::

    ir_green_cfg = {
        "components": {
            "red": {
             "swir1": 1.0
            },
            "green": {
             "nir": 1.0
            },
            "blue": {
             "green": 1.0
            },
        },
        "scale_range": (50, 3000),
    }

.. image:: https://user-images.githubusercontent.com/4548530/112120795-b215b880-8c12-11eb-8bfa-1033961fb1ba.png
    :width: 1128

If we wanted a greyscale image of a single band (say red), you could do this:

::

    pure_red_cfg = {
        "components": {
            "red": {
             "red": 1.0
            },
            "green": {
             "red": 1.0
            },
            "blue": {
             "red": 1.0
            },
        },
        "scale_range": (50, 3000),
    }


.. image:: https://user-images.githubusercontent.com/4548530/112124234-3ddd1400-8c16-11eb-9d01-37b895010221.png
    :width: 1128

What if want to mix more than one band to make each channel? Here we average all three visible bands
into the red channel, put near infra-red in the green channel amd average the two shortwave infrared
bands to make the blue channel:

::

    all_bands_cfg = {
        "components": {
            "red": {
             "red": 0.333,
             "green": 0.333,
             "blue": 0.333,
            },
            "green": {
             "nir": 1.0
            },
            "blue": {
             "swir1": 0.5,
             "swir2": 0.5,
            },
        },
        "scale_range": (50, 3000),
    }


.. image:: https://user-images.githubusercontent.com/4548530/112124842-e8553700-8c16-11eb-9d60-a5a964d3a9ab.png
    :width: 1128


You can read more about
`component based styles <https://datacube-ows.readthedocs.io/en/latest/cfg_component_styles.html>`_
in the documentation.
