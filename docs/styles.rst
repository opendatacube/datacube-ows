=====
Layer Styling
=====

.. note:: The full documentation is included in the source, please see **ows_cfg_example.py**

OWS supports extensive image processing during styling performed via
using PIL, numpy and other array processing mechanisms.

Sample styles include:

#. Style RGB - A passthrough style for plain RGB imagery.
#. Styles with Masking - Use mask sources to blank out RGB imagery.
#. Styles with multi-band mathematical processing - Clear examples of this form
of styling is NDVI computation on the fly. These have floating point output and
have to be combined with colourmaps.
#. Styles with implicit and explicit colour maps - Colour maps can be specified
explicitly using a **color_ramp** dictionary or implicitly to use a Matplotlib
color_map using **mpl_ramp** string key.
#. The above styles can be combined and complex raster processing/band-combination
performed using **index_function** definitions. Index functions refer by name to
a python function used as a lambda to process every pixel in the input bands.
