# pylint: skip-file

# Example configuration file for datacube_ows.
#
# OVERVIEW
#
# This file forms the primary documentation for the configuration file format at this stage.
#
# The actual configuration is held in a single serialisable object that can be directly
# declared as a python object or imported from JSON.
#
# WHERE IS CONFIGURATION READ FROM?
#
# Configuration is read by default from the ows_cfg object in datacube_ows/ows_cfg.py
#
# but this can be overridden by setting the $DATACUBE_OWS_CFG environment variable.
#
# $DATACUBE_OWS_CFG is interpreted as follows (first matching alternative applies):
#
# 1. Has a leading slash, e.g. "/opt/odc_ows_cfg/odc_ows_cfg_prod.json"
#    Config loaded as json from absolute file path.
#
# 2. Contains a slash, e.g. "configs/prod.json"
#    Config loaded as json from relative file path.
#
# 3. Begins with an open brace "{", e.g. "{...}"
#    Config loaded directly from the environment variable as json (not recommended)
#
# 4. Ends in ".json", e.g. "cfg_prod.json"
#    Config loaded as json from file in working directory.
#
# 5. Contains a dot (.), e.g. "package.sub_package.module.cfg_object_name"
#    Imported as python object (expected to be a dictionary).
#    N.B. It is up to you that the Python file in question is in your Python path.
#
# 6. Valid python object name, e.g. "cfg_prod"
#    Imported as python object from named object in datacube_ows/ows_cfg.py
#
# 7. Blank or not set
#    Default to import ows_cfg object in datacube_ows/ows_cfg.py as described above.
#
# REUSING CHUNKS OF CONFIGURATION
#
# Often it is desirable to re-use chunks of configuration in multiple places.  E.g. a set
# of related data products may share a band index or style definition configurations.
#
# If you are loading config as a Python object, this is trivial, as demonstrated in this
# example file.
#
# If you want to reuse chunks of config in json, or wish to combine bits of json config
# with bits of python config, the following convention applies in both Python and JSON
# configuration:
#
# Any JSON or Python element that forms the full configuration tree or a subset of it,
# can be supplied in any of the following ways:
#
# 1. Directly embed the config content:
#       {
#           "a_cfg_entry": 1,
#           "another_entry": "llama",
#       }
#
# 2. Include a python object (by FQN):
#       {
#           "include": "path.to.module.object",
#           "type": "python"
#       }
#
#       N.B. It is up to you to make sure the included Python file is in your Python Path.
#            Relative Python imports are not supported.
#
# 3. Include a JSON file (by absolute or relative file path):
#       {
#           "include": "path/to/file.json",
#           "type": "json"
#       }
#
#       N.B. Resolution of relative file paths is done in the following order:
#           a) Relative to the working directory of the web app.
#           b) If a JSON file is being included from another JSON file, relative to
#              directory in which the including file resides.
#
# Note that this does not just apply to dictionaries. Either of the above include dictionaries
# could expand to an array, or even to single integer or string.
#
# THIS EXAMPLE FILE
#
# In this example file, there are some reusable code chunks defined at the top.  The actual
# config tree is defined as ows_cfg below the reusable chunks.
#

