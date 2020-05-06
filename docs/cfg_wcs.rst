=================
OWS Configuration
=================

.. contents:: Table of Contents

WCS Section
--------------

The ``wcs`` section of the `root configuration object
<configuration.rst>`_
contains config entries that apply
to the WCS services for all coverages.

The ``wcs`` section must be supplied if the WCS service is
activated (specified in the `global services <cfg_global.rst#service-selection-services>`_
section).


Supported output formats (formats)
==================================

Specifies the supported WCS output formats.

This section must be supplied if the WCS service is
activated (specified in the `global services <cfg_global.rst#service-selection-services>`_
section) and must contain at least one output format.

Support for GeoTIFF and and NetCDF is included in datacube_ows.  Adding
another format would require writing a new python method to render
the output images.

For 99% of users, then, this section should configure for GeoTIFF and
NetCDF formats and look something like this:

::

    "formats": {
            # Key is the format name, as used in DescribeCoverage XML
            "GeoTIFF": {
                # Renderer is the FQN of a Python function that takes:
                #   * A WCSRequest object
                #   * Some ODC data to be rendered.
                "renderer": "datacube_ows.wcs_utils.get_tiff",
                # The MIME type of the image, as used in the Http Response.
                "mime": "image/geotiff",
                # The file extension to add to the filename.
                "extension": "tif",
                # Whether or not the file format supports multiple time slices.
                "multi-time": False
            },
            "netCDF": {
                "renderer": "datacube_ows.wcs_utils.get_netcdf",
                "mime": "application/x-netcdf",
                "extension": "nc",
                "multi-time": True,
            }
        },

Some special use cases may require tweaking the MIME type or the
file extension. Either way don't touch this section unless you
are very sure about what you are doing.

Native Format (native_format)
=============================

Specifies the default output format to use if the user does not
specify a format.

This entry must be supplied if the WCS service is
activated (specified in the `global services <cfg_global.rst#service-selection-services>`_
section) and must contain the name of one of the formats in
defined in the
`formats <#native-format-native_format>`_ section.


