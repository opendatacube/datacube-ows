===============================
OWS Configuration - WCS Section
===============================

.. contents:: Table of Contents

WCS Section
--------------

The ``wcs`` section of the `root configuration object
<https://datacube-ows.readthedocs.io/en/latest/configuration.html>`_
contains config entries that apply
to the WCS services for all coverages.

The ``wcs`` section must be supplied if the WCS service is
activated (specified in the `global services <https://datacube-ows.readthedocs.io/en/latest/cfg_global.html#service-selection-services>`_
section).


Supported output formats (formats)
==================================

Specifies the supported WCS output formats.

This section must be supplied if the WCS service is
activated (specified in the `global services <https://datacube-ows.readthedocs.io/en/latest/cfg_global.html#service-selection-services>`_
section) and must contain at least one output format.

Support for GeoTIFF and and NetCDF is included in datacube_ows.  Adding
another format would require writing a new python methods to render
the output images for WCS1 and WCS2.

For 99% of users, then, this section should configure for GeoTIFF and
NetCDF formats and look something like this:

::

    "formats": {
            # Key is the format name, as used in DescribeCoverage XML
            "GeoTIFF": {
                "renderers": {
                    "1: "datacube_ows.wcs1_utils.get_tiff",
                    "2: "datacube_ows.wcs2_utils.get_tiff",
                },
                # The MIME type of the image, as used in the Http Response.
                "mime": "image/geotiff",
                # The file extension to add to the filename.
                "extension": "tif",
                # Whether or not the file format supports multiple time slices.
                "multi-time": False
            },
            "netCDF": {
                "renderers": {
                    "1": "datacube_ows.wcs1_utils.get_netcdf",
                    "2": "datacube_ows.wcs2_utils.get_netcdf",
                "mime": "application/x-netcdf",
                "extension": "nc",
                "multi-time": True,
            }
        },

Renderer is set using OWS's `function configuration format <https://datacube-ows.readthedocs.io/en/latest/cfg_functions.html>`_.

For WCS1, The function is expected to take the following arguments:
  * A WCSRequest object
  * An xarray.DataArray to render

For WCS2, additional arguments are required and adding an additional output format may
not be possible from configuration changes alone. Some special use cases may require
tweaking the MIME type or the file extension. More extensive modifications are not
guaranteed to be supported. Refer to the source code and be very sure about what you are doing.

Native Format (native_format)
=============================

Specifies the default output format to use if the user does not
specify a format.

This entry must be supplied if the WCS service is
activated (specified in the `global services <https://datacube-ows.readthedocs.io/en/latest/cfg_global.html#service-selection-services>`_
section) and must contain the name of one of the formats in
defined in the
`formats <#supported-output-formats-formats>`_ section.

GEOTiff Statistics (calculate_tiff_statistics)
==============================================

An optional boolean (defaults to True) that only applies for geotiff coverage responses.

It specifies whether or not channel statistics (max/min/avg/stddev) are calculated and stored
in TIFF metadata.  Calculating statistics results in better interoperability with some clients
(e.g. QGIS) but results in increased memory usage when generating very large coverage files.

We recommend leaving this setting false (the default) unless you particularly need to
support very large coverage files.

::

    # Suppress tiff statistics to support very large geotiff responses
    "calculate_tiff_statistics": False,

GetCapabilities Cache Control Headers (caps_cache_maxage)
=========================================================

The ``caps_cache_maxage`` entry in the ``wcs`` section controls the value of the
``Cache-control`` HTTP header returned with WCS GetCapabilities responses.

Refer to the documentation for
`WMS GetCapabilities Caching <https://datacube-ows.readthedocs.io/en/latest/cfg_wms.html#GetCapabilities-Cache-Control-Headers-caps_cache_maxage>`_
for further information (the WCS behaviour is identical, except it applies to
the WCS Capabilities document instead of WMS and WMTS).

DescribeCoverage Default Cache Control Headers (default_desc_cache_maxage)
==========================================================================

The ``default_desc_cache_maxage`` entry in the ``wcs`` section controls the default value of the
``Cache-control`` HTTP header returned with WCS DescribeCoverage responses.

Behaviour is identical to the ``caps_cache_maxage`` entry discussed above and
`WMS GetCapabilities Caching <https://datacube-ows.readthedocs.io/en/latest/cfg_wms.html#GetCapabilities-Cache-Control-Headers-caps_cache_maxage>`_.

Note however, that the default DescribeCoverage cache rule for can
be over-ridden at the layer/coverage level using the
`describe_cache_maxage entry<https://datacube-ows.readthedocs.io/en/latest/cfg_layers.html#cache-control-dataset-cache-rules-and-describe-cache-maxage>`_
in the ``resource_limits`` section for the layer.