# REUSABLE CONFIG FRAGMENTS - Band alias maps
landsat8_bands = {
    # Supported bands, mapping native band names to a list of possible aliases.
    # 1. Aliases must be unique for the product.
    # 2. Band aliases can be used anywhere in the configuration that refers to bands by name.
    # 3. The native band name MAY be explicitly declared as an alias for the band, but are always treated as
    # a valid alias.
    # 4. The band labels used in GetFeatureInfo and WCS responses will be the first declared alias (or the native name
    # if no aliases are declared.)
    # 5. Bands NOT listed here will not be included in the GetFeatureInfo output and cannot be referenced
    # elsewhere in the configuration.
    # 6. If not specified for a product, defaults to all available bands, using only their native names.
    # 7. The following are reserved words that may not be used as aliases.  (N.B. If they occur as a native
    #    band name, an alias should be declared and used in the config in preference to the native name):
    #               scale_range
    #               function
    #
    "red": [],
    "green": [],
    "blue": [ "near_blue" ],
    "nir": [ "near_infrared" ],
    "swir1": [ "shortwave_infrared_1", "near_shortwave_infrared" ],
    "swir2": [ "shortwave_infrared_2", "far_shortwave_infrared" ],
    "coastal_aerosol": [ "far_blue" ],
    "quality": [ ],

    # N.B. Include pixel quality bands if they are in the main data product.
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
            "red": 1.0
        },
        "green": {
            "green": 1.0
        },
        "blue": {
            "blue": 1.0
        }
    },
    # The raw band value range to be compressed to an 8 bit range for the output image tiles.
    # Band values outside this range are clipped to 0 or 255 as appropriate.
    "scale_range": [0.0, 65535.0],
    # Legend section is optional for linear combination styles. If not supplied, no legend is displayed
    "legend": {
        # Whether or not to display a legend for this style.
        # Defaults to False for linear combination styles.
        "show_legend": True,
        # A legend cannot be auto-generated for a linear combination style, so a url pointing to
        # legend PNG image must be supplied if 'show_legend' is True.
        # Note that legend urls are proxied, not displayed directly to the user.
        "url": "http://example.com/custom_style_image.png"
    }

}

style_rgb_cloudmask = {
    "name": "cloud_masked_rgb",
    "title": "Simple RGB with cloud masking",
    "abstract": "Simple true-colour image, using the red, green and blue bands, with cloud masking",
    "components": {
        "red": {
            "red": 1.0
        },
        "green": {
            "green": 1.0
        },
        "blue": {
            "blue": 1.0
        }
    },
    # PQ masking example
    # Pixels with any of the listed flag values are masked out (made transparent).
    "pq_masks": [
        {
            "flags": {
                "cloud_acca": "no_cloud",
                "cloud_fmask": "no_cloud",
            },
        },
    ],
    "scale_range": [0.0, 65535.0],
}

style_rgb_cloud_and_shadowmask = {
    "name": "cloud_and_shadow_masked_rgb",
    "title": "Simple RGB with cloud and cloud shadow masking",
    "abstract": "Simple true-colour image, using the red, green and blue bands, with cloud and cloud shadow masking",
    "components": {
        "red": {
            "red": 1.0
        },
        "green": {
            "green": 1.0
        },
        "blue": {
            "blue": 1.0
        }
    },
    # PQ masking example
    "pq_masks": [
        {
            "flags": {
                "cloud_acca": "no_cloud",
                "cloud_fmask": "no_cloud",
                "cloud_shadow_acca": "no_cloud_shadow",
                "cloud_shadow_fmask": "no_cloud_shadow",
            },
        },
    ],
    "scale_range": [0.0, 65535.0],
}

style_ext_rgb = {
    "name": "extended_rgb",
    "title": "Extended RGB",
    "abstract": "Extended true-colour image, incorporating the coastal aerosol band",
    "components": {
        "red": {
            "red": 1.0
        },
        "green": {
            "green": 1.0
        },
        "blue": {
            "blue": 0.6,
            "coastal_aerosol": 0.4
        }
    },
    "scale_range": [0.0, 65535.0],
}

style_ls8_allband_false_colour = {
    "name": "wideband",
    "title": "Wideband false-colour",
    "abstract": "False-colour image, incorporating all available LS8 spectral bands",
    "components": {
        "red": {
            "swir2": 0.255,
            "swir1": 0.45,
            "nir": 0.255,
        },
        "green": {
            "nir": 0.255,
            "red": 0.45,
            "green": 0.255,
        },
        "blue": {
            "green": 0.255,
            "blue": 0.45,
            "coastal_aerosol": 0.255,
        }
    },
    "scale_range": [0.0, 65535.0],
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
        }
    },
    # The style scale_range can be omitted if all components have a component-specific scale_range defined.
    # "scale_range": [0.0, 3000.0]
}

