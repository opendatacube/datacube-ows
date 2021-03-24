=======================
OWS Stying HOW-TO Guide
=======================

.. toctree::
   :maxdepth: 2
   :hidden:

   style_howto_components

.. contents:: Table of Contents

Introduction
============

Scope
-----

This HOW-TO Guide is aimed at scientific staff with a good understanding
of their data product and the use of the Open Data Cube (ODC). It aims to:

1. provide some specific examples of how to call the OWS Styling API to
   generate test images from raw ODC data.
2. demonstrate how to configure OWS styles with real-world examples.

For thorough technical description of the configuration format,
`see the configuration documentation
<https://datacube-ows.readthedocs.io/en/latest/configuration.html>`_.

Introduction - Testing styles
-----------------------------

We'll start with a quick but complete walk through the process of creating an
image with the API.

First of all, you'll need some data.  Select a bounding box (in lat/long), a date,
a resolution, and an output CRS, the measurement bands you need, and obtain your data
from the Open Data Cube.

Note that it is *essential* that you select all the bands used by your style
definition.
lable bands so we can use this data for all the examples on this page.)

::

    from datacube import Datacube
    dc = Datacube()
    data = dc.load(
        product='ls8_nbart_geomedian_annual',
        measurements=['red', 'green', 'blue'],
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
    :width: 600

`View full size
<https://user-images.githubusercontent.com/4548530/112110854-96f17b80-8c07-11eb-9f21-ab5ff49b9fda.png>`_

`Next <https://datacube-ows.readthedocs.io/en/latest/style_howto_components.html>`_
we start to look at how style configurations work.