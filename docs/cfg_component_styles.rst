=================
OWS Configuration
=================

.. contents:: Table of Contents

Component Styles
----------------

Component Styles are `styles<cfg_styling.rst>`_ where
each component channel of the image (red, green, blue and optionally
alpha) is calculated independently from the data for that pixel.

Component styles support the
`elements common to all styles<cfg_styling.rst#common-elements>`_.

There are two additional settings specific to component styles:
`scale_range<#style-scale-range>` and `components<#components>`

----------
components
----------

The components section contains one component definition per
component channel of the output image::

  * "red" (required)
  * "green" (required)
  * "blue" (required)
  * "alpha" (optional)

Alpha is the opacity of each pixel.  When alpha is 0 the image pixel is
fully transparent, when 255 fully opaque.  If not provided, the alpha channel
is assumed to be always fully opaque (unless otherwise masked, e.g. by
the `extent mask<cfg_layers.rst#extent-mask-function-extent-mask-func>`_
or `style masking<cfg_styling.rst#bit-flag-masks-pq-masks>`_).

Calculating the value for each pixel has two steps::

1. Calculate an unscaled channel value.

   Each component definition defines either a
   `linear combination of raw channel data<#linear-combination-components>`_
   or a
   `callback function<#callback-function-components>`_
   (as discussed in detail below) to determine the unscaled value
   for that channel for each pixel.

2. Scale the unscaled value to unsigned 8-bit value (0-255).

   This is defined by the `scale_range<#component-scale-range`_
   entry for the channel if it exists, or the style-wide
   `scale_range<#style-scale-range>`_.

Component scale_range
+++++++++++++++++++++

Defines the raw band value range that will be compressed
to an 8 bit range for the output image.  Band values outside
this range are clipped to 0 or 255.

The component scale_range is optional and if not present defaults
to the `style-side scale_range<#style-scale-range>`_.

E.g.::

    # raw values less than 15 are clipped to 0 and raw values greater than 3100
    # are clipped to 255.  Raw values from 15 to 3100 are linearly scaled to the
    # 8 bit range 0 to 255.

    "scale_range": [15, 3100],

Linear Combination Components
+++++++++++++++++++++++++++++

Callback Function Components
+++++++++++++++++++++++++++++

-----------------
Style scale_range
-----------------

Defines the raw band value range that will be compressed
to an 8 bit range for the output image.  Band values outside
this range are clipped to 0 or 255.

The style-level scale_range applies to all component channels
that do not set their own component-level scale_range, and that do not
have a function call back defined. These exceptions are described in
detail below.

The style-level scale_range is required unless all component channels
satisfy the exceptions discussed above and described in detail below.

E.g.::

    # raw values less than 15 are clipped to 0 and raw values greater than 3100
    # are clipped to 255.  Raw values from 15 to 3100 are linearly scaled to the
    # 8 bit range 0 to 255.

    "scale_range": [15, 3100],