style_mineral_content = {
    "name": "mineral_content",
    "title": "Multi-band mineral indexes",
    "abstract": "Red: Ferric Iron. Green: Bare soil. Blue: Clay/mica",
    "components": {
        "red": {
            # If the component dictionary contains the key "function", then the dictionary as treated as
            # a function callback as follows:
            #    a) "function" (required): A string containing the fully qualified path to a python function
            #    b) "args" (optional): An array of additional positional arguments that will always be passed to the function.
            #    c) "kwargs" (optional): An array of additional keyword arguments that will always be passed to the function.
            #    d) "pass_product_cfg" (optional): Boolean (defaults to False). If true, the relevant ProductLayerConfig is passed
            #       to the function as a keyword argument named "product_cfg".  This is useful if you are passing band aliases
            #       to the function in the args or kwargs.  The product_cfg allows the index function to convert band aliases to
            #       to band names.
            #
            # The function is assumed to take one arguments, an xarray Dataset.  (Plus any additional
            # arguments required by the args and kwargs values in format 3, possibly including product_cfg.)
            #
            # An xarray DataArray is returned containing the band data.  Note that it is up to the function
            # to normalise the output to 0-255.
            #
            "function": "datacube_ows.band_utils.norm_diff",
            "pass_product_cfg": True,
            "kwargs": {
                "band1": "red",
                "band2": "blue",
                "scale_from": [-0.1, 1.0],
            }
        },
        "green": {
            "function": "datacube_ows.band_utils.norm_diff",
            "pass_product_cfg": True,
            "kwargs": {
                "band1": "nir",
                "band2": "swir1",
                "scale_from": [-0.1, 1.0],
            }
        },
        "blue": {
            "function": "datacube_ows.band_utils.norm_diff",
            "pass_product_cfg": True,
            "kwargs": {
                "band1": "swir1",
                "band2": "swir2",
                "scale_from": [-0.1, 1.0],
            }
        }
    },
    # If ANY components include a function callback, the bands that need to be passed to the callback
    # MUST be declared in a "additional_bands" item:
    "additional_bands": [ "red", "blue", "nir", "swir1", "swir2" ]

    #
    # The style scale_range can be omitted if all components have a component-specific scale_range defined or
    # a function callback.
    # "scale_range": [0.0, 3000.0]
}

# Monochrome single band layers
style_pure_ls8_coastal_aerosol = {
    "name": "coastal_aerosol",
    "title": "Spectral band 1 - Coastal aerosol",
    "abstract": "Coastal aerosol band, approximately 435nm to 450nm",
    "components": {
        "red": {
            "coastal_aerosol": 1.0
        },
        "green": {
            "coastal_aerosol": 1.0
        },
        "blue": {
            "coastal_aerosol": 1.0
        }
    },
    "scale_range": [0.0, 65535.0],
}

style_pure_ls8_blue = {
    "name": "blue",
    "title": "Spectral band 2 - Blue",
    "abstract": "Blue band, approximately 453nm to 511nm",
    "components": {
        "red": {
            "blue": 1.0
        },
        "green": {
            "blue": 1.0
        },
        "blue": {
            "blue": 1.0
        }
    },
    "scale_range": [0.0, 65535.0],
}

style_pure_ls8_green = {
    "name": "green",
    "title": "Spectral band 3 - Green",
    "abstract": "Green band, approximately 534nm to 588nm",
    "components": {
        "red": {
            "green": 1.0
        },
        "green": {
            "green": 1.0
        },
        "blue": {
            "green": 1.0
        }
    },
    "scale_range": [0.0, 65535.0],
}

style_pure_ls8_red = {
    "name": "red",
    "title": "Spectral band 4 - Red",
    "abstract": "Red band, roughly 637nm to 672nm",
    "components": {
        "red": {
            "red": 1.0
        },
        "green": {
            "red": 1.0
        },
        "blue": {
            "red": 1.0
        }
    },
    "scale_range": [0.0, 65535.0],
}

