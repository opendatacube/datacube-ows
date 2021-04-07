====================================
OWS Styling HOW-TO Guide: Components
====================================

.. contents:: Table of Contents


Simple Linear Components
------------------------

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

It's easiest to explain with some examples.  We will use the same test data as in the
introduction, but this time we will select all the available measurement bands, so we
can re-use the same data for all the examples in this section.

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

Example: Infrared/Green False Colour
++++++++++++++++++++++++++++++++++++

Lets start with a popular false-colour style, using optical green and two infrared bands.
Note that the "green" band of the data is not assigned to the "green" channel of the
output image.

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
    :width: 600

`View full size
<https://user-images.githubusercontent.com/4548530/112120795-b215b880-8c12-11eb-8bfa-1033961fb1ba.png>`_

Example: Greyscale single band
++++++++++++++++++++++++++++++

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

Example: Mixing bands
+++++++++++++++++++++

What if we want to mix more than one band to make each channel? Here we average all three visible bands
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
    :width: 600

`View full size
<https://user-images.githubusercontent.com/4548530/112124842-e8553700-8c16-11eb-9d60-a5a964d3a9ab.png>`_

Example: Unused channels
++++++++++++++++++++++++

If you don't want to write any data to one or more of the image channels (red, green or blue)
just leave it empty:

::

    only_red_cfg = {
        "components": {
            "red": {
                "red": 1.0
            },
            "green": {},
            "blue": {},
        },
        "scale_range": (50, 3000),
    }


.. image:: https://user-images.githubusercontent.com/4548530/112239767-357aec80-8c9b-11eb-9827-6696a1d03a17.png
    :width: 600

`View full size
<https://user-images.githubusercontent.com/4548530/112239767-357aec80-8c9b-11eb-9827-6696a1d03a17.png>`_

Scale Ranges: Controlling dynamic range
---------------------------------------

What about the other part of that config - the ``scale_ranges`` part? Let's try some other values and see what happens.

Firstly, let's remind ourselves of our original RGB configuration and image:

::

    rgb_cfg = {
        "components": {
            "red": {"red": 1.0},
            "green": {"green": 1.0},
            "blue": {"blue": 1.0},
        },
        "scale_range": (50, 3000),
    }

.. image:: https://user-images.githubusercontent.com/4548530/112110854-96f17b80-8c07-11eb-9f21-ab5ff49b9fda.png
    :width: 600

`View full size
<https://user-images.githubusercontent.com/4548530/112110854-96f17b80-8c07-11eb-9f21-ab5ff49b9fda.png>`_

Example: Low Scale Range
++++++++++++++++++++++++

Let's start by pulling the scale_range down a bit:

::

    rgb_low_scale_rng_cfg = {
        "components": {
            "red": {"red": 1.0},
            "green": {"green": 1.0},
            "blue": {"blue": 1.0},
        },
        "scale_range": (10, 800),
    }


.. image:: https://user-images.githubusercontent.com/4548530/112252356-15562800-8cb1-11eb-961a-8c10c38167d7.png
    :width: 600

`View full size
<https://user-images.githubusercontent.com/4548530/112252356-15562800-8cb1-11eb-961a-8c10c38167d7.png>`_

As you can see, the resulting image looks saturated, washed out and overly bright.  So if your first
guess at scale_range values produced an image like this, you probably want to increase your
scale_range a bit.

Example: High Scale Range
+++++++++++++++++++++++++

::

    rgb_high_scale_rng_cfg = {
        "components": {
            "red": {"red": 1.0},
            "green": {"green": 1.0},
            "blue": {"blue": 1.0},
        },
        "scale_range": (1000, 8000),
    }

.. image:: https://user-images.githubusercontent.com/4548530/112252569-75e56500-8cb1-11eb-89ae-fde23ea3df58.png
    :width: 600

`View full size
<https://user-images.githubusercontent.com/4548530/112252569-75e56500-8cb1-11eb-89ae-fde23ea3df58.png>`_

Whoops too far!  Now it's almost pure black!  If your image looks like this, you
need to pull your scale_range down a bit:

Example: Narrow Scale Range
+++++++++++++++++++++++++++

::

    rgb_narrow_scale_rng_cfg = {
        "components": {
            "red": {"red": 1.0},
            "green": {"green": 1.0},
            "blue": {"blue": 1.0},
        },
        "scale_range": (1000, 3000),
    }

.. image:: https://user-images.githubusercontent.com/4548530/112252764-c230a500-8cb1-11eb-873a-68527e786f69.png
    :width: 600

`View full size
<https://user-images.githubusercontent.com/4548530/112252764-c230a500-8cb1-11eb-873a-68527e786f69.png>`_

This is better, but the lower end of the scale range is too high. If you keep adjusting back and forth,
you'll eventually end up more or less where we started.

Example: Per-channel scale_ranges
+++++++++++++++++++++++++++++++++

What if we want to apply a different scale ranges to different channels?

For example, the image in the `false colour example above
<#example-infrared-green-false-colour>`_, looks a bit
saturated, especially in the red and green bands (red+green make yellow).

.. image:: https://user-images.githubusercontent.com/4548530/112120795-b215b880-8c12-11eb-8bfa-1033961fb1ba.png
    :width: 600

`View full size
<https://user-images.githubusercontent.com/4548530/112120795-b215b880-8c12-11eb-8bfa-1033961fb1ba.png>`_

Let's see what we can do with some judicious tweaking of the scale_ranges
on a per-band basis:

::

    irg_bandscale_cfg = {
        "components": {
            "red": {
                "swir1": 1.0,
                "scale_range": (1500, 3700),
            },
            "green": {
                "nir": 1.0,
                "scale_range": (1600, 3200),
            },
            "blue": {
                "green": 1.0
            },
        },
        "scale_range": (200, 1900),
    }

The "blue" channel takes the default scale_range ``(200,1900)``.

The red and green channel have custom scale ranges.

.. image:: https://user-images.githubusercontent.com/4548530/112267141-1f842080-8cc9-11eb-92c8-d66fba3a43ac.png
    :width: 600

`View full size
<https://user-images.githubusercontent.com/4548530/112267141-1f842080-8cc9-11eb-92c8-d66fba3a43ac.png>`_

Wow! That looks much better!

But don't get too carried away!  You'll probably find that these particular scale ranges
look really dark and washed out in south eastern australia and super bright and saturated
in the central deserts.  The trick is usually to choose a few datasets from different
land cover types and come up with a compromise configuration that looks good everywhere.

But as any scientist will tell you, when it comes to visualisation, linear equations can
only get you so far, so `next
<https://datacube-ows.readthedocs.io/en/latest/style_howto_components_nonlinear.html>`_
we start to look at how to apply more powerful maths to calculate components.
