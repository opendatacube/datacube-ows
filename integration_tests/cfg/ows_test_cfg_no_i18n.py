# pylint: skip-file
# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
# SPDX-License-Identifier: Apache-2.0


# THIS IS A TESTING FILE
# Please refer to datacube_ows/ows_cfg_example.py for EXAMPLE CONFIG

# REUSABLE CONFIG FRAGMENTS - Band alias maps
ls8_usgs_level1_bands = {
    "coastal_aerosol": ["band_1"],
    "blue": ["band_2"],
    "green": ["band_3", "green"],
    "red": ["band_4", "pink"],
    "nir": ["nir", "band_5"],
    "swir1": ["band_6"],
    "swir2": ["band_7"],
    "panchromatic": ["band_8"],
    "cirrus": ["band_9"],
    "lwir1": ["band_10"],
    "lwir2": ["band_11"],
    "quality": ["QUALITY"],
}

bands_fc = {
    "BS": ["bare_soil"],
    "PV": ["photosynthetic_vegetation", "green_vegetation"],
    "NPV": ["non_photosynthetic_vegetation", "brown_vegetation"],
}

bands_wofs_obs = {
    "water": [],
}


# REUSABLE CONFIG FRAGMENTS - Style definitions
# Examples of styles which are linear combinations of the available spectral bands.
style_rgb = {
    # Machine readable style name. (required.  Must be unique within a layer.)
    "name": "simple_rgb",
    # Human readable style title (required.  Must be unique within a layer.)
    "title": "Simple RGB",
    # Abstract - a longer human readable style description. (required. Must be unique within a layer.)
    "abstract": "Simple true-colour image, using the red, green and blue bands",
    # Components section is required for linear combination styles.
    # The component keys MUST be "red", "green" and "blue" (and optionally "alpha")
    "components": {
        "red": {
            # Band aliases may be used here.
            # Values are multipliers.  The should add to 1.0 for each component to preserve overall brightness levels,
            # but this is not enforced.
            "pink": 1.0
        },
        "green": {"green": 1.0},
        "blue": {"blue": 1.0},
    },
    # The raw band value range to be compressed to an 8 bit range for the output image tiles.
    # Band values outside this range are clipped to 0 or 255 as appropriate.
    "scale_range": [0.0, 65535.0],
}

style_rgb_clone = {
    "inherits": {"layer": "ls8_usgs_level1_scene_layer", "style": "simple_rgb"},
    "name": "simple_rgb_clone",
    "title": "Simple RGB Clone",
    "scale_range": [0.0, 20000.0],
}

style_infrared_false_colour = {
    "name": "infra_red",
    "title": "False colour multi-band infra-red",
    "abstract": "Simple false-colour image, using the near and short-wave infra-red bands",
    "components": {
        "red": {
            "swir1": 1.0,
            # The special dictionary value 'scale_range' can be used to provide a component-specific
            # scale_range that overrides the style scale_range below.
            # (N.B. if you are unlucky enough to have a native band called "scale_range", you can access it
            # by defining a band alias.)
            "scale_range": [5.0, 4000.0],
        },
        "green": {
            "swir2": 1.0,
            "scale_range": [25.0, 4000.0],
        },
        "blue": {
            "nir": 1.0,
            "scale_range": [0.0, 3000.0],
        },
    },
    # The style scale_range can be omitted if all components have a component-specific scale_range defined.
    # "scale_range": [0.0, 3000.0]
}


style_pure_ls8_blue = {
    "name": "blue",
    "title": "Spectral band 2 - Blue",
    "abstract": "Blue band, approximately 453nm to 511nm",
    "components": {"red": {"blue": 1.0}, "green": {"blue": 1.0}, "blue": {"blue": 1.0}},
    "scale_range": [0.0, 65535.0],
}

