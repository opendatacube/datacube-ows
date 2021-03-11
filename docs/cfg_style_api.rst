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

1. "name" and "abstract" are optional.

   As Style objects are stand-alone they do not require metadata, or a unique identifier.

2. Style inheritance cannot be used.

   Style inheritance depends on the context of the enclosing complete OWS Configuration and
   so is not available for stand-alone styles.

3. The various band-aliasing techniques are not available.

    It is up to the the user of the API to ensure the band names in the style definition exactly
    match the data variable names in the XArray Dataset being styled.

4. Auto-legend generation is not supported initially.

   Support will be added to the API soon.


