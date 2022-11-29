=======
History
=======

1.8.x Releases
==============

Datacube-ows version 1.8.x indicates that it is designed work with datacube-core versions 1.8.x.

1.8.32 (2022-11-30)
-------------------

Full list of changes:

* Add datacube pypi badge (#891)
* Pre-commit auto-updates (#894, #899, #906)
* Github action update (#896)
* Documentation updates (#898, #903, #904)
* WCS grid counts and add checks for sign errors in native resolution (#902)
* Match docker image version numbers to github SCM version numbers (#907, #908, #909)
* Update default version number and HISTORY.rst (#910)

Contributions from @pindge and @SpacemanPaul (and of course, the pre-commit-ci bot).


1.8.31 (2022-10-24)
-------------------

Full list of changes:

* Added pre_scaled_norm_diff to band_utils.py, allowing calculation of normalised difference calculations on
  data that is scaled with an offset. (#881)
* Add support for url patching - allowing OWS to serve data from commercial data repositories that use
  uri signing for authentication (e.g. Microsoft Planetary Computer) (#883)
* Further refinements to Sentry logging. (#884)
* Improve interoperability with Jupyter Notebooks. (#886)
* Allow band alises for Flag Bands taken from main product(s). (#887)
* Add new metadata type to MV definitions, to support DEA Sentinel-2 Collection 3. (#888)
* Add support for html info_format for GetFeatureInfo queries in WMS and WMTS - may improve ArcGIS
  compatibility. (#889)
* Updates to HISTORY.rst, README.rst and default version string for release (#890)

Contributions from @pindge, @rtaib and @SpacemanPaul.

1.8.30 (2022-10-11)
-------------------

Minor release, consisting of better Sentry reporting for production deployments, and routine repository
maintainance.

Full list of changes:

* Update code-of-conduct.md to refer to current ODC Steering Council chair (#862)
* Fixes to docker-compose files and github workflows (#864, #866, )
* Simplify and cleanup scripts and config to create database for integration tests (#865, #871)
* Change interpretation of Sentry environment variables to allow Sentry reporting to any hosted Sentry service (#868, #877)
* Prevent mysterious Shapely warning message from clogging up Sentry logs (#873)
* Minor tweaks to aid trouble-shooting and better support local deployments (#878)
* Updates to HISTORY.rst, README.rst and default version string for release (#879)

Contributions from @pindge and @SpacemanPaul.

1.8.29 (2022-08-30)
-------------------

This release includes support for heterogenous multi-product layers (single layers that combine data
from satellite platforms with different bands and native resolutions - e.g. Sentinel-2 plus Landsat),
an upgrade to the docker container (now based on Ubuntu 22.04, with Python 3.10), plus documentation updates
and bug fixes.

Full list of changes:

* Enhancements to support heterogenous multi-product layers (#837, #841, #844)
* Refactor data for integration test fixtures (#835)
* Docker image migrated to Python3.10/Ubuntu-22.040-based osgeo/gdal base image, and updates to
  dependencies (#838, #843, #852, #854, #856, #859)
* Isolate ops imports to minimise dependencies for appliations only using the styling API (#855)
* Documentation updates and improvements (#846, #847, #848, #849)
* Bug Fix: Skip cached bounding boxes when layer extent is entirely outside the valid region for the CRS (#832)
* Bug Fix: Invalid version parameters in otherwise valid requests were failing with unhandled 500 errors. OWS now
  makes a best-effort guess in this case, tending towards the lowest supported version (#850)
* Bug Fix: response_crs parameter was not being handled correctly by WCS1 (#858)
* Updates to HISTORY.rst and default version string for release (#860)

This release includes contributions from @SpacemanPaul, and @pindge.

1.8.28 (2022-04-12)
-------------------

This release introduces changes to both the materialised view definitions and the ``datacube-ows-update``
utility to improve the accuracy and reliability of these extents, as well as bug fixes for
externally-hosted legend images.

This release includes:

* A bug fix to the OWS code which reads from the materialised views, preventing runtime errors
  from occurring in scenarios where accurate extent information is not available (#825)
* Enhancements to the materialised view definitions to support extracting extent polygons
  from various optional metadata locations in both EO and EO3 based products. (#826)
* Sanity-check and sanitise bounding box ranges for global datasets.  It should now be
  possible to use datasets with bounding box ``(-180, -90, 180, 90, crs=EPSG:4326)`` in
  OWS.  Previously this required hacking the metadata to result in e.g.
  ``(-179.9999, -89.9999, 179.999, 89.999, crs=EPSG:4326)`` (#828)
* Usability improvements for external legends. Clearer reporting of read errors on external
  urls, and raise warning instead of failing if external image format is not PNG. (#829)
* Update HISTORY.rst and default version number (#830)

Upgrade notes:
++++++++++++++

To enjoy all the advantages of these extent handling enhancements you will need to
run the following command, using a database role capable of altering the schema::

     datacube-ows-update --schema --role role_to_grant_access_to

After regenerating the schema, the range tables should also be updated::

     datacube-ows-update

(Note that there is no need to run ``datacube-ows-update`` with the ``--views`` option in between these
two steps.)

1.8.27 (2022-04-04)
-------------------

Several bugfixes, and documentation updates and we had to change our CI test data because the old USGS Landsat PDS went user-pays.

Cache-control hints can now be configured for the XML requests (GetCapabilities, DescribeCoverage).  WMS and WCS GetCapabilities can be configured separately.  WCS DescribeCoverage can be configured globally and optionally over-ridden per layer/coverage.   Refer to the documentation for details.

Full list of changes since 1.8.26:
++++++++++++++++++++++++++++++++++

* Bug fix: Multidate NetCDF requests were broken in both WCS1 and WCS2- now fixed (#799)
* int8 added as a supported dtype (#801, #802)
* Logging updated to include remote IP (#808,#811,#818)
* Documentation updates (#810, #819, #820)
* Replace USGS Landsat data with Sentinel-2 data for CI integration testing. (#812, #817)
* Bug fix: Manual merge where no extent mask function was broken (#817)
* Cache-control hints for XML requests (GetCapabilities/DescribeCoverage) (#821, #822)
* Update HISTORY.rst and default version number (#823)

1.8.26 (2022-01-31)
-------------------

Optimisation release.  Performance improvements to colour-map style rendering algorithm.
For large, complex value_map rule sets the improvement is dramatic (e.g. DEA LCCS level4 style,
which contains over 100 rules, rendering speed is increased by 70-80%).

* Minor improvements to unit and docker testing (#792, #793)
* Optimisation of colour-map style rendering algorithm (#795)
* Increment default version number and update HISTORY.rst (#797)

1.8.25 (2022-01-19)
-------------------
Bug fix release.

The legend internationalisation code in 1.8.24 caused errors in manual legends for deployments that do not have internationalisation enabled.  This release fixes that issue.

* Legend internationalisation bug fix (#789, #790)
* Update default version number and HISTORY.rst (#791)

1.8.24 (2022-01-18)
-------------------

Introduces support for internationalisation (translation) of style legends - see the documentation for details:

https://datacube-ows.readthedocs.io/en/latest/configuration.html#metadata-separation-and-internationalisation
https://datacube-ows.readthedocs.io/en/latest/cfg_styling.html#url

This is the first formal release since the 9th December, although there were several interim releases in
mid-December when we were testing the Prometheus metric changes (see below).

Due to an oversight in deprecation warnings several releases ago, some configurations that worked in 1.8.23
will now raise errors.  Affected configurations have legacy "legend" hints embedded inside the colour ramp
definitions.  Such hints have not been read by OWS for quite some time, having been replaced by the "tick_labels" entry in the "legend" section.  Digital Earth Australia and Digital Earth Africa configurations have already been updated.

Changes since 1.8.23:

* Prometheus metric enhancements and release notes for interim releases (#777, #778, #779, #780, #781, #782)
* Github integration tests against a large real world OWS configuration (DEA) (#784)
* Internationalisation of style legends. (#783, #786)
* Fix WCS1 DescribeCoverage regression (missing SRS/CRS) (#787)
* Update History.RST and increment default version number (#788)

1.8.23.3 (2021-12-16)
---------------------

Interim administrative release.

* Upgraded Prometheus metrics to histogram type, and updated HISTORY.rst (#781)

1.8.23.2 (2021-12-15)
---------------------

Interim administrative release.

* Improved Prometheus metrics for monitoring (#779)
* Update HISTORY.rst (#780)

1.8.23.1 (2021-12-10)
---------------------

Interim administrative release.

* Improved Prometheus metrics for monitoring (#777)
* Update HISTORY.rst (#778)

1.8.23 (2021-11-16)
-------------------

In addition to the standard animated handlers previously supported by all style types, this release
introduces two additional approaches to produce an non-animated image from a multi-date request for
colour-map (aka value_map) type styles:

* Using a variant of the value_map_ entry used for the single-date case. This is a much simpler way of achieving most use cases.
* Using an aggregator function, which allows for fully customisable behaviour but requires writing Python code.

The new behaviour is fully documented here: https://datacube-ows.readthedocs.io/en/latest/cfg_colourmap_styles.html#multi-date-requests

This means that OWS now supports rich comparison visualisation techniques for both contiguous and discrete data products.

Also, the masking rule parser for pq_masks sections now uses the same code as the parser for value_map rules in colour map styles.

This means that:

* pq_mask rules now supports and/or operators, consistent with value_map rules.
* value_map rules now support the invert operator, consistent with pq_mask rules.
* The old "enum" keyword in pq_masks is now deprecated - please now use the values keyword, as in value_maps.

Full details are in the documentation. Old style syntax will continue to work as before - except the
enum keyword in pq_masks now produces a deprecated warning message.

Changes in this release:
++++++++++++++++++++++++

New Feature:

*  Support for non-animated multi-date handlers for "colour-map" type styles. (#770)
*  Consistent syntax for masking rules in pq_masks and value_map rules (#774)

Bug fixes

* Fix to bug affecting resource-limiting for WCS (#769)
* Fix bug in handling of missing data when applying cross-product masking (#772)

Dependency management and release process

* Remove constraint requiring very recent versions of numpy (#766)
* Upgrade to Postgis 3.1 (#767)
* Add automated spell check of documentation to github actions (#775)
* Increment default version number. (#776)

This release includes contributions from @Kirill888, @NikitaGandhi, @pindge and @SpacemanPaul

1.8.22 (2021-11-11)
-------------------

* Raise error on duplicate layer names. (#759)
* Add layer name to config manifest file format (#759)
* Apply configured http headers to WCS2 GetCoverage responses (#761)
* Remove and replace tests based on S3FS, removing test dependency on aiobotocore (#762)
* Documentation updates (#758)
* Increment default version number (#763)

1.8.21 (2021-10-21)
-------------------

* Allow layers with no ``extent_mask_function`` (#739)
* Eliminate redundant connection pool - use datacube-core connection pool directly (#740)
* Remove requirements.txt Use setup.py exclusively for dependency management. (#741, #744)
* Improve docker image efficiency (#743, #745, #746)
* Fix WCS1 bug affecting requests with no explicit measurements or style (#749)
* Add ``$AWS_S3_ENDPOINT`` to environment variable documentation (#751)
* Improve Prometheus metrics (#752)
* Fix function config internal over-writing issue - was causing issues for odc-stats (#754)
* Increment default version number and switch setuptools_scm to post-release version numbering (#753)

1.8.20 (2021-10-06)
-------------------

WCS enhancements, new docker image, bug fixes, and doc updates.

Please read the release notes before upgrading.

WCS changes
+++++++++++

As more in the community are starting to actively use WCS, we are slowly polishing away the rough edges. This
release has two changes of interest to OWS administrators who use WCS:

1. Firstly, the wcs ``default_bands`` has been removed. The default behaviour for WCS requests that do not specify
   bands is now to return all available bands, as specified in the WCS2 standards.

This means that layer-level ``wcs`` sections is no longer required. If you have any, you will get warning
messages. You can ignore these until you are sure that all your server instances have been upgraded to 1.8.20,
when it is safe to remove the layer ``wcs`` sections from your config to suppress the warning.

2. Secondly, more options are available for resource limiting in WCS. Refer to the documentation for details:

https://datacube-ows.readthedocs.io/en/latest/cfg_layers.html#resource-limits-wcs

Docker image base change
++++++++++++++++++++++++

The Docker images are now based on ``osgeo/gdal`` instead of ``opendatacube/geobase``. You may need to tweak
your build environment slightly - check your env files against the latest examples.

New in this release
+++++++++++++++++++

* Switch docker base image from geobase to osgeo/gdal. (#727)
* Remove support for wcs ``default_bands`` entry (# 725)
* Extend resource management capabilities for WCS (#730)
* Fixed several corner-case bugs in the color ramp legend generator (#732)
* Add chapter on legend generation to HOWTO (#733, #735)
* Added Security.md file (#734)
* Other improved documentation (#711)
* Fix bug affecting layers with no extent mask function. (#737, #739)
* Increment default version number to 1.8.20 (#738)

1.8.19 (2021-09-20)
-------------------

Improved test coverage and documentation; bug fixes; repo cleanup.

* Improved test coverage (#708, #709, #710)
* Fixed zero-day bug in WMTS GetFeatureInfo (#708)
* Improved pylint github action (thanks @pindge). (#713)
* Cleanup of requirements lists, and removal of old unused files. (#714)
* Fix platform-dependent numpy.typing import issue (thanks @alexgleith) (#718)
* Fix two WCS query interpretation bugs (#719)
* Documentation updates, including a cleanup of the README. (#720)
* Add support for ows_stats performance diagnostic tool to WMTS and WCS. (#721)
* Pin s3fs version in requirements.txt for compatibility with odc_tools (#722, #724)
* Increment version number (#723)


1.8.18 (2021-09-02)
-------------------

Adds support for dynamic credentials for S3 access.

Thanks to @woodcockr, @valpesendorfer and @pindge.

* Docker-compose fix for v1.29 (#702)
* Add smart resource management data to ows_stats output (#703)
* Renewable S3 credentials (#704, #706)
* Fix bug in direct config inheritance for objects supporting named inheritance (#705)
* Increment default version number (#707)


1.8.17 (2021-08-25)
-------------------

Urgent bug-fix release to address a WCS bug.

This release also contains a couple of minor backwards compatibility issues, see below for details.

Version 1.8.18 will probably follow fairly rapidly as there are a couple of other known issues that
are actively being worked on, see below for details.

Changes:
++++++++

* Cleanup/refactor of styles package: docstrings, type-hints, cleanup and improved test coverage (#695)
* Change default behaviour of ``$AWS_NO_SIGN_REQUEST`` to match the standard default behaviour for boto3-based applications (#696)
* Fix WCS queries against layers with a flag-band in the main product (#699)
* Increment version number (#700)

Backward Incompatibilities
++++++++++++++++++++++++++

1. #695 removed support for some legacy legend config formats that have been deprecated (and undocumented)
   for over a year.
2. #696 changes the default behaviour if ``$AWS_NO_SIGN_REQUEST`` is not set. Previously the default behaviour
   was unsigned requests, it is now signed requests. This was a necessary first-step to supporting dynamic
   credentials for S3 access, and brings OWS into line with other software using boto3 for S3 access.

Known Issues
++++++++++++

1. There are still issues with WCS queries against layers with a flag-band in the main product. These will be
   addressed in the next release and should not effect queries generated by the Terria Export function.
2. Dynamic credentialling for S3 access is still problematic. We have a PR almost ready to merge (#697) but
   it needs further testing.

1.8.16 (2021-08-16)
-------------------

Mostly about implementing smarter resource limiting to make time-series animation production ready.

* Smarter resource limiting (#686, #689, #690)
* docker-compose.yml fixes. (#685)
* Fix typo in ``.env_ows_root`` (#683)
* Remove "experimental" warning on time-series animations (#691)
* Better error reporting of config error cases potentially caused by easy-to-make typos (#692)
* Increment version number (#693)

Note the following changes to configuration introduced in this release. Old configurations should continue to work,
with the backwards-incompatible exceptions noted below, however you may see warning messages on startup advising
which parts of your config are now deprecated and should be updated.

1. ``native_crs`` and ``native_resolution`` were previously part of the ``wcs`` configuration section of layers,
   as they were previously only used for generating WCS metadata. They are now also used by the new
   ``min_zoom_level`` resource limit for WMS/WMTS, and have therefore moved out of the ``wcs`` section and into
   the main layer config section. These entries will continue to be read from the old location with a
   deprecation warning. If present in both locations, the values in the new locations take precedence, and
   the deprecation warning will still be raised.
2. There is a new ``min_zoom_level`` configuration option, which should be considerably easier to set and
   use than ``min_zoom_factor``, as well as being much smarter about how resource requirements for request
   are estimated. ``min_zoom_factor`` is still supported, but will be deprecated in a future release.

Backwards Incompatibility Notes

I try to avoid backwards incompatible changes to config format, but some minor ones were unavoidable in this release:

1. Layers with no CRS and/or resolution defined in the ODC product metadata now ALWAYS require a native CRS and resolution to be defined in configuration. This was previously only the case if WCS was enabled for the layer.
2. The default resource_limiting behaviour for WMS/WMTS has changed from "min_zoom_factor = 300.0" to "no resource limits". Maintaining backwards compatibility would have resulted in confusing and inconsistent behaviour.


1.8.15 (2021-07-30)
-------------------

1.8.15 introduces experimental* support for time-series animations from WMS/WMTS, in APNG format,
and has increased CI test coverage to over 90%.

If you use docker-compose to orchestrate your configuration, you may need to make some changes to
your ``.env`` file after upgrading to this release. See the updated examples and the documentation for details.

Thanks to all contributors, especially @whatnick for the prototype implementation of time-series animation,
and @alexgleith for supplying much needed user-feedback on the CLI interfaces.

(* experimental) = produces a warning message when activated. The existing resource limit implementation is
not suitable for production deployment with time-series animations. I hope to address this in the next release.

* Support for time-series animation APNG output for WMS and WMTS. (#656, #670, #678)
* User configurable WMS default time (#676)
* Code cleanup, starting to systematically add type hints and docstrings. (#660, #663, #664, #665, #671)
* CI enhancements (#662, #672, #674)
* datacube-ows-update changes to error handling to improve UX for maintainers. (#666, #679)
* Enhancements to config management in docker-compose. Note that if you use docker-compose, you may need to make some changes to your ``.env`` file. See the updated examples and the documentation for details. (#681)
* Release housekeeping, including incrementing default version number (#682)

1.8.14 (2021-07-09)
-------------------

* Default band names (as exposed by WCS) are now internationalisable (#651)
* Extent polygon rendering now uses rasterio rasterize, removing the dependency on scikit-image (#655)
* Calculating GeoTIFF statistics in WCS is now (globally) configurable (#654)
* Return an empty response if data for any requested dates is not available (#652)
* Bug fix - summary products (time_resolition not raw) were broken in areas close to 0 longitude. (e.g. Africa) (#657)
* Increment default version number (#658)

1.8.13 (2021-06-29)
-------------------

* Support for Regular Time Dimensions: Two independent requests for this behaviour have come from the user community. (#642)
* Fix for WCS2 band-aliasing bug (#645)
* Increment default version number (#647)

1.8.12 (2021-06-22)
-------------------

Documentation and API tweaks for the styling workshops at the 2021 ODC conference.

* Fix output aspect ratio when plotting from notebooks. (#369)
* Fixes to Styling HOWTO and JupyterHub Quick Start. (#641)
* Increment default version number to 1.8.12 (#640)


1.8.11 (2021-06-18)
-------------------

Bug Fix release.

* Multiproduct masking bugfix (#633)
* Better error reporting (#637)
* Documentation tweaks. (#632, #634, #645)
* Increment default version number (#636)

1.8.10 (2021-06-16)
-------------------

Mostly a bugfix release.

* plot_image functions added to styling API (e.g. for use in notebooks). (#619)
* Pass $AWS_S3_ENDPOINT through from calling environment to docker. (#622)
* Add dive for monitoring container size and contents (#626)
* Suppress confusing error messages when update_ranges is first run (#629)
* Bug fix (#620, #621,#623)
* Documentation corrections and enhancements. (#624,#625,#627,#630)
* Increment default version number to 1.8.10 (#631)

1.8.9 (2021-06-03)
------------------

New features:
+++++++++++++

* Optional separation of metadata from configuration and internationalisation (#587, #608, #609).
* Docker containers now run on Python 3.8 (#592, #598, #599, #602, #603, #604, #605, #606, #610, #612, #614).
* Bulk processing capabilities in Styling API (#595).
* Ability to load json config from S3 (disabled by default - enable with environment variable). (#591, #601)
* Misc bug-fixes and documentation updates (#611, #616, #617)

Repository Maintenance and Administrivia:
+++++++++++++++++++++++++++++++++++++++++

* Reduce redundant processing in Github Actions (#594).
* Add license headers and code-of-conduct. Improve documentation to meet OSGeo project requirements (#593)
* Make ows_cfg_example.py (more) valid. (#600)
* Increment version number (#618)

WARNING: Backwards incompatible change:
+++++++++++++++++++++++++++++++++++++++

* The old datacube-ows-cfg-parse CLI tool has been replaced by the check sub-command of the new, more general purpose datacube-ows-cfg CLI tool.


1.8.8 (2021-05-04)
------------------

New Features:
+++++++++++++

* Multidate ordering (#580)
* New "day_summary" time_resolution type, for data with summary-style time coordinates (as opposed to local solar-date style time coordinates). (#584)

Bug Fixes and Administrivia:
++++++++++++++++++++++++++++

* More thorough testing of styling engine (#578)
* Bug fixes (#579, #583)
* Upgrade pydevd version for debugging against Pycharm 2021.1.1 (#581)
* Repository security issue mediation (Codecov security breach) (#585)
* Increment version number (#586)

1.8.7 (2021-04-20)
------------------

* Includes support for user-defined band math (for colour ramp styles with matplotlib colour ramps). This is
  an experimental non-standard WMS extension that extends the WMS GetCapabilities document in the standard
  manner. The output validates against an XSD which is a valid extension of the WMS GetCapabilities schema.
  Backwards compatible extensions to GetMap allow the feature to be called by client software (#562, #563).
* If all goes to plan this will be the first OWS release automatically pushed to PyPI
  (#560, #568, #369, #570, #571, #572, #573, #574, #575, #576).
* Multi-product masking bug fix (#567). This was a serious bug affecting most multi-product masking use cases.
* Documentation updates (#561, #564)
* Version number increment to 1.8.7 (#577)

1.8.6 (2021-04-08)
------------------

* Enhanced documentation (including HOWTO Styling Guide). (#545, #551, #554, #555, #558)
* Stricter linting (#549, #550, #552, #557)
* Minor improvements to extent masking (#546)
* Miscellaneous bug fixes (#553, #556)

1.8.5 (2021-03-25)
------------------

First release to
PyPI: `https://pypi.org/project/datacube-ows/1.8.5/ <https://pypi.org/project/datacube-ows/1.8.5/>`_

* Date delta can now control subtraction direction from config (#535)
* New helper functions in standalone API (#538)
* Bug fixes in standalone API. (#542, #543)
* First draft of new "HOWTO" Styling guide. (#540, #543)
* Miscellaneous cleanup. (#533, #534, #537, #541)
* Prep for PyPI (#544)

1.8.4 (2021-03-19)
------------------

*    Standalone API for OWS styling. (#523)
*    Support for enumeration type bands in colour-map styles. (#529)
*    Numerous bugfixes.
*    Updated documentation.

1.8.3 (2021-03-12)
------------------

*    Generalised handling of WMTS tile matrix sets (#452)
*    Progressive cache control headers (#476)
*    Support for multi-product masking flags. (#499)
*    Greatly improved test coverage (various)
*    Many bug-fixes, documentation updates and minor enhancements (various)

1.8.2 (2020-10-26)
------------------

*    Config inheritance for layers and styles.
*    CRS aliases
*    Enhanced band util functions.
*    Query stats parameter.
*    Stand-alone config parsing/validating tool.
*    Cleaner internal APIs, improved test coverage, and bug fixes.

1.8.1 (2020-08-18)
------------------

* Bug fixes
* Performance enhancements - most notable using materialised views for spatio-temporal DB searches.
* Improved testing and documentation.

1.8.0 (2020-06-10)
------------------

* Synchronise minor version number with datacube-core.
* Materialised spatio-temporal views for ranges.
* WCS2 support.

Incomplete list of pre-1.8 releases.
====================================

Prior to 1.8.0 the release process was informal and ad hoc.

0.8.1 (2019-01-10)
------------------

* Reconcile package version number with git managed version number

0.2.0 (2019-01-09)
------------------

* Establishing proper versioning
* WMS, WMTS, WCS support

0.1.0 (2017-02-24)
------------------

* First release on (DEA internal) PyPI.