# Examples of non-linear colour-ramped styles.
style_ndvi = {
    "name": "ndvi",
    "title": "NDVI",
    "abstract": "Normalised Difference Vegetation Index - a derived index that correlates well with the existence of vegetation",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "mapped_bands": True,
        "kwargs": {"band1": "nir", "band2": "red"},
    },
    # List of bands used by this style. The band may not be passed to the index function if it is not declared
    # here, resulting in an error.  Band aliases can be used here.
    "needed_bands": ["red", "nir"],
    # The color ramp. Values between specified entries have both their alphas and colours
    # interpolated.
    "color_ramp": [
        # Any value less than the first entry will have colour and alpha of the first entry.
        # (i.e. in this example all negative values will be fully transparent (alpha=0.0).)
        {"value": -0.0, "color": "#8F3F20", "alpha": 0.0},
        {"value": 0.0, "color": "#8F3F20", "alpha": 1.0},
        {
            # do not have to defined alpha value
            # if no alpha is specified, alpha will default to 1.0 (fully opaque)
            "value": 0.1,
            "color": "#A35F18",
        },
        {"value": 0.2, "color": "#B88512"},
        {"value": 0.3, "color": "#CEAC0E"},
        {"value": 0.4, "color": "#E5D609"},
        {"value": 0.5, "color": "#FFFF0C"},
        {"value": 0.6, "color": "#C3DE09"},
        {"value": 0.7, "color": "#88B808"},
        {"value": 0.8, "color": "#529400"},
        {"value": 0.9, "color": "#237100"},
        # Values greater than the last entry will use the colour and alpha of the last entry.
        # (N.B. This will not happen for this example because it is normalised so that 1.0 is
        # maximum possible value.)
        {"value": 1.0, "color": "#114D04"},
    ],
    # If true, the calculated index value for the pixel will be included in GetFeatureInfo responses.
    # Defaults to True.
    "include_in_feature_info": True,
}

# Examples of non-linear colour-ramped style with multi-date support.
style_ndvi_delta = {
    "name": "ndvi_delta",
    "title": "NDVI Delta",
    "abstract": "Normalised Difference Vegetation Index - with delta support",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "mapped_bands": True,
        "kwargs": {"band1": "nir", "band2": "red"},
    },
    "needed_bands": ["red", "nir"],
    # The color ramp for single-date requests - same as ndvi style example above
    "color_ramp": [
        {"value": -0.0, "color": "#8F3F20", "alpha": 0.0},
        {"value": 0.0, "color": "#8F3F20", "alpha": 1.0},
        {"value": 0.1, "color": "#A35F18"},
        {"value": 0.2, "color": "#B88512"},
        {"value": 0.3, "color": "#CEAC0E"},
        {"value": 0.4, "color": "#E5D609"},
        {"value": 0.5, "color": "#FFFF0C"},
        {"value": 0.6, "color": "#C3DE09"},
        {"value": 0.7, "color": "#88B808"},
        {"value": 0.8, "color": "#529400"},
        {"value": 0.9, "color": "#237100"},
        {"value": 1.0, "color": "#114D04"},
    ],
    "include_in_feature_info": True,
    "legend": {
        "show_legend": True,
    },
    # Define behaviour(s) for multi-date requests. If not declared, style only supports single-date requests.
    "multi_date": [
        # A multi-date handler.  Different handlers can be declared for different numbers of dates in a request.
        {
            # The count range for which this handler is to be used - a tuple of two ints, the smallest and
            # largest date counts for which this handler will be used.  Required.
            "allowed_count_range": [2, 2],
            # A function, expressed in the standard format as described elsewhere in this example file.
            # The function is assumed to take one arguments, an xarray Dataset.
            # The function returns an xarray Dataset with a single band, which is the input to the
            # colour ramp defined below.
            "aggregator_function": {
                "function": "datacube_ows.band_utils.multi_date_delta"
            },
            # The multi-date color ramp.  May be defined as an explicit colour ramp, as shown above for the single
            # date case; or may be defined with a range and unscaled color ramp as shown here.
            #
            # The range specifies the min and max values for the color ramp.  Required if an explicit color
            # ramp is not defined.
            "range": [-1.0, 1.0],
            # The name of a named matplotlib color ramp.
            # Reference here: https://matplotlib.org/examples/color/colormaps_reference.html
            # Only used if an explicit colour ramp is not defined.  Optional - defaults to a simple (but
            # kind of ugly) blue-to-red rainbow ramp.
            "mpl_ramp": "RdBu",
            # The feature info label for the multi-date index value.
            "feature_info_label": "ndvi_delta",
        }
    ],
}


# Hybrid style - blends a linear mapping and an colour-ramped index style
# There is no scientific justification for these styles, I just think they look cool.  :)
style_rgb_ndvi = {
    "name": "rgb_ndvi",
    "title": "NDVI plus RGB",
    "abstract": "Normalised Difference Vegetation Index (blended with RGB) - a derived index that correlates well with the existence of vegetation",
    # Mixing ration between linear components and colour ramped index. 1.0 is fully linear components, 0.0 is fully colour ramp.
    "component_ratio": 0.6,
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "mapped_bands": True,
        "kwargs": {"band1": "nir", "band2": "red"},
    },
    "needed_bands": ["red", "nir"],
    "range": [0.0, 1.0],
    "components": {"red": {"red": 1.0}, "green": {"green": 1.0}, "blue": {"blue": 1.0}},
    "scale_range": [0.0, 65535.0],
    # N.B. The "pq_mask" section works the same as for the style types above.
}
style_ls_simple_rgb = {
    "name": "simple_rgb",
    "title": "Simple RGB",
    "abstract": "Simple true-colour image, using the red, green and blue bands",
    "components": {"red": {"red": 1.0}, "green": {"green": 1.0}, "blue": {"blue": 1.0}},
    "scale_range": [0.0, 3000.0],
}

