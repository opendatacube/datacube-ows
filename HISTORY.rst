=======
History
=======

0.1.0 (2017-02-24)
------------------

* First release on PyPI.

0.2.0 (2019-01-09)
------------------

* Establishing proper versioning
* WMS, WMTS, WCS support

0.8.1 (2019-01-10)
------------------

* Reconcile package version number with git managed version number

1.8.0 (2020-06-10)
------------------

* Synchronise minor version number with datacube-core.
* Materialised spatio-temporal views for ranges.
* WCS2 support.

1.8.1 (2020-08-18)
------------------

* Bug fixes
* Performance enhancements - most notable using materialised views for spatio-temporal DB searches.
* Improved testing and documentation.


1.8.2 (2020-10-26)
------------------

*    Config inheritance for layers and styles.
*    CRS aliases
*    Enhanced band util functions.
*    Query stats parameter.
*    Stand-alone config parsing/validating tool.
*    Cleaner internal APIs, improved test coverage, and bug fixes.


1.8.3 (2021-03-12)
------------------

*    Generalised handling of WMTS tile matrix sets (#452)
*    Progressive cache control headers (#476)
*    Support for multi-product masking flags. (#499)
*    Greatly improved test coverage (various)
*    Many bug-fixes, documentation updates and minor enhancements (various)


1.8.4 (2021-03-19)
------------------

*    Standalone API for OWS styling. (#523)
*    Support for enumeration type bands in colour-map styles. (#529)
*    Numerous bugfixes.
*    Updated documentation.

1.8.5 (2021-03-25)
------------------

* Date delta can now control subtraction direction from config (#535)
* New helper functions in standalone API (#538)
* Bug fixes in standalone API. (#542, #543)
* First draft of new "HOWTO" Styling guide. (#540, #543)
* Miscellaneous cleanup. (#533, #534, #537, #541)
* Prep for PyPI (#544)