style_pure_ls8_nir = {
    "name": "nir",
    "title": "Spectral band 5 - Near infra-red",
    "abstract": "Near infra-red band, roughly 853nm to 876nm",
    "components": {
        "red": {
            "nir": 1.0
        },
        "green": {
            "nir": 1.0
        },
        "blue": {
            "nir": 1.0
        }
    },
    "scale_range": [0.0, 65535.0],
}

style_pure_ls8_swir1 = {
    "name": "swir1",
    "title": "Spectral band 6 - Short wave infra-red 1",
    "abstract": "Short wave infra-red band 1, roughly 1575nm to 1647nm",
    "components": {
        "red": {
            "swir1": 1.0
        },
        "green": {
            "swir1": 1.0
        },
        "blue": {
            "swir1": 1.0
        }
    },
    "scale_range": [0.0, 65535.0],
}

style_pure_ls8_swir2 = {
    "name": "swir2",
    "title": "Spectral band 7 - Short wave infra-red 2",
    "abstract": "Short wave infra-red band 2, roughly 2117nm to 2285nm",
    "components": {
        "red": {
            "swir2": 1.0
        },
        "green": {
            "swir2": 1.0
        },
        "blue": {
            "swir2": 1.0
        }
    },
    "scale_range": [0.0, 65535.0],
}


# Examples of non-linear colour-ramped styles.
style_ndvi = {
    "name": "ndvi",
    "title": "NDVI",
    "abstract": "Normalised Difference Vegetation Index - a derived index that correlates well with the existence of vegetation",
    # The index function is continuous value from which the heat map is derived.
    #
    # Two formats are supported:
    # 1. A string containing a fully qualified path to a python function
    #    e.g. "index_function": "datacube_ows.ogc_utils.not_a_real_function_name",
    #
    # 2. A dict containing the following elements:
    #    a) "function" (required): A string containing the fully qualified path to a python function
    #    b) "args" (optional): An array of additional positional arguments that will always be passed to the function.
    #    c) "kwargs" (optional): An array of additional keyword arguments that will always be passed to the function.
    #    d) "pass_product_cfg" (optional): Boolean (defaults to False). If true, the relevant ProductLayerConfig is passed
    #       to the function as a keyword argument named "product_cfg".  This is useful if you are passing band aliases
    #       to the function in the args or kwargs.  The product_cfg allows the index function to convert band aliases to
    #       to band names.
    #
    # The function is assumed to take one arguments, an xarray Dataset.  (Plus any additional
    # arguments required by the args and kwargs values in format 3, possibly including product_cfg.)
    #
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "pass_product_cfg": True,
        "kwargs": {
            "band1": "nir",
            "band2": "red"
        }
    },
    # List of bands used by this style. The band may not be passed to the index function if it is not declared
    # here, resulting in an error.  Band aliases can be used here.
    "needed_bands": ["red", "nir"],
    # The color ramp. Values between specified entries have both their alphas and colours
    # interpolated.
    "color_ramp": [
        # Any value less than the first entry will have colour and alpha of the first entry.
        # (i.e. in this example all negative values will be fully transparent (alpha=0.0).)
        {
            "value": -0.0,
            "color": "#8F3F20",
            "alpha": 0.0
        },
        {
            "value": 0.0,
            "color": "#8F3F20",
            "alpha": 1.0
        },
        {
            # do not have to defined alpha value
            # if no alpha is specified, alpha will default to 1.0 (fully opaque)
            "value": 0.1,
            "color": "#A35F18"
        },
        {
            "value": 0.2,
            "color": "#B88512"
        },
        {
            "value": 0.3,
            "color": "#CEAC0E"
        },
        {
            "value": 0.4,
            "color": "#E5D609"
        },
        {
            "value": 0.5,
            "color": "#FFFF0C"
        },
        {
            "value": 0.6,
            "color": "#C3DE09"
        },
        {
            "value": 0.7,
            "color": "#88B808"
        },
        {
            "value": 0.8,
            "color": "#529400"
        },
        {
            "value": 0.9,
            "color": "#237100"
        },
        # Values greater than the last entry will use the colour and alpha of the last entry.
        # (N.B. This will not happen for this example because it is normalised so that 1.0 is
        # maximum possible value.)
        {
            "value": 1.0,
            "color": "#114D04"
        }
    ],
    # If true, the calculated index value for the pixel will be included in GetFeatureInfo responses.
    # Defaults to True.
    "include_in_feature_info": True,
    # Legend section is optional for non-linear colour-ramped styles.
    # If not supplied, a legend for the style will be automatically generated from the colour ramp.
    "legend": {
        # Whether or not to display a legend for this style.
        # Defaults to True for non-linear colour-ramped styles.
        "show_legend": True,
        # Instead of using the generated color ramp legend for the style, a URL to an PNG file can
        # be used instead.  If 'url' is not supplied, the generated legend is used.
        "url": "http://example.com/custom_style_image.png"
    }
}

# Examples of non-linear colour-ramped style with multi-date support.
style_ndvi_delta = {
    "name": "ndvi_delta",
    "title": "NDVI Delta",
    "abstract": "Normalised Difference Vegetation Index - with delta support",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "pass_product_cfg": True,
        "kwargs": {
            "band1": "nir",
            "band2": "red"
        }
    },
    "needed_bands": ["red", "nir"],
    # The color ramp for single-date requests - same as ndvi style example above
    "color_ramp": [
        {
            "value": -0.0,
            "color": "#8F3F20",
            "alpha": 0.0
        },
        {
            "value": 0.0,
            "color": "#8F3F20",
            "alpha": 1.0
        },
        {
            "value": 0.1,
            "color": "#A35F18"
        },
        {
            "value": 0.2,
            "color": "#B88512"
        },
        {
            "value": 0.3,
            "color": "#CEAC0E"
        },
        {
            "value": 0.4,
            "color": "#E5D609"
        },
        {
            "value": 0.5,
            "color": "#FFFF0C"
        },
        {
            "value": 0.6,
            "color": "#C3DE09"
        },
        {
            "value": 0.7,
            "color": "#88B808"
        },
        {
            "value": 0.8,
            "color": "#529400"
        },
        {
            "value": 0.9,
            "color": "#237100"
        },
        {
            "value": 1.0,
            "color": "#114D04"
        }
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
            "feature_info_label": "ndvi_delta"
        }
    ]
}

# Examples of Matplotlib Color-Ramp styles
style_deform = {
    "name": "deform",
    "title": "InSAR Deformation",
    "abstract": "InSAR Derived Deformation Map",
    # The range specifies the min and max values for the color ramp.  Required if an explicit color ramp is not
    # defined.
    "range": [-110.0, 110.0],
    # The Matplotlib color ramp. Value specified is a string that indicates a Matplotlib Colour Ramp should be
    # used. Reference here: https://matplotlib.org/examples/color/colormaps_reference.html
    # Only used if an explicit colour ramp is not defined.  Optional - defaults to a simple (but
    # kind of ugly) blue-to-red rainbow ramp.
    "mpl_ramp": "RdBu",
    # If true, the calculated index value for the pixel will be included in GetFeatureInfo responses.
    # Defaults to True.
    "include_in_feature_info": True,
    # Legend section is optional for non-linear colour-ramped styles.
    # If not supplied, a legend for the style will be automatically generated from the colour ramp.
    "legend": {
        # appended to the title of the legend
        # if missing will use 'unitless'
        "units": "mm",
        # radix places to round tick labels to
        # set to 0 for ints
        "radix_point": 0,
        # values will be scaled by this amount
        # to generate tick labels
        # e.g. for a percentage stored as 0 - 1.0
        # this should be 100
        # TODO: Make this derive automatically from range as appropriate
        "scale_by": 1.0,
        # tick labels will be created for values that
        # are modulo 0 by this value
        "major_ticks": 10,
        ## Use offset to get negative side of the ramp
        "offset": 0.0
    }
}

style_ndvi_cloudmask = {
    "name": "ndvi_cloudmask",
    "title": "NDVI with cloud masking",
    "abstract": "Normalised Difference Vegetation Index (with cloud masking) - a derived index that correlates well with the existence of vegetation",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "pass_product_cfg": True,
        "kwargs": {
            "band1": "nir",
            "band2": "red"
        }
    },
    "needed_bands": ["red", "nir"],
    # If a "range" is supplied instead of a "color_ramp", a default color ramp is used.
    # Areas where the index_function returns less the lower range limit are transparent.
    # Areas where the index_function returns within the range limits are mapped to a
    # simple heat map ranging from dark blue, through blue, green, yellow, orange, and red to dark red.
    # Areas where the index_function returns greater than the upper range limit are displayed as dark red.
    "range": [0.0, 1.0],
    # Cloud masks work the same as for linear combination styles.
    "pq_masks": [
        {
            "flags": {
                "cloud_acca": "no_cloud",
                "cloud_fmask": "no_cloud",
            },
        },
    ],
    # Already have NDVI in GetFeatureInfo.
    "include_in_feature_info": False,
}

style_ndwi = {
    "name": "ndwi",
    "title": "NDWI",
    "abstract": "Normalised Difference Water Index - a derived index that correlates well with the existence of water",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "pass_product_cfg": True,
        "kwargs": {
            "band1": "green",
            "band2": "nir"
        }
    },
    "needed_bands": ["green", "nir"],
    "range": [0.0, 1.0],
}

style_ndbi = {
    "name": "ndbi",
    "title": "NDBI",
    "abstract": "Normalised Difference Buildup Index - a derived index that correlates with the existence of urbanisation",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "pass_product_cfg": True,
        "kwargs": {
            "band1": "swir2",
            "band2": "nir"
        }
    },
    "needed_bands": ["swir2", "nir"],
    "range": [0.0, 1.0],
}

# Mask layers - examples of how to display raw pixel quality data.
# This works by creatively mis-using the colormap styles.
# The index function returns a constant, so the output is a flat single colour, masked by the
# relevant pixel quality flags.
style_cloud_mask = {
    "name": "cloud_mask",
    "title": "Cloud Mask",
    "abstract": "Highlight pixels with cloud.",
    "index_function": {
        "function": "datacube_ows.band_utils.constant",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "red",
            "const": "0.1"
        }
    },
    "needed_bands": ["red"],
    "range": [0.0, 1.0],
    # Mask flags normally describe which areas SHOULD be shown.
    # (i.e. show pixels with any of the declared flag values)
    # pq_mask_invert inverts this logic.
    # (i.e. show pixels for which none of the declared flags are true)
    #
    # i.e. Specifying like this shows pixels which are not clouds under either algorithm.
    #      Specifying "cloud"for both flags and setting the "pq_mask_invert" to False would
    #      show pixels which are not clouds in both metrics.
    "pq_masks": [
        {
            "invert": True,
            "flags": {
                "cloud_acca": "no_cloud",
                "cloud_fmask": "no_cloud",
            },
        },
    ],
    "legend": {
        # Default legend won't work well with mask layers, so set 'show_legend' to False or provide a url to
        # legend PNG.
        "show_legend": False
    },
    # The constant function causes errors in GetFeatureInfo.
    # In any case, pixel flags are already included in GetFeatureInfo, so styles like this are not needed there.
    "include_in_feature_info": False,
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
        "pass_product_cfg": True,
        "kwargs": {
            "band1": "nir",
            "band2": "red"
        }
    },
    "needed_bands": ["red", "nir"],
    "range": [0.0, 1.0],
    "components": {
        "red": {
            "red": 1.0
        },
        "green": {
            "green": 1.0
        },
        "blue": {
            "blue": 1.0
        }
    },
    "scale_range": [0.0, 65535.0],
    # N.B. The "pq_mask" section works the same as for the style types above.
}

# Describes a style which uses several bitflags to create a style

# REUSABLE CONFIG FRAGMENTS - resource limit declarations

standard_resource_limits = {
    "wms": {
        # WMS/WMTS resource limits
        #
        # There are two independent resource limits applied to WMS/WMTS requests.  If either
        # limit is exceeded, then the actual data is not rendered.  Instead an indicative polygon
        # showing the extent of the data is rendered.
        #
        # The fill-colour of the indicative polygons when either wms/wmts resource limits is exceeded.
        # Triplets (rgb) or quadruplets (rgba) of integers 0-255.
        #
        # (The fourth number in an rgba quadruplet represents opacity with 255 being fully opaque and
        # 0 being fully transparent.)
        #
        # Defaults to [150, 180, 200, 160]
        "zoomed_out_fill_colour": [150, 180, 200, 160],

        # WMS/WMTS Resource Limit 1: Min zoom factor
        #
        # The zoom factor is a dimensionless number calculated from the request in a way that is independent
        # of the CRS. A higher zoom factor corresponds to a more zoomed in view.
        #
        # If the zoom factor of the request is less than the minimum zoom factor (i.e. is zoomed out too far)
        # then indicative polygons are rendered instead of accessing the actual data.
        #
        # Defaults to 300.0
        "min_zoom_factor": 500.0,

        # Min zoom factor (above) works well for small-tiled requests, (e.g. 256x256 as sent by Terria).
        # However, for large-tiled requests (e.g. as sent by QGIS), large and intensive queries can still
        # go through to the datacube.
        #
        # max_datasets specifies a maximum number of datasets that a GetMap or GetTile request can retrieve.
        # Indicatative polygons are displayed if a request exceeds the limits imposed by EITHER max_dataset
        # OR min_zoom_factor.
        #
        # max_datasets should be set in conjunction with min_zoom_factor so that Terria style 256x256
        # tiled requests respond consistently - you never want to see a mixture of photographic tiles and polygon
        # tiles at a given zoom level.  i.e. max_datasets should be greater than the number of datasets
        # required for most intensive possible photographic query given the min_zoom_factor.
        # Note that the ideal value may vary from product to product depending on the size of the dataset
        # extents for the product.
        # Defaults to zero, which is interpreted as no dataset limit.
        "max_datasets": 6,
    },
    "wcs": {
        # wcs::max_datasets is the WCS equivalent of wms::max_datasets.  The main requirement for setting this
        # value is to avoid gateway timeouts on overly large WCS requests (and reduce server load).
        #
        # Defaults to zero, which is interpreted as no dataset limit.
        "max_datasets": 16,
    }
}


# MAIN CONFIGURATION OBJECT

ows_cfg = {
    # Config entries in the "global" section apply to all services and all layers/coverages
    "global": {

        # These HTML headers are added to all responses
        # Optional, default {} - no added headers
        "response_headers": {
            "Access-Control-Allow-Origin": "*",  # CORS header (strongly recommended)
        },
        ## Which web service(s) should be implemented by this instance
        # Optional, defaults: wms,wmts: True, wcs: False
        "services": {
            "wms": True,
            "wmts": True,
            "wcs": True
        },
        # Service title - appears e.g. in Terria catalog (required)
        "title": "OGC web-services for the Open Datacube",
        # Service URL.
        # A list of fully qualified URLs that the service can return
        # in the GetCapabilities documents based on the requesting url
        "allowed_urls": [ "http://localhost/odc_ows",
                          "https://localhost/odc_ows",
                          "https://alternateurl.domain.org/odc_ows",
                          "http://127.0.0.1:5000/"],
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
        # Supported co-ordinate reference systems. Any coordinate system supported by GDAL and Proj.4J can be used.
        # At least one CRS must be included.  At least one geographic CRS must be included if WCS is active.
        # Web Mercator (EPSG:3857) and WGS-84 (EPSG:4326) are strongly recommended, but not required.
        "published_CRSs": {
            "EPSG:3857": {  # Web Mercator
                "geographic": False,
                "horizontal_coord": "x",
                "vertical_coord": "y",
            },
            "EPSG:4326": {  # WGS-84
                "geographic": True,
                "vertical_coord_first": True
            },
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
    },   #### End of "global" section.

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
        # Max tile height/width for wms.  (N.B. Does not apply to WMTS)
        # Optional, defaults to 256x256
        "max_width": 512,
        "max_height": 512,
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
            }
        },
        # These define the AuthorityURLs.
        # They represent the authorities that define the "Identifiers" defined layer by layer below.
        # The spec allows AuthorityURLs to be defined anywhere on the Layer heirarchy, but datacube_ows treats them
        # as global entities.
        # Required if identifiers are to be declared for any layer.
        "authorities": {
            # The authorities dictionary maps names to authority urls.
            "auth": "https://authoritative-authority.com",
            "idsrus": "https://www.identifiers-r-us.com",
        }
    }, ####  End of "wms" section.

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
        # The wcs:native_format must be declared in wcs:formats dict above.
        "native_format": "GeoTIFF",
    }, ###### End of "wcs" section

    # Products published by this datacube_ows instance.
    # The layers section is a list of layer definitions.  Each layer may be either:
    # 1) A folder-layer.  Folder-layers are not named and can contain a list of child layers.  Folder-layers are
    #    only used by WMS and WMTS - WCS does not support a hierarchical index of coverages.
    # 2) A mappable named layer that can be requested in WMS GetMap or WMTS GetTile requests.  A mappable named layer
    #    is also a coverage, that may be requested in WCS DescribeCoverage or WCS GetCoverage requests.
    "layers": [
        {
            # NOTE: This layer is a folder - it is NOT "named layer" that can be selected in GetMap requests
            # Every layer must have a human-readable title
            "title": "Landsat 8",
            # Top level layers must have a human-readable abstract. The abstract is optional for child-layers - defaulting
            # to that of the parent layer.
            "abstract": "Images from the Landsat 8 satellite",
            # NOTE: Folder-layers do not have a layer "name".

            # Keywords are optional, but can be added at any folder level and are cumulative.
            # A layer combines its own keywords, the keywords of it's parent (and grandparent, etc) layers,
            # and any keywords defined in the global section above.
            #
            "keywords": [
                "landsat",
                "landsat8",
            ],
            # Attribution.  This entire section is optional.  If provided, it overrides any
            #               attribution defined in the wms section above or any higher layers, and
            #               applies to this layer and all child layers under this layer unless itself
            #               overridden.
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
                }
            },
            # Folder-type layers include a list of sub-layers
            "layers": [
                {
                    # NOTE: This layer IS a mappable "named layer" that can be selected in GetMap requests
                    "title": "Level 1 USGS Landsat-8 Public Data Set",
                    "abstract": "Imagery from the Level 1 Landsat-8 USGS Public Data Set",
                    "name": "ls8_usgs_level1_scene",
                    "product_name": "ls8_usgs_level1_scene",
                    "bands": landsat8_bands,
                    "resource_limits": standard_resource_limits,
                    "flags": {
                        "band": "quality",
                        "ignore_time": False,
                        "ignore_info_flags": [],
                        "manual_merge": True,
                    },
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
                        "always_fetch_bands": [ "quality" ],
                        "fuse_func": None,
                        "manual_merge": True,
                        # Apply corrections for solar angle, for "Level 1" products.
                        # (Defaults to false - should not be used for NBAR/NBAR-T or other Analysis Ready products
                        "apply_solar_corrections": True
                    },
                    "wcs": {
                        "native_crs": "EPSG:4326",
                        "native_resolution": [ 25.0, 25.0 ],
                        "default_bands": [ "red", "green", "blue" ],
                    },
                    "styling": {
                        "default_style": "simple_rgb",
                        "styles": [
                            style_rgb, style_ext_rgb,
                            style_ls8_allband_false_colour, style_infrared_false_colour,
                            style_pure_ls8_coastal_aerosol, style_pure_ls8_blue,
                            style_pure_ls8_green, style_pure_ls8_red,
                            style_pure_ls8_nir, style_pure_ls8_swir1, style_pure_ls8_swir2,
                            style_ndvi, style_ndwi, style_ndbi,
                            style_rgb_ndvi
                        ]
                    }
                } ##### End of ls8_level1_pds product definition.
            ]
        }  ### End of Landsat 8 folder.
    ]  ##### End of "layers" list.
} #### End of example configuration object