style_fc_simple = {
    "name": "simple_fc",
    "title": "Fractional Cover",
    "abstract": "Fractional cover representation, with green vegetation in green, dead vegetation in blue, and bare soil in red",
    "components": {"red": {"BS": 1.0}, "green": {"PV": 1.0}, "blue": {"NPV": 1.0}},
    "scale_range": [0.0, 100.0],
    "pq_masks": [
        {
            "band": "water",
            "flags": {"dry": True},
        },
        {
            "band": "water",
            "flags": {
                "terrain_or_low_angle": False,
                "high_slope": False,
                "cloud_shadow": False,
                "cloud": False,
                "sea": False,
            },
        },
    ],
}

style_wofs_obs = {
    "name": "observations",
    "title": "Observations",
    "abstract": "Observations",
    "value_map": {
        "water": [
            {
                # Make noncontiguous data transparent
                "title": "",
                "abstract": "",
                "flags": {"noncontiguous": True},
                "alpha": 0.0,
                "color": "#ffffff",
            },
            {
                # Make sea and sea glint transparent
                "title": "",
                "abstract": "",
                "flags": {"sea": True},
                "alpha": 0.0,
                "color": "#4f81bd",
            },
            {
                "title": "Cloudy Steep Terrain",
                "abstract": "",
                "flags": {"and": {"high_slope": True, "cloud": True}},
                "color": "#f2dcb4",
            },
            {
                "title": "Cloudy Water",
                "abstract": "",
                "flags": {"and": {"wet": True, "cloud": True}},
                "color": "#bad4f2",
            },
            {
                "title": "Shaded Water",
                "abstract": "",
                "flags": {"and": {"wet": True, "cloud_shadow": True}},
                "color": "#335277",
            },
            {
                "title": "Cloud",
                "abstract": "",
                "flags": {"cloud": True},
                "color": "#c2c1c0",
            },
            {
                "title": "Cloud Shadow",
                "abstract": "",
                "flags": {"cloud_shadow": True},
                "color": "#4b4b37",
            },
            {
                "title": "Terrain Shadow or Low Sun Angle",
                "abstract": "",
                "flags": {"terrain_or_low_angle": True},
                "color": "#2f2922",
            },
            {
                "title": "Steep Terrain",
                "abstract": "",
                "flags": {"high_slope": True},
                "color": "#776857",
            },
            {
                "title": "Water",
                "abstract": "",
                "flags": {"and": {"wet": True, "sea": False}},
                "color": "#4f81bd",
            },
            {
                "title": "Dry",
                "abstract": "",
                "flags": {"and": {"dry": True, "sea": False}},
                "color": "#96966e",
            },
        ]
    },
    "legend": {"width": 3.0, "height": 2.1},
}

style_wofs_obs_wet_only = {
    "name": "wet",
    "title": "Wet Only",
    "abstract": "Wet Only",
    "value_map": {
        "water": [
            {
                "title": "Invalid",
                "abstract": "Slope or Cloud",
                "flags": {
                    "or": {
                        "terrain_or_low_angle": True,
                        "cloud_shadow": True,
                        "cloud": True,
                        "high_slope": True,
                        "noncontiguous": True,
                    }
                },
                "color": "#707070",
                "alpha": 0.0,
            },
            {
                # Possible Sea Glint, also mark as invalid
                "title": "",
                "abstract": "",
                "flags": {"dry": True, "sea": True},
                "color": "#707070",
                "alpha": 0.0,
            },
            {
                "title": "Dry",
                "abstract": "Dry",
                "flags": {
                    "dry": True,
                    "sea": False,
                },
                "color": "#D99694",
                "alpha": 0.0,
            },
            {
                "title": "Wet",
                "abstract": "Wet or Sea",
                "flags": {"or": {"wet": True, "sea": True}},
                "color": "#4F81BD",
            },
        ]
    },
}

# Describes a style which uses several bitflags to create a style

# REUSABLE CONFIG FRAGMENTS - resource limit declarations

