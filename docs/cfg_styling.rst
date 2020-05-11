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
one style.  There are several different