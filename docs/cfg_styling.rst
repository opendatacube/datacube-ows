=================
OWS Configuration
=================

.. contents:: Table of Contents

Styling Section
---------------

The "styling" sub-section of a `layer configuration section
<cfg_layers.rst>`_
contains definitions of the various styles
that layer supports.

Styles officially only apply to WMS and WMTS
requests. Datacube-OWS WCS GetCoverage requests will accept
a styles parameter, but this is not compliant with the
standard.  (I.e. an unofficial extension to the WCS standard).
Consequently, the "styling" section is always required,
even if WMS and WMTS services are deactivated.

The "styling" section has two entries: styles and default_style.

styles and default_style
========================

The "styles" list must be supplied, and must contain at least
one style.  There are several different possible style, each
with a slightly different syntax, these are discussed below.

The "default_style" entry is optional and identifies the style
that will be used by default if no style is specified in the
request.  If not supplied, it defaults to the first style in the
"styles" list.

E.g. Here the second style "another_style" is the default. If the
"default_style" entry is removed from this snippet, then the first
style "a_style" will be the default.

::

    "styling": {
        "default_style": "another_style",
        "styles": [
            { "name": "a_style", ... },
            { "name": "another_style", ... },
        ]
    }

Style Types
===========

There are four distinct possible types of style.

1. `Component Styles <#component-styles>`_

   Each component channel of the image (red, green, blue and optionally
   alpha) is calculated independently from the data for that pixel.

2. `Colour Map Styles <#colour-map-styles>`_

   Each pixel is mapped to one particular colour from a fixed pallet
   by applying a logical decision tree to the date for that pixel.

3. `Colour Ramp Styles <#colour-ramp-styles>`_

   A single continuous index value is calculated from the data for
   each pixel, and that index value mapped to a graduated colour ramp
   for display.

4. `Hybrid Styles <#hybrid-styles>`_

   A linear combination of a component style and a colour ramp style.

   This can allow for a more easily visually interpreted image, but
   there are usually better ways to achieve the same effect on the
   client side.

----------------
Component Styles
----------------

-----------------
Colour Map Styles
-----------------

------------------
Colour Ramp Styles
------------------

-------------
Hybrid Styles
-------------