standard_resource_limits = {
    "wms": {
        "zoomed_out_fill_colour": [150, 180, 200, 160],
        "min_zoom_factor": 35.0,
        "max_datasets": 16,  # Defaults to no dataset limit
    },
    "wcs": {
        # "max_datasets": 16, # Defaults to no dataset limit
    },
}


reslim_aster = {
    "wms": {
        "zoomed_out_fill_colour": [150, 180, 200, 160],
        "min_zoom_factor": 10.0,
        # "max_datasets": 16, # Defaults to no dataset limit
    },
    "wcs": {
        # "max_datasets": 16, # Defaults to no dataset limit
    },
}

reslim_wofs_obs = standard_resource_limits

# MAIN CONFIGURATION OBJECT

ows_cfg = {
    # Config entries in the "global" section apply to all services and all layers/coverages
    "global": {
        # These HTML headers are added to all responses
        # Optional, default {} - no added headers
        "response_headers": {
            "Access-Control-Allow-Origin": "*",  # CORS header (strongly recommended)
        },
        # Which web service(s) should be implemented by this instance
        # Optional, defaults: wms,wmts: True, wcs: False
        "services": {"wms": True, "wmts": True, "wcs": True},
        # Service title - appears e.g. in Terria catalog (required)
        "title": "Open web-services for the Open Data Cube",
        # Service URL.
        # A list of fully qualified URLs that the service can return
        # in the GetCapabilities documents based on the requesting url
        "allowed_urls": [
            "http://127.0.0.1:5000/",
            "http://127.0.0.1:8000/",
            "http://localhost/odc_ows",
            "https://localhost/odc_ows",
            "https://alternateurl.domain.org/odc_ows",
        ],
        # URL that humans can visit to learn more about the service(s) or organization
        # should be fully qualified
        "info_url": "http://opendatacube.org",
        # Abstract - longer description of the service (Note this text is used for both WM(T)S and WCS)
        # Optional - defaults to empty string.
        "abstract": """This web-service serves georectified raster data from our very own special Open Datacube instance.""",
        # Keywords included for all services and products
        # Optional - defaults to empty list.
        "keywords": [
            "satellite",
            "australia",
            "time-series",
        ],
        # Contact info.
        # Optional but strongly recommended - defaults to blank.
        "contact_info": {
            "person": "Firstname Surname",
            "organisation": "Acme Corporation",
            "position": "CIO (Chief Imaginary Officer)",
            "address": {
                "type": "postal",
                "address": "GPO Box 999",
                "city": "Metropolis",
                "state": "North Arcadia",
                "postcode": "12345",
                "country": "Elbonia",
            },
            "telephone": "+61 2 1234 5678",
            "fax": "+61 2 1234 6789",
            "email": "test@example.com",
        },
        # If fees are charged for the use of the service, these can be described here in free text.
        # If blank or not included, defaults to "none".
        "fees": "",
        # If there are constraints on access to the service, they can be described here in free text.
        # If blank or not included, defaults to "none".
        "access_constraints": "",
        # Attribution. This provides a way to identify the source of the data used in a layer or layers.
        # This entire section is optional.  If provided, it is taken as the
        # default attribution for any layer that does not override it.
        "attribution": {
            # Attribution must contain at least one of ("title", "url" and "logo")
            # A human readable title for the attribution - e.g. the name of the attributed organisation
            "title": "Acme Satellites",
            # The associated - e.g. URL for the attributed organisation
            "url": "http://www.acme.com/satellites",
            # Logo image - e.g. for the attributed organisation
            "logo": {
                # Image width in pixels (optional)
                "width": 370,
                # Image height in pixels (optional)
                "height": 73,
                # URL for the logo image. (required if logo specified)
                "url": "https://www.acme.com/satellites/images/acme-370x73.png",
                # Image MIME type for the logo - should match type referenced in the logo url (required if logo specified.)
                "format": "image/png",
            },
        },
        # Supported co-ordinate reference systems. Any coordinate system supported by GDAL and Proj.4J can be used.
        # At least one CRS must be included.  At least one geographic CRS must be included if WCS is active.
        # Web Mercator (EPSG:3857) and WGS-84 (EPSG:4326) are strongly recommended, but not required.
        "published_CRSs": {
            "EPSG:3857": {  # Web Mercator
                "geographic": False,
                "horizontal_coord": "x",
                "vertical_coord": "y",
            },
            "EPSG:4326": {"geographic": True, "vertical_coord_first": True},  # WGS-84
            "I-CANT-BELIEVE-ITS-NOT-EPSG:4326": {"alias": "EPSG:4326"},
            "EPSG:3577": {  # GDA-94, internal representation
                "geographic": False,
                "horizontal_coord": "x",
                "vertical_coord": "y",
            },
        },
        # If True the new EXPERIMENTAL materialised views are used for spatio-temporal extents.
        # If False (the default), the old "update_ranges" tables (and native ODC search methods) are used.
        # DO NOT SET THIS TO TRUE unless you understand what this means and want to participate
        # in the experiment!
        "use_extent_views": False,
    },  #### End of "global" section.
    # Config items in the "wms" section apply to the WMS service (and WMTS, which is implemented as a
    # thin wrapper to the WMS code unless stated otherwise) to all WMS/WMTS layers (unless over-ridden).
    "wms": {
        # Provide S3 data URL, bucket name for data_links in GetFeatureinfo responses
        # Note that this feature is currently restricted to data stored in AWS S3.
        # This feature is also fairly specialised to DEA requirements and may not be suited to more general use.
        # All Optional
        "s3_url": "http://data.au",
        "s3_bucket": "s3_bucket_name",
        "s3_aws_zone": "ap-southeast-2",
        "user_band_math_extension": True,
        # Max tile height/width for wms.  (N.B. Does not apply to WMTS)
        # Optional, defaults to 256x256
        "max_width": 512,
        "max_height": 512,

        # These define the AuthorityURLs.
        # They represent the authorities that define the "Identifiers" defined layer by layer below.
        # The spec allows AuthorityURLs to be defined anywhere on the Layer heirarchy, but datacube_ows treats them
        # as global entities.
        # Required if identifiers are to be declared for any layer.
        "authorities": {
            # The authorities dictionary maps names to authority urls.
            "auth": "https://authoritative-authority.com",
            "idsrus": "https://www.identifiers-r-us.com",
        },
    },  ####  End of "wms" section.
    # Config items in the "wcs" section apply to the WCS service to all WCS coverages
    # (unless over-ridden).
    "wcs": {
        # Must be a geographic CRS in the global published_CRSs list.
        # EPSG:4326 is recommended, but any geographic CRS should work.
        "default_geographic_CRS": "EPSG:4326",
        # Supported WCS formats
        # NetCDF and GeoTIFF work "out of the box".  Other formats will require writing a Python function
        # to do the rendering.
        "formats": {
            # Key is the format name, as used in DescribeCoverage XML
            "GeoTIFF": {
                # Renderer is the FQN of a Python function that takes:
                #   * A WCSRequest object
                #   * Some ODC data to be rendered.
                "renderers": {
                    "1": "datacube_ows.wcs1_utils.get_tiff",
                    "2": "datacube_ows.wcs2_utils.get_tiff",
                },
                # The MIME type of the image, as used in the Http Response.
                "mime": "image/geotiff",
                # The file extension to add to the filename.
                "extension": "tif",
                # Whether or not the file format supports multiple time slices.
                "multi-time": False,
            },
            "netCDF": {
                "renderers": {
                    "1": "datacube_ows.wcs1_utils.get_netcdf",
                    "2": "datacube_ows.wcs2_utils.get_netcdf",
                },
                "mime": "application/x-netcdf",
                "extension": "nc",
                "multi-time": True,
            },
        },
        # The wcs:native_format must be declared in wcs:formats dict above.
        "native_format": "GeoTIFF",
    },  ###### End of "wcs" section
    # Products published by this datacube_ows instance.
    # The layers section is a list of layer definitions.  Each layer may be either:
    # 1) A folder-layer.  Folder-layers are not named and can contain a list of child layers.  Folder-layers are
    #    only used by WMS and WMTS - WCS does not support a hierarchical index of coverages.
    # 2) A mappable named layer that can be requested in WMS GetMap or WMTS GetTile requests.  A mappable named layer
    #    is also a coverage, that may be requested in WCS DescribeCoverage or WCS GetCoverage requests.
    "layers": [
        {
            "title": "Landsat",
            "abstract": "Images from the Landsat satellite",
            "keywords": ["landsat", "landsat8", "landsat7"],
            "attribution": {
                # Attribution must contain at least one of ("title", "url" and "logo")
                # A human readable title for the attribution - e.g. the name of the attributed organisation
                "title": "Open Data Cube - OWS",
                # The associated - e.g. URL for the attributed organisation
                "url": "https://www.opendatacube.org/",
                # Logo image - e.g. for the attributed organisation
                "logo": {
                    # Image width in pixels (optional)
                    "width": 268,
                    # Image height in pixels (optional)
                    "height": 68,
                    # URL for the logo image. (required if logo specified)
                    "url": "https://static.wixstatic.com/media/8959d6_98a1d74703d946ecab030b32f53db883~mv2.png/v1/fill/w_268,h_68,al_c,q_85,usm_0.66_1.00_0.01/f9d4ea_7a2d1d0c69ad4da0a2f48b69bc481612_.webp",
                    # Image MIME type for the logo - should match type referenced in the logo url (required if logo specified.)
                    "format": "image/png",
                },
            },
            "label": "landsat",
            "layers": [
                {
                    # NOTE: This layer IS a mappable "named layer" that can be selected in GetMap requests
                    "title": "Level 1 USGS Landsat-8 Public Data Set",
                    "abstract": "Imagery from the Level 1 Landsat-8 USGS Public Data Set",
                    "name": "ls8_usgs_level1_scene_layer",
                    "product_name": "ls8_usgs_level1_scene",
                    "user_band_math": True,
                    "bands": ls8_usgs_level1_bands,
                    "resource_limits": standard_resource_limits,
                    "flags": [
                        {
                            "band": "quality",
                            "ignore_time": False,
                            "ignore_info_flags": [],
                            "manual_merge": True,
                        },
                    ],
                    "image_processing": {
                        # Extent mask function
                        #
                        # See documentation above.  This is an example of multiple extent_mask_functions.
                        "extent_mask_func": [
                            "datacube_ows.ogc_utils.mask_by_quality",
                            "datacube_ows.ogc_utils.mask_by_val",
                        ],
                        # Bands to always fetch from the Datacube, even if it is not used by the active style.
                        # Useful for when a particular band is always needed for the extent_mask_func, as
                        # is the case here.
                        "always_fetch_bands": ["quality"],
                        "fuse_func": None,
                        "manual_merge": True,
                        # Apply corrections for solar angle, for "Level 1" products.
                        # (Defaults to false - should not be used for NBAR/NBAR-T or other Analysis Ready products
                        "apply_solar_corrections": True,
                    },
                    "wcs": {
                        "native_crs": "EPSG:4326",
                        "native_resolution": [0.000225, 0.000225],
                        "default_bands": ["red", "green", "blue"],
                    },
                    "styling": {
                        "default_style": "simple_rgb",
                        "styles": [
                            style_rgb,
                            style_rgb_clone,
                            style_infrared_false_colour,
                            style_pure_ls8_blue,
                            style_ndvi,
                            style_ndvi_delta,
                            style_rgb_ndvi,
                        ],
                    },
                },  ##### End of ls8_level1_pds product definition.
                {
                    "inherits": {
                        "layer": "ls8_usgs_level1_scene_layer",
                    },
                    "title": "Level 1 USGS Landsat-8 Public Data Set Clone",
                    "abstract": "Imagery from the Level 1 Landsat-8 USGS Public Data Set Clone",
                    "name": "ls8_usgs_level1_scene_layer_clone",
                },
            ],
        },  ### End of Landsat folder.
        {
            "title": "Fractional Cover",
            "abstract": """
Fractional Cover version 2.2.1, 25 metre, 100km tile, Australian Albers Equal Area projection (EPSG:3577). Data is only visible at higher resolutions; when zoomed-out the available area will be displayed as a shaded region.
Fractional cover provides information about the the proportions of green vegetation, non-green vegetation (including deciduous trees during autumn, dry grass, etc.), and bare areas for every 25m x 25m ground footprint. Fractional cover provides insight into how areas of dry vegetation and/or bare soil and green vegetation are changing over time. The fractional cover algorithm was developed by the Joint Remote Sensing Research Program, for more information please see data.auscover.org.au/xwiki/bin/view/Product+pages/Landsat+Fractional+Cover
Fractional Cover products use Water Observations from Space (WOfS) to mask out areas of water, cloud and other phenomena. To be considered in the FCP product a pixel must have had at least 10 clear observations over the year.
For service status information, see https://status.dea.ga.gov.au
""",
            "label": "fc",
            "layers": [
                {
                    "title": "Fractional Cover 25m 100km tile (Fractional Cover Landsat 5)",
                    "name": "ls5_fc_albers",
                    "abstract": """
Fractional Cover version 2.2.1, 25 metre, 100km tile, Australian Albers Equal Area projection (EPSG:3577). Data is only visible at higher resolutions; when zoomed-out the available area will be displayed as a shaded region.
Fractional cover provides information about the the proportions of green vegetation, non-green vegetation (including deciduous trees during autumn, dry grass, etc.), and bare areas for every 25m x 25m ground footprint. Fractional cover provides insight into how areas of dry vegetation and/or bare soil and green vegetation are changing over time. The fractional cover algorithm was developed by the Joint Remote Sensing Research Program, for more information please see data.auscover.org.au/xwiki/bin/view/Product+pages/Landsat+Fractional+Cover
Fractional Cover products use Water Observations from Space (WOfS) to mask out areas of water, cloud and other phenomena.
This product contains Fractional Cover dervied from the Landsat 5 satellite
For service status information, see https://status.dea.ga.gov.au
""",
                    "product_name": "ls5_fc_albers",
                    "bands": bands_fc,
                    "resource_limits": reslim_aster,
                    "image_processing": {
                        "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                        "always_fetch_bands": [],
                        "manual_merge": False,
                    },
                    "flags": [
                        {
                            "band": "water",
                            "product": "wofs_albers",
                            "ignore_time": False,
                            "ignore_info_flags": [],
                            "fuse_func": "datacube_ows.wms_utils.wofls_fuser",
                        },
                    ],
                    "wcs": {
                        "native_crs": "EPSG:3577",
                        "default_bands": ["BS", "PV", "NPV"],
                        "native_resolution": [25, -25],
                    },
                    "styling": {
                        "default_style": "simple_fc",
                        "styles": [
                            style_fc_simple,
                        ],
                    },
                },
                {
                    "title": "Water Observations from Space 25m albers (WOfS Daily Observations)",
                    "name": "wofs_albers",
                    "abstract": """
Water Observations from Space (WOfS) provides surface water observations derived from satellite imagery for all of Australia. The current product (Version 2.1.5) includes observations taken from 1986 to the present, from the Landsat 5, 7 and 8 satellites. WOfS covers all of mainland Australia and Tasmania but excludes off-shore Territories.
The WOfS product allows users to get a better understanding of where water is normally present in a landscape, where water is seldom observed, and where inundation has occurred occasionally.
Data is provided as Water Observation Feature Layers (WOFLs), in a 1 to 1 relationship with the input satellite data. Hence there is one WOFL for each satellite dataset processed for the occurrence of water. The details of the WOfS algorithm and derived statistics are available at http://dx.doi.org/10.1016/j.rse.2015.11.003.
For service status information, see https://status.dea.ga.gov.au
""",
                    "product_name": "wofs_albers",
                    "bands": bands_wofs_obs,
                    "resource_limits": reslim_wofs_obs,
                    "dynamic": True,
                    "image_processing": {
                        "extent_mask_func": "datacube_ows.ogc_utils.mask_by_bitflag",
                        "always_fetch_bands": [],
                        "manual_merge": False,
                        "fuse_func": "datacube_ows.wms_utils.wofls_fuser",
                    },
                    "wcs": {
                        "native_crs": "EPSG:3577",
                        "native_resolution": [25, -25],
                        "default_bands": ["water"],
                    },
                    "styling": {
                        "default_style": "observations",
                        "styles": [style_wofs_obs, style_wofs_obs_wet_only],
                    },
                },
                {
                    "title": "Fractional Cover 25m 100km tile (Fractional Cover Landsat 7)",
                    "name": "ls7_fc_albers",
                    "abstract": """
Fractional Cover version 2.2.1, 25 metre, 100km tile, Australian Albers Equal Area projection (EPSG:3577). Data is only visible at higher resolutions; when zoomed-out the available area will be displayed as a shaded region.
Fractional cover provides information about the the proportions of green vegetation, non-green vegetation (including deciduous trees during autumn, dry grass, etc.), and bare areas for every 25m x 25m ground footprint. Fractional cover provides insight into how areas of dry vegetation and/or bare soil and green vegetation are changing over time. The fractional cover algorithm was developed by the Joint Remote Sensing Research Program, for more information please see data.auscover.org.au/xwiki/bin/view/Product+pages/Landsat+Fractional+Cover
Fractional Cover products use Water Observations from Space (WOfS) to mask out areas of water, cloud and other phenomena.
This product contains Fractional Cover dervied from the Landsat 7 satellite
For service status information, see https://status.dea.ga.gov.au
""",
                    "product_name": "ls7_fc_albers",
                    "bands": bands_fc,
                    "resource_limits": reslim_aster,
                    "dynamic": True,
                    "image_processing": {
                        "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                        "always_fetch_bands": [],
                        "manual_merge": False,
                    },
                    "flags": [
                        {
                            "band": "water",
                            "product": "wofs_albers",
                            "ignore_time": False,
                            "ignore_info_flags": [],
                            "fuse_func": "datacube_ows.wms_utils.wofls_fuser",
                        },
                    ],
                    "wcs": {
                        "native_crs": "EPSG:3577",
                        "default_bands": ["BS", "PV", "NPV"],
                        "native_resolution": [25, -25],
                    },
                    "styling": {
                        "default_style": "simple_fc",
                        "styles": [
                            style_fc_simple,
                        ],
                    },
                },
                {
                    "title": "Fractional Cover 25m 100km tile (Fractional Cover Landsat 8)",
                    "name": "ls8_fc_albers",
                    "abstract": """
Fractional Cover version 2.2.1, 25 metre, 100km tile, Australian Albers Equal Area projection (EPSG:3577). Data is only visible at higher resolutions; when zoomed-out the available area will be displayed as a shaded region.
Fractional cover provides information about the the proportions of green vegetation, non-green vegetation (including deciduous trees during autumn, dry grass, etc.), and bare areas for every 25m x 25m ground footprint. Fractional cover provides insight into how areas of dry vegetation and/or bare soil and green vegetation are changing over time. The fractional cover algorithm was developed by the Joint Remote Sensing Research Program, for more information please see data.auscover.org.au/xwiki/bin/view/Product+pages/Landsat+Fractional+Cover
Fractional Cover products use Water Observations from Space (WOfS) to mask out areas of water, cloud and other phenomena.
This product contains Fractional Cover dervied from the Landsat 8 satellite
For service status information, see https://status.dea.ga.gov.au
""",
                    "product_name": "ls8_fc_albers",
                    "bands": bands_fc,
                    "resource_limits": reslim_aster,
                    "dynamic": True,
                    "image_processing": {
                        "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                        "always_fetch_bands": [],
                        "manual_merge": False,
                    },
                    "flags": [
                        {
                            "band": "water",
                            "product": "wofs_albers",
                            "ignore_time": False,
                            "ignore_info_flags": [],
                            "fuse_func": "datacube_ows.wms_utils.wofls_fuser",
                        },
                    ],
                    "wcs": {
                        "native_crs": "EPSG:3577",
                        "default_bands": ["BS", "PV", "NPV"],
                        "native_resolution": [25, -25],
                    },
                    "styling": {
                        "default_style": "simple_fc",
                        "styles": [
                            style_fc_simple,
                        ],
                    },
                },
                {
                    "title": "Fractional Cover 25m 100km tile (Fractional Cover Combined)",
                    "name": "fc_albers_combined",
                    "abstract": """
Fractional Cover version 2.2.1, 25 metre, 100km tile, Australian Albers Equal Area projection (EPSG:3577). Data is only visible at higher resolutions; when zoomed-out the available area will be displayed as a shaded region. Fractional cover provides information about the the proportions of green vegetation, non-green vegetation (including deciduous trees during autumn, dry grass, etc.), and bare areas for every 25m x 25m ground footprint. Fractional cover provides insight into how areas of dry vegetation and/or bare soil and green vegetation are changing over time. The fractional cover algorithm was developed by the Joint Remote Sensing Research Program, for more information please see data.auscover.org.au/xwiki/bin/view/Product+pages/Landsat+Fractional+Cover Fractional Cover products use Water Observations from Space (WOfS) to mask out areas of water, cloud and other phenomena. This product contains Fractional Cover dervied from the Landsat 5, 7 and 8 satellites For service status information, see https://status.dea.ga.gov.au
""",
                    "multi_product": True,
                    "product_names": [
                        "ls5_fc_albers",
                        "ls7_fc_albers",
                        "ls8_fc_albers",
                    ],
                    "bands": bands_fc,
                    "resource_limits": reslim_aster,
                    "dynamic": True,
                    "image_processing": {
                        "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                        "always_fetch_bands": [],
                        "manual_merge": False,
                    },
                    "flags": [
                        {
                            "band": "water",
                            "products": ["wofs_albers", "wofs_albers", "wofs_albers"],
                            "ignore_time": False,
                            "ignore_info_flags": [],
                            "fuse_func": "datacube_ows.wms_utils.wofls_fuser",
                        },
                    ],
                    "wcs": {
                        "native_crs": "EPSG:3577",
                        "default_bands": ["BS", "PV", "NPV"],
                        "native_resolution": [25, -25],
                    },
                    "styling": {
                        "default_style": "simple_fc",
                        "styles": [
                            style_fc_simple,
                        ],
                    },
                },
            ],
        },
    ],  ##### End of "layers" list.
}  #### End of test configuration object
