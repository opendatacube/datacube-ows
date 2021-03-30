==========================================
OWS Stying HOW-TO Guide: Colour Map Styles
==========================================

.. contents:: Table of Contents

Colour Maps
-----------

Discrete measurement bands (i.e. bit-flag or enumeration bands) demand very different visualisation
approaches than continuous measurement bands, and they are not well served by the sorts of
component and ramp based styles we have discussed so far[1]_.

Example Data
------------



Colour Maps work on a single band by defining a series of logical rules, with the first rule a pixel
matches determining the colour of the pixel.



.. [1] You could force the use case onto colour-ramp styles pretty easily.  But a colour map gives a few advantages -
   in particular the embedded metadata which can be used to autogenerate a legend.


