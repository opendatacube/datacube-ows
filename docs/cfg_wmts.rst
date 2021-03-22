================================
OWS Configuration - WMTS Section
================================

.. contents:: Table of Contents

WMTS Section
------------

The "wmts" section of the `root configuration object
<https://datacube-ows.readthedocs.io/en/latest/configuration.html>`_
contains config entries that apply only to WMTS service for all layers.

Note that the `wms <https://datacube-ows.readthedocs.io/en/latest/cfg_wms.html>`_ section
also contains configuration that applies to the WMTS service.

All entries in the WMTS section are optional and the entire section can therefore be omitted.

Tile Matrix Sets (tile_matrix_sets)
===================================

A Tile Matrix Set is a way of breaking down a map into a standardised set
of tiles at a number of different zoom levels.  For further details, refer
to the `WMTS specification <http://portal.opengeospatial.org/files/?artifact_id=35326>`_.

Datacube_ows always supports the de-facto standard Google-Maps compatible
EPSG:3857-based tile matrix - you do not need to explicitly define it
in configuration.

The tile_matrix_sets entry is a dictionary mapping WMTS tile matrix set
identifiers to a tile matrix set definition.

The default value is an empty dictionary, which means ONLY the Google-style
WholeWorld_WebMercator tile matrix set will be offered by the WMTS service.

---------------------------------
Defining a custom tile matrix set
---------------------------------

The Identifier
++++++++++++++

The identifier for a tile matrix set should be a unique identifier-like string. The
identifier is the key in the tile_matrix_set dictionary.

CRS (crs)
+++++++++

The "crs" element of the tile matrix set definition is required and must
be the name or alias of a
`published CRS <https://datacube-ows.readthedocs.io/en/latest/cfg_global.html#co-ordinate-reference-systems-published-crss>`_.

Matrix Origin (matrix_origin)
+++++++++++++++++++++++++++++

The matrix origin element is required and must be a list of two floats,
representing the coordinates in the specified CRS of the top-left corner
of the tile matrix set. The horizontal coordinate should always be specified
first here, regardless of the coordinate order convention of the CRS.

Tile Size (tile_size)
+++++++++++++++++++++

The tile size element is required and must be a list of two ints,
representing the width and height respectively of a tile in pixels
in the tile matrix set.

The tile size must be valid according to the max_width and max_height
configuration in the wms section.

Scale Set (scale_set)
+++++++++++++++++++++

The scale set configuration is required and must be a list of floats
representing the scale denominators for each zoom level.  Refer to the
WMTS spec for more details.

Well Known Scale Set (wkss)
+++++++++++++++++++++++++++

wkss is optional, and if supplied should be a string containing
a well known URN for the tile matrix set.

E.g. the wkss for the default Google tile matrix set is
"urn:ogc:def:wkss:OGC:1.0:GoogleMapsCompatible".

Force Raw CRS Name (force_raw_crs_name)
+++++++++++++++++++++++++++++++++++++++

force_raw_crs_name is optional, defaults to False, and if supplied should be a
boolean.

If True, the CRS for the Tile Matrix Set is published in GetCapabilities
exactly as it appears in the configuration.  If False, EPSG CRSs are published
in GetCapabilities as a URN.  (E.g. "urn:ogc:def:crs:EPSG::3857")

Initial Offsets for Matrix Exponents (matrix_exponent_initial_offsets)
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Datacube OWS offers only minimal control over the number of tiles available
at each zoom level.

The default behaviour is to have a single tile for tile matrix 0,
four tiles (2x2) at tile matrix 1, and generally 2**n by 2**n tiles at
tile matrix n.

To override this behaviour a pair of integer exponent offsets can be
supplied in the matrix_exponent_initial_offsets element. The offset
for the horizontal dimension comes first.

The default behaviour is represented by setting both offsets to zero.

A positive offset represents the number of tiles along the relevant dimension
in tile matrix 0.  E.g. there would be 2**(n+offset) tiles along the relevant
dimension in tile matrix n.

A negative offset is interpreted similarly, except if the number of tiles along
a dimension would be less than 1, it is capped to 1.

E.g.:

Offset = 0:
number of tiles along dimension: 1, 2, 4, 8, 16, ...

Offset = 2:
number of tiles along dimension: 4, 8, 16, 32

Offset = -2:
number of tiles along dimension: 1, 1, 1, 2, 4, 8, 16, ....

Unit Coefficients (unit_coefficients)
+++++++++++++++++++++++++++++++++++++

The unit_coefficients elements captures two important factors for converting between tile
row/column numbers and CRS coordinates.  It is optional and should be a list of
two floats, defaulting to (1.0, -1.0).

The first coefficient in the list is associated with horizontal axis and the second with
the vertical axis.

The magnitude of the unit coefficient is the number of nominal metres per CRS coordinate
unit.  For CRSs calibrated in metres (e.g. northings/eastings), this will be 1.0.

The sign of the unit coefficient represents any transformation required to get from
the coordinate direction conventions of the CRS to direction conventions of WMTS, which
are:

* Horizontal coordinate increases from left to right.
* Vertical coordinate increases from top to bottom.

E.g. EPSG:3857 which is calibrating in metres northing and easting requires
the default unit coefficients (1, -1).  The -1 is to convert northings, which
increase from south to north to image coordinates with north pointing upwards.


E.g.

::

    "wmts": {
        "tile_matrix_sets": {
            # VicGrid Geo-Cortex-compatible tile matrix set
            "VicGrid": {
                "crs": "EPSG:3111",
                "matrix_origin": (1786000.0, 3081000.0),
                "tile_size": (512, 512),
                "scale_set": [
                    7559538.928601667,
                    3779769.4643008336,
                    1889884.7321504168,
                    944942.3660752084,
                    472471.1830376042,
                    236235.5915188021,
                    94494.23660752083,
                    47247.11830376041,
                    23623.559151880207,
                    9449.423660752083,
                    4724.711830376042,
                    2362.355915188021,
                    1181.1779575940104,
                    755.9538928601667,
                ],
                "matrix_exponent_initial_offsets": (1, 0),
            },
        }
    }
