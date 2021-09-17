# pylint: skip-file
# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0


# Example configuration file for datacube_ows.
#
# The file was originally the only documentation for the configuration file format.
# Detailed and up-to-date formal documentation is now available and this this file
# is no longer actively maintained and may contain errors or obsolete elements.
#
# https://datacube-ows.readthedocs.io/en/latest/configuration.html

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
    "blue": ["near_blue"],
    "nir": ["near_infrared"],
    "swir1": ["shortwave_infrared_1", "near_shortwave_infrared"],
    "swir2": ["shortwave_infrared_2", "far_shortwave_infrared"],
    "coastal_aerosol": ["far_blue"],

    # N.B. Include pixel quality bands if they are in the main data product.
}

sentinel2_bands = {
    "nbar_coastal_aerosol": ['nbar_far_blue'],
    "nbar_blue": [],
    "nbar_green": [],
    "nbar_red": [],
    "nbar_red_edge_1": [],
    "nbar_red_edge_2": [],
    "nbar_red_edge_3": [],
    "nbar_nir_1": ["nbar_near_infrared_1"],
    "nbar_nir_2": ["nbar_near_infrared_2"],
    "nbar_swir_2": ["nbar_shortwave_infrared_2"],
    "nbar_swir_3": ["nbar_shortwave_infrared_3"],
    "nbart_coastal_aerosol": ['coastal_aerosol', 'nbart_far_blue', 'far_blue'],
    "nbart_blue": ['blue'],
    "nbart_green": ['green'],
    "nbart_red": ['red'],
    "nbart_red_edge_1": ['red_edge_1'],
    "nbart_red_edge_2": ['red_edge_2'],
    "nbart_red_edge_3": ['red_edge_3'],
    "nbart_nir_1": ["nir_1", "nbart_near_infrared_1"],
    "nbart_nir_2": ["nir_2", "nbart_near_infrared_2"],
    "nbart_swir_2": ["swir_2", "nbart_shortwave_infrared_2"],
    "nbart_swir_3": ["swir_3", "nbart_shortwave_infrared_3"],

    # N.B. Include pixel quality bands if they are in the main data product.
    "quality": [],
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
    "scale_range": [0.0, 3000.0],
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
    "scale_range": [0.0, 3000.0]
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
    "scale_range": [0.0, 3000.0]
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
    "scale_range": [0.0, 3000.0]
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
    "scale_range": [0.0, 3000.0]
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
            #    d) "mapped_bands" (optional): Boolean (defaults to False). If true, a band mapping function is passed
            #       to the function as a keyword argument named "band_mapper".  This is useful if you are passing band aliases
            #       to the function in the args or kwargs.  The band_mapper allows the index function to convert band aliases to
            #       to band names.
            #
            # The function is assumed to take one arguments, an xarray Dataset.  (Plus any additional
            # arguments required by the args and kwargs values in format 3, possibly including product_cfg.)
            #
            # An xarray DataArray is returned containing the band data.  Note that it is up to the function
            # to normalise the output to 0-255.
            #
            "function": "datacube_ows.band_utils.norm_diff",
            "mapped_bands": True,
            "kwargs": {
                "band1": "red",
                "band2": "blue",
                "scale_from": [-0.1, 1.0],
            }
        },
        "green": {
            "function": "datacube_ows.band_utils.norm_diff",
            "mapped_bands": True,
            "kwargs": {
                "band1": "nir",
                "band2": "swir1",
                "scale_from": [-0.1, 1.0],
            }
        },
        "blue": {
            "function": "datacube_ows.band_utils.norm_diff",
            "mapped_bands": True,
            "kwargs": {
                "band1": "swir1",
                "band2": "swir2",
                "scale_from": [-0.1, 1.0],
            }
        }
    },
    # If ANY components include a function callback, the bands that need to be passed to the callback
    # MUST be declared in a "additional_bands" item:
    "additional_bands": ["red", "blue", "nir", "swir1", "swir2"]

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
    "scale_range": [0.0, 3000.0]
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
    "scale_range": [0.0, 3000.0]
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
    "scale_range": [0.0, 3000.0]
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
    "scale_range": [0.0, 3000.0]
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
    "scale_range": [0.0, 3000.0]
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
    "scale_range": [0.0, 3000.0]
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
    "scale_range": [0.0, 3000.0]
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
    #    d) "mapped_bands" (optional): Boolean (defaults to False). If true, a band mapping function is passed
    #       to the function as a keyword argument named "band_mapper".  This is useful if you are passing band aliases
    #       to the function in the args or kwargs.  The band_mapper allows the index function to convert band aliases to
    #       to band names.
    #
    # The function is assumed to take one arguments, an xarray Dataset.  (Plus any additional
    # arguments required by the args and kwargs values in format 3, possibly including product_cfg.)
    #
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "mapped_bands": True,
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
        "mapped_bands": True,
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
        # Show the legend (default True for colour ramp styles)
        "show_legend": True,
        # Example config for colour ramp style auto-legend generation.

        # The range covered by the legend.
        # Defaults to the first and last non transparent (alpha != 0.0)
        # entry in the explicit colour ramp, or the values in the range parameter.
        # It is recommended that values be supplied as integers or strings rather
        # than floating point.
        "begin": "0.0",
        "end": "1.0",
        # Ticks.
        # One of the following alternatives.  All the examples below result in the same tick behaviour, given
        # the begin and end values above.
        #
        # 1. Regularly spaced ticks, by size, starting from the begin tick.
        "ticks_every": "0.2",
        # 2. Regularly spaced ticks, by number of ticks, not counting the begin tick, but including the end tick. (int)
        # "tick_count": 5,
        # 3. Explicit ticks
        # "ticks": [ "0.0", "0.2", "0.4", "0.6". "0.8", "1.0"]
        # Default is a tick_count of 1, which means only the begin and end ticks.
        # Legend title.  Defaults to the style name.
        "title": "This is not a legend",

        # Units
        # added to title of legend in parenthesis, default is to not display units.  To emulate
        # the previous default behaviour use:
        "units": "unitless",

        # decimal_places. 1 for "1.0" style labels, 2 for "1.00" and 0 for "1", etc.
        # (default 1)
        "decimal_places": 1,

        # tick_labels
        # Labels for individual ticks can be customised"
        "tick_labels": {
            # The special entry "default" allows setting
            # a prefix and/or suffix for all labels.
            # Default is no prefix or suffix
            "default": {
                # E.g. this encloses every tick label in parentheses.
                "prefix": "(",
                "suffix": ")",
            },
            # Other entries override the label for individual ticks.
            # If they do not match a tick, as defined by the tick behaviour
            # described above, the entry is ignored.  If you are having trouble
            # getting the right tick value, use the "ticks" option to explicitly
            # declare your tick locations and make sure you use strings instead of
            # floats.
            # The default prefix and suffix can be over-ridden.
            "0.0": {
                # E.g. to remove the parentheses for the 0.0 tick
                "prefix": "",
                "suffix": "",
            },
            # Or the label can changed.  Note that the default prefix and suffix
            # are still applied unless explicitly over-ridden.
            # E.g. To display "(max)" for the 1.0 tick:
            "1.0": {
                "label": "max"
            }
        },

        # MatPlotLib rcparams options.
        # Defaults to {} (i.e. matplotlib defaults)
        # See https://matplotlib.org/3.2.2/tutorials/introductory/customizing.html
        "rcParams": {
                 "lines.linewidth": 2,
                 "font.weight": "bold",
        },

        # Image size (in "inches").
        # Matplotlib's default dpi is 100, so measured in hundreds of pixels unless the dpi
        # is over-ridden by the rcParams above.
        # Default is 4x1.25, i.e. 400x125 pixels
        "width": 4,
        "height": 1.25,

        # strip_location
        # The location and size of the coloured strip, in format:
        #  [ left, bottom, width, height ], as passed to Matplotlib Figure.add_axes function.
        # All values as fractions of the width and height.  (i.e. between 0.0 and 1.0)
        # The default is:
        "strip_location": [0.05, 0.5, 0.9, 0.15]
    },
    # Define behaviour(s) for multi-date requests. If not declared, style only supports single-date requests.
    "multi_date": [
        # A multi-date handler.  Different handlers can be declared for different numbers of dates in a request.
        {
            # The count range for which this handler is to be used - a tuple of two ints, the smallest and
            # largest date counts for which this handler will be used.  Required.
            "allowed_count_range": [2, 2],
            # Re-sort data returned from the ODC so the order of date coordinates in the "time" dimension
            # matches the date order supplied by the user in the WMS request.
            # Optional. Defaults to False (date coordinates in the "time" dimension are always sorted chronologically)
            "preserve_user_date_order": True,
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
            "legend": {
                # Legend only covers positive part of ramp.
                "begin": "0.0",
                "end": "1.0"
            },
            # The feature info label for the multi-date index value.
            "feature_info_label": "ndvi_delta"
        }
    ]
}

# Examples of non-linear colour-ramped style with multi-date animation support.
style_ndvi_anim = {
    "name": "ndvi_anim",
    "title": "NDVI Animation",
    "abstract": "Normalised Difference Vegetation Index - with animation support",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "mapped_bands": True,
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
        # Show the legend (default True for colour ramp styles)
        "show_legend": True,
        # Example config for colour ramp style auto-legend generation.

        # The range covered by the legend.
        # Defaults to the first and last non transparent (alpha != 0.0)
        # entry in the explicit colour ramp, or the values in the range parameter.
        # It is recommended that values be supplied as integers or strings rather
        # than floating point.
        "begin": "0.0",
        "end": "1.0",
        # Ticks.
        # One of the following alternatives.  All the examples below result in the same tick behaviour, given
        # the begin and end values above.
        #
        # 1. Regularly spaced ticks, by size, starting from the begin tick.
        "ticks_every": "0.2",
        # 2. Regularly spaced ticks, by number of ticks, not counting the begin tick, but including the end tick. (int)
        # "tick_count": 5,
        # 3. Explicit ticks
        # "ticks": [ "0.0", "0.2", "0.4", "0.6". "0.8", "1.0"]
        # Default is a tick_count of 1, which means only the begin and end ticks.
        # Legend title.  Defaults to the style name.
        "title": "This is not a legend",

        # Units
        # added to title of legend in parenthesis, default is to not display units.  To emulate
        # the previous default behaviour use:
        "units": "unitless",

        # decimal_places. 1 for "1.0" style labels, 2 for "1.00" and 0 for "1", etc.
        # (default 1)
        "decimal_places": 1,

        # tick_labels
        # Labels for individual ticks can be customised"
        "tick_labels": {
            # The special entry "default" allows setting
            # a prefix and/or suffix for all labels.
            # Default is no prefix or suffix
            "default": {
                # E.g. this encloses every tick label in parentheses.
                "prefix": "(",
                "suffix": ")",
            },
            # Other entries override the label for individual ticks.
            # If they do not match a tick, as defined by the tick behaviour
            # described above, the entry is ignored.  If you are having trouble
            # getting the right tick value, use the "ticks" option to explicitly
            # declare your tick locations and make sure you use strings instead of
            # floats.
            # The default prefix and suffix can be over-ridden.
            "0.0": {
                # E.g. to remove the parentheses for the 0.0 tick
                "prefix": "",
                "suffix": "",
            },
            # Or the label can changed.  Note that the default prefix and suffix
            # are still applied unless explicitly over-ridden.
            # E.g. To display "(max)" for the 1.0 tick:
            "1.0": {
                "label": "max"
            }
        },

        # MatPlotLib rcparams options.
        # Defaults to {} (i.e. matplotlib defaults)
        # See https://matplotlib.org/3.2.2/tutorials/introductory/customizing.html
        "rcParams": {
                 "lines.linewidth": 2,
                 "font.weight": "bold",
        },

        # Image size (in "inches").
        # Matplotlib's default dpi is 100, so measured in hundreds of pixels unless the dpi
        # is over-ridden by the rcParams above.
        # Default is 4x1.25, i.e. 400x125 pixels
        "width": 4,
        "height": 1.25,

        # strip_location
        # The location and size of the coloured strip, in format:
        #  [ left, bottom, width, height ], as passed to Matplotlib Figure.add_axes function.
        # All values as fractions of the width and height.  (i.e. between 0.0 and 1.0)
        # The default is:
        "strip_location": [0.05, 0.5, 0.9, 0.15]
    },
    # Define behaviour(s) for multi-date requests. If not declared, style only supports single-date requests.
    "multi_date": [
        # A multi-date handler.  Different handlers can be declared for different numbers of dates in a request.
        {
            # The count range for which this handler is to be used - a tuple of two ints, the smallest and
            # largest date counts for which this handler will be used.  Required.
            # For animations consider the RAM usage on OWS pods and keep the maximum time steps reasonable
            "allowed_count_range": [2, 10],
            # Re-sort data returned from the ODC so the order of date coordinates in the "time" dimension
            # matches the date order supplied by the user in the WMS request.
            # Optional. Defaults to False (date coordinates in the "time" dimension are always sorted chronologically)
            "preserve_user_date_order": True,
            # Flag that an animation should be generated. Without this only the most recent frame is returned. Optional.
            "animate": True,
            # A function, expressed in the standard format as described elsewhere in this example file.
            # The function is assumed to take one arguments, an xarray Dataset.
            # The function returns an xarray Dataset with a with multiple-bands per time step, output is defined
            # by colour ramp below
            "aggregator_function": {
                "function": "datacube_ows.band_utils.multi_date_pass"
            },
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
            "legend": {
                # Legend only covers positive part of ramp.
                "begin": "0.0",
                "end": "1.0"
            },
            # The feature info label for the multi-date animation performs a pixel drill.
            "feature_info_label": "ndvi_anim"
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
        # Only use positive part of range.
        # tick labels will be created for values that
        # are modulo 0 by this value
        "ticks_every": "10",
        "begin": "0.0",
        # appended to the title of the legend
        "units": "mm",
        # decimal places for tick labels
        # set to 0 for ints
        "decimal_places": 0,
    }
}

style_ndvi_cloudmask = {
    "name": "ndvi_cloudmask",
    "title": "NDVI with cloud masking",
    "abstract": "Normalised Difference Vegetation Index (with cloud masking) - a derived index that correlates well with the existence of vegetation",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "mapped_bands": True,
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
        "mapped_bands": True,
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
        "mapped_bands": True,
        "kwargs": {
            "band1": "swir2",
            "band2": "nir"
        }
    },
    "needed_bands": ["swir2", "nir"],
    "range": [0.0, 1.0],
}

style_wofs_frequency = {
    "name": "WOfS_frequency",
    "title": " Wet and Dry Count",
    "abstract": "WOfS summary showing the frequency of Wetness",
    "needed_bands": ["frequency"],
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "mapped_bands": True,
        "kwargs": {
            "band": "frequency",
        }
    },
    # Should the index_function value be shown as a derived band in GetFeatureInfo responses.
    # Defaults to true for style types with an index function.
    "include_in_feature_info": False,
    "color_ramp": [
        {
            "value": 0.002,
            "color": "#000000",
            "alpha": 0.0
        },
        {
            "value": 0.005,
            "color": "#8e0101",
            "alpha": 0.25
        },
        {
            "value": 0.01,
            "color": "#cf2200",
            "alpha": 0.75
        },
        {
            "value": 0.02,
            "color": "#e38400"
        },
        {
            "value": 0.05,
            "color": "#e3df00"
        },
        {
            "value": 0.1,
            "color": "#a6e300"
        },
        {
            "value": 0.2,
            "color": "#62e300"
        },
        {
            "value": 0.3,
            "color": "#00e32d"
        },
        {
            "value": 0.4,
            "color": "#00e384"
        },
        {
            "value": 0.5,
            "color": "#00e3c8"
        },
        {
            "value": 0.6,
            "color": "#00c5e3"
        },
        {
            "value": 0.7,
            "color": "#0097e3"
        },
        {
            "value": 0.8,
            "color": "#005fe3"
        },
        {
            "value": 0.9,
            "color": "#000fe3"
        },
        {
            "value": 1.0,
            "color": "#5700e3",
        }
    ],
    # defines the format of the legend generated
    # for this style
    "legend": {
        "units": "%",
        # Formatting 0.0-1.0 data as a percentage
        # setup ticks every 25% (0.25 raw)
        "begin": "0.00",
        "end": "1.00",
        "ticks_every": "0.25",
        "decimal_places": 2,
        # override tick labels.
        "tick_labels": {
            "0.00": {"label": "0"},
            "0.25": {"label": "25"},
            "0.50": {"label": "50"},
            "0.75": {"label": "75"},
            "1.00": {"label": "100"},
        }
    }
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
        "mapped_bands": True,
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
        "mapped_bands": True,
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
    "scale_range": [0.0, 3000.0]
    # N.B. The "pq_mask" section works the same as for the style types above.
}

# Describes a style which uses several bitflags to create a style

style_mangrove = {
    "name": "mangrove",
    "title": "Mangrove Cover",
    "abstract": "",
    # Each entry in the value_map dict
    # represents a band which is a bitflagged band
    "value_map": {
        "canopy_cover_class": [
            {
                "title": "Woodland",
                "abstract": "(20% - 50% cover)",
                # flags that all must match
                # in order for this style color to apply
                # "and" and "or" flags cannot be mixed
                "flags": {
                    "and": {
                        "woodland": True
                    }
                },
                "color": "#9FFF4C",
                # If specified as True (defaults to False)
                # Any areas which match this flag set
                # will be masked out completely, similar to using an extent
                # mask function or pq masking
                "mask": True
            },
            {
                "title": "Open Forest",
                "abstract": "(50% - 80% cover)",
                # flags that any may match
                # in order for this style color to apply
                # "and" and "or" flags cannot be mixed
                "flags": {
                    "or": {
                        "open_forest": True
                    }
                },
                "color": "#5ECC00",
                # Can set an optional alpha value (0.0 - 1.0) for these colors
                # will default to 1.0 (fully opaque)
                "alpha": 0.5
            },
            {
                "title": "Closed Forest",
                "abstract": "(>80% cover)",
                "flags": {
                    "closed_forest": True
                },
                "color": "#3B7F00"
            },
        ]
    }
    # NB: You can also do additional masking using the "pq_mask" section as described above for other
    #     style types.
}

# REUSABLE CONFIG FRAGMENTS - resource limit declarations

standard_resource_limits = {
    "wms": {
        # WMS/WMTS resource limits
        #
        # There are two independent resource limits applied to WMS/WMTS requests.  If either
        # limit is exceeded, then either the low-resolution summary product is used if one is defined, otherwise
        # indicative polygon showing the extent of the data is rendered.
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
        "max_datasets": 10,
        # Dataset cache rules.
        #
        # The number of datasets accessed by a GetMap/GetTile/GetCoverage query can be used to control
        # the cache-control headers returned by the query.
        #
        # Special cases:
        #
        # 1. No dataset_cache_rules element: Never return a cache-control header
        # 2. dataset_cache_rules set to an empty list []:  Return no-cache for all queries.
        # 3. General case: refer to comments embedded in example below.
        "dataset_cache_rules": [
            # Where number of datasets less than the min_datasets element of the first cache rule  (0-3 in this example):
            #       no-cache.
            {
                # Where number of datasets greater than or equal to the min_datasets value for this rule AND
                # less than the min_datasets of the next rule (4-7 in this example)
                "min_datasets": 4, # Must be greater than zero.  Blank tiles (0 datasets) are NEVER cached
                # The cache-control max-age for this rule, in seconds.
                "max_age": 86400,  # 86400 seconds = 24 hours
            },
            {
                # Rules must be sorted in ascending order of min_datasets values.
                "min_datasets": 8,
                "max_age": 604800,  # 604800 seconds = 1 week
            },
            # If a resource limit is exceeded, no-cache applies.
            # Summarising the cache-control results for this example:
            # 0-3 datasets: no-cache
            # 4-7 datasets: max-age: 86400
            # 8-10 datasets: max-age: 604800
            # 11+ datasets:  no-cache (over-limit behaviour.  Low-resolution summary product or shaded polygons.)
        ]
    },
    "wcs": {
        # wcs::max_datasets is the WCS equivalent of wms::max_datasets.  The main requirement for setting this
        # value is to avoid gateway timeouts on overly large WCS requests (and reduce server load).
        #
        # Defaults to zero, which is interpreted as no dataset limit.
        "max_datasets": 16,
        # dataset_cache_rules can be set independently for WCS requests.  This example omits it, so
        # WCS GetCoverage requests will always return no cache-control header.
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
        # Which web service(s) should be implemented by this instance
        # Optional, defaults: wms,wmts: True, wcs: False
        "services": {
            "wms": True,
            "wmts": True,
            "wcs": True
        },
        # Service title - appears e.g. in Terria catalog (required)
        "title": "Open web-services for the Open Data Cube",
        # Service URL.
        # A list of fully qualified URLs that the service can return
        # in the GetCapabilities documents based on the requesting url
        "allowed_urls": ["http://localhost/odc_ows",
                          "https://localhost/odc_ows",
                          "https://alternateurl.domain.org/odc_ows",
                          "http://127.0.0.1:8000/"],
        # URL that humans can visit to learn more about the service(s) or organization
        # should be fully qualified
        "info_url": "http://opendatacube.org",
        # Abstract - longer description of the service (Note this text is used for both WM(T)S and WCS)
        # Optional - defaults to empty string.
        "abstract": """This web-service serves georectified raster data from our very own special Open Data Cube instance.""",
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
        # Attribution.
        #
        # This provides a way to identify the source of the data used in a WMS layer or layers.
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
        # If fees are charged for the use of the service, these can be described here in free text.
        # If blank or not included, defaults to "none".
        "fees": "",
        # If there are constraints on access to the service, they can be described here in free text.
        # If blank or not included, defaults to "none".
        "access_constraints": "",
        # Supported co-ordinate reference systems. Any coordinate system supported by GDAL and Proj.4J can be used.
        # At least one CRS must be included.  At least one geographic CRS must be included if WCS is active.
        # WGS-84 (EPSG:4326) is strongly recommended, but not required.
        # Web Mercator (EPSG:3857) is strongly recommended, but is only required if WMTS is active.
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
            "EPSG:3111": {  # VicGrid94 for delwp.vic.gov.au
               "geographic": False,
                "horizontal_coord": "x",
                "vertical_coord": "y",
            },
            "EPSG:3577": {  # GDA-94, internal representation
                "geographic": False,
                "horizontal_coord": "x",
                "vertical_coord": "y",
            },
        },
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

    # Config items in the "wmts" section apply to the WMTS service only.
    # Note that most items in the "wms" section apply to the WMTS service
    # as well as the WMS service.
    #
    # Config items in the "wmts" section apply to all WMTS layers. All
    # entries are optional and the entire section may be omitted.
    "wmts": {
        # Datacube-ows always supports the standard "Google Maps" style
        # EPSG:3857-based tile matrix set.
        # If you require a custom tile matrix set (or sets) you can
        # define them here.
        "tile_matrix_sets": {
            # Example custom tile matrix set
            # Vic Grid (EPSG:3111) GeoCortex compatible tile matrix set
            # The key is the identifier for the Tile Matrix Set in WMTS instance.
            "vicgrid": {
                # The CRS of the Tile Matrix Set
                "crs": "EPSG:3111",
                # The coordinates (in the CRS above) of the upper-left
                # corner of the tile matrix set.
                "matrix_origin": (1786000.0, 3081000.0),
                # The size of tiles (must not exceed the WMS maximum tile size)
                "tile_size": (512, 512),
                # The scale denominators (as defined in the WMTS spec) for
                # the various zoom level from right out, to zoomed right in.
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
                # Defaults to (0,0), which means the first tile matrix
                # will have 1 tile (1x1), then doubling each time
                # (then 2x2, 4x4, 8x8, 16x16, etc.)
                #
                # (1, 0) means the width  of the first tile matrix has
                # is 2**1 = 2
                # So tiles side by side (2x1) (then 4x2, 8x4, 16x8, etc.)
                "matrix_exponent_initial_offsets": (1, 0),
            },
        }
    },

    # Config items in the "wcs" section apply to the WCS service to all WCS coverages
    # (unless over-ridden).
    "wcs": {
        # Supported WCS formats
        # NetCDF and GeoTIFF work "out of the box".  Other formats will require writing a Python function
        # to do the rendering.
        "formats": {
            # Key is the format name, as used in DescribeCoverage XML
            "GeoTIFF": {
                # Writing your own renderers is not documented.
                "renderers": {
                    "1": "datacube_ows.wcs1_utils.get_tiff",
                    "2": "datacube_ows.wcs2_utils.get_tiff",
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
                },
                "mime": "application/x-netcdf",
                "extension": "nc",
                "multi-time": True,
            }
        },
        # The wcs:native_format must be declared in wcs:formats dict above.
        # Maybe over-ridden at the named layer (i.e. coverage)
        # level.
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
                "title": "Digital Earth Australia",
                # The associated - e.g. URL for the attributed organisation
                "url": "http://www.ga.gov.au/dea",
                # Logo image - e.g. for the attributed organisation
                "logo": {
                    # Image width in pixels (optional)
                    "width": 370,
                    # Image height in pixels (optional)
                    "height": 73,
                    # URL for the logo image. (required if logo specified)
                    "url": "https://www.ga.gov.au/__data/assets/image/0011/61589/GA-DEA-Logo-Inline-370x73.png",
                    # Image MIME type for the logo - should match type referenced in the logo url (required if logo specified.)
                    "format": "image/png",
                }
            },
            # Folder-type layers include a list of sub-layers
            "layers": [
                {
                    # NOTE: This layer IS a mappable "named layer" that can be selected in GetMap requests
                    # Every layer must have a distinct human-readable title and abstract.
                    "title": "Level 2 DEA NBART Landsat-8 Data",
                    "abstract": "Imagery from DEA's Level 2 NBART Analysis-Ready Data Set",
                    # Mappable layers must have a name - this is the layer name that appears in WMS GetMap
                    # or WMTS GetTile requests and the coverage name that appears in WCS
                    # DescribeCoverage/GetCoverage requests.
                    "name": "ls8_nbart_albers",
                    # The ODC product name for the associated data product
                    "product_name": "ls8_nbart_albers",

                    # Supported bands, mapping native band names to a list of possible aliases.
                    # See reusable band alias maps above for documentation.
                    "bands": landsat8_bands,
                    # Resource limits.
                    # See reusable resource limit declarations above for documentation.
                    "resource_limits": standard_resource_limits,
                    # If "dynamic" is False (the default) the the ranges for the product are cached in memory.
                    # Dynamic products slow down the generation of the GetCapabilities document - use sparingly.
                    "dynamic": False,
                    # The resolution of the time access.  Optional. Allowed values are:
                    # * "raw" (the default - data with timestamps to be according to the local solar day)
                    # * "day" (daily data with date-resolution time stamps)
                    # * "month" (for monthly summary datasets)
                    # * "year" (for annual summary datasets)
                    "time_resolution": "raw",
                    # The "native" CRS.  (as used for resource management calculations and WCS metadata)
                    # (Used for resource management calculations and WCS metadata)
                    # Must be in the global "published_CRSs" list.
                    # Can be omitted if the product has a single native CRS, as this will be used in preference.
                    "native_crs": "EPSG:3577",
                    # The native resolution (x,y)
                    # (Used for resource management calculations and WCS metadata)
                    # This is the number of CRS units (e.g. degrees, metres) per pixel in the horizontal
                    # and vertical directions for the native CRS.
                    # Can be omitted if the product has a single native resolution, as this will be used in preference.
                    # E.g. for EPSG:3577; (25.0,25.0) for Landsat-8 and (10.0,10.0 for Sentinel-2)
                    "native_resolution": [25.0, 25.0],
                    "flags": {
                        # Data may include flags that mark which pixels have missing or poor-quality data,
                        # or contain cloud, or cloud-shadow, etc.  This section describes how
                        # datacube_ows handles such flags.  The entire section may be omitted if no
                        # flag masking is to be supported by the layer.
                        #
                        # Items in this section affect WMS/WMTS requests only, unless explicitly stated
                        # otherwise.
                        #
                        # The name of the measurement band for the pixel-quality flags
                        # Pixel-quality bitmasks and flags can be used for image/data masking.
                        #
                        # Required, unless the whole "flags" section is empty or None.
                        #
                        "band": "pixelquality",
                        # Sometimes the pixel quality band is packaged in a separate ODC product
                        # If this is the case, you can specify this product with the "flags::product"
                        # element.  If "flags::band" is set but "flags::product" is omitted, then the
                        # pixel quality band is assumed to be included in the main data product.
                        "product": "ls8_pq_albers",
                        # Flags Fuse func
                        # Determines how multiple dataset arrays are compressed into a single time array for
                        # the PQ layer
                        #
                        # Two formats are supported:
                        # 1. A string containing a fully qualified path to a python function (e.g. as shown below)
                        #
                        # 2. A dict containing the following elements:
                        #    a) "function" (required): A string containing the fully qualified path to a python function
                        #    b) "args" (optional): An array of additional positional arguments that will always be passed to the function.
                        #    c) "kwargs" (optional): An array of additional keyword arguments that will always be passed to the function.
                        #    d) "mapped_bands" (optional): Boolean (defaults to False). If true, a band mapping function is passed
                        #       to the function as a keyword argument named "band_mapper".  This is useful if you are passing band aliases
                        #       to the function in the args or kwargs.  The band_mapper allows the index function to convert band aliases to
                        #       to band names.
                        #
                        # Passed directly to the datacube load_data function.  Defaults to None.
                        "fuse_func": "datacube.helpers.ga_pq_fuser",
                        # Flags Ignore time
                        # Doesn't use the time from the data to find a corresponding mask layer
                        # Used when you have a mask layer that doesn't have a time dimension
                        #
                        # Defaults to False
                        "ignore_time": False,
                        # Values of flags listed here are not included in GetFeatureInfo responses.
                        # (defaults to empty list)
                        "ignore_info_flags": [],
                        # Set to true if the pq product dataset extents include nodata regions.
                        #
                        # Default to False.
                        "manual_merge": False,
                    },
                    # The image_processing section must be supplied.
                    "image_processing": {
                        # Extent mask function
                        # Determines what portions of dataset is potentially meaningful data.
                        #
                        # All the formats described above for "flags->fuse_func" are
                        # supported here as well.
                        #
                        # Additionally, multiple extent mask functions can be specified as a list of any of
                        # supported formats.  The result is the intersection of all supplied mask functions.
                        #
                        # The function is assumed to take two arguments, data (an xarray Dataset) and band (a band name).  (Plus any additional
                        # arguments required by the args and kwargs values in format 3, possibly including product_cfg.)
                        #
                        "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                        # Bands to always fetch from the Datacube, even if it is not used by the active style.
                        # Useful for when a particular band is always needed for the extent_mask_func,
                        "always_fetch_bands": [],
                        # Fuse func
                        #
                        # Determines how multiple dataset arrays are compressed into a single time array
                        # All the formats described above for "extent_mask_func" are supported here as well.
                        # (Passed through to datacube load_data() function.)
                        #
                        # Defaults to None.
                        "fuse_func": None,
                        # Set to true if the band product dataset extents include nodata regions.
                        # Defaults to False.
                        "manual_merge": False,
                        # Apply corrections for solar angle, for "Level 1" products.
                        # (Defaults to false - should not be used for NBAR/NBAR-T or other Analysis Ready products
                        "apply_solar_corrections": False,
                    },
                    # If the WCS section is not supplied, then this named layer will NOT appear as a WCS
                    # coverage (but will still be a layer in WMS and WMTS).
                    "wcs": {

                        # The default bands for a WCS request.
                        # 1. Must be provided if WCS is activated.
                        # 2. Must contain at least one band.
                        # 3. All bands must exist in the band index.
                        # 4. Bands may be referred to by either native name or alias
                        "default_bands": ["red", "green", "blue"],
                        # The native format advertised for the coverage.
                        # Must be one of the formats defined
                        # in the global wcs formats section.
                        # Optional: if not supplied defaults to the
                        # globally defined native_format.
                        "native_format": "NetCDF"
                    },
                    # Each key of the identifiers dictionary must match a name from the authorities dictionary
                    # in the global section.  The values are the identifiers defined for this layer by that
                    # authority.
                    "identifiers": {
                        "auth": "ls8_ard",
                        "idsrus": "12345435::0054234::GHW::24356-splunge"
                    },
                    # The urls section provides the values that are included in the FeatureListURLs and
                    # DataURLs sections of a WMS GetCapabilities document.
                    # Multiple of each may be defined per product.
                    #
                    # The entire section the "features and "data" subsections within it are optional. The
                    # default is an empty list(s).
                    #
                    # Each individual entry must include a url and MIME type format.
                    #
                    # FeatureListURLs point to "a list of the features represented in a Layer".
                    # DataURLs "offer a link to the underlying data represented by a particular layer"
                    "urls": {
                        "features": [
                            {
                                "url": "http://domain.tld/path/to/page.html",
                                "format": "text/html"
                            },
                            {
                                "url": "http://another-domain.tld/path/to/image.png",
                                "format": "image/png"
                            }
                        ],
                        "data": [
                            {
                                "url": "http://abc.xyz/data-link.xml",
                                "format": "application/xml"
                            }
                        ]
                    },
                    # The feature_info section is optional.
                    "feature_info": {
                        # Include an additional list of utc dates in the WMS Get Feature Info. Defaults to False.
                        # HACK: only used for GSKY non-solar day lookup.
                        "include_utc_dates": False,
                        # Optional: custom data to be included in GetFeatureInfo responses.  Defaults to an empty
                        # dictionary.
                        # Keys are the keys to insert into the GetFeatureInfo response.  Values are function wrappers,
                        # using the same format options available elsewhere in the config.  Specified functions are
                        # expected to be passed a dictionary of band values (as parameter "data") and return any data
                        # that can be serialised to JSON.
                        "include_custom": {
                            "timeseries": {
                                "function": "datacube_ows.ogc_utils.feature_info_url_template",
                                "mapped_bands": False,
                                "kwargs": {
                                    "template": "https://host.domain/path/{data['f_id']:06}.csv"
                                }
                            }
                        }
                    },
                    # The sub_products section is optional.
                    "sub_products": {
                        # A function that extracts the "sub-product" id (e.g. path number) from a dataset.
                        # Function should return a (small) integer.  If None or not specified, the product
                        # has no sub-layers.
                        # All the formats supported for extent_mask_func as described above are supported here.
                        # The function is assumed to take a datacube dataset object and return an integer
                        # sub-product id.
                        "extractor": "datacube_ows.ogc_utils.ls8_subproduct",
                        # A prefix used to describe the sub-layer in the GetCapabilities response.
                        # E.g. sub-layer 109 will be described as "Landsat Path 109"
                        "label": "Landsat Path",
                    },
                    # Style definitions
                    # The "styling" section is required
                    "styling": {
                        # The default_style is the style used when no style is explicitly given in the
                        # request.  If given, it must be the name of a style in the "styles" list. If
                        # not explictly defined it defaults to the first style in "styles" list.
                        "default_style": "simple_rgb",
                        # The "styles" list must be explicitly supplied, and must contain at least one
                        # style.  See reusable style definitions above for more documentation on
                        # defining styles.
                        "styles": [
                            style_rgb, style_rgb_cloudmask, style_rgb_cloud_and_shadowmask,
                            style_ext_rgb, style_ls8_allband_false_colour, style_infrared_false_colour,
                            style_pure_ls8_coastal_aerosol, style_pure_ls8_blue,
                            style_pure_ls8_green, style_pure_ls8_red,
                            style_pure_ls8_nir, style_pure_ls8_swir1, style_pure_ls8_swir2,
                            style_ndvi, style_ndvi_cloudmask,
                            style_ndwi, style_ndbi,
                            style_cloud_mask,
                            style_rgb_ndvi
                        ]
                    }
                }, #### End of ls8_nbart_albers product
                {
                    # NOTE: This layer IS a mappable "named layer" that can be selected in GetMap requests
                    "title": "Level 1 USGS Landsat-8 Public Data Set",
                    "abstract": "Imagery from the Level 1 Landsat-8 USGS Public Data Set",
                    "name": "ls8_level1_pds",
                    "product_name": "ls8_level1_usgs",
                    "bands": landsat8_bands,
                    "resource_limits": standard_resource_limits,
                    # native_crs and native_resolution taken from product meta-data
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
                        "always_fetch_bands": ["quality"],
                        "fuse_func": None,
                        "manual_merge": True,
                        # Apply corrections for solar angle, for "Level 1" products.
                        # (Defaults to false - should not be used for NBAR/NBAR-T or other Analysis Ready products
                        "apply_solar_corrections": True
                    },
                    "wcs": {
                        "default_bands": ["red", "green", "blue"],
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
                }, ##### End of ls8_level1_pds product definition.


                {
                    # NOTE: This layer IS a mappable "named layer" that can be selected in GetMap requests
                    "title": "WOfS Summary",
                    "abstract": "Water Observations from Space - Summary",
                    "name": "wofs_summary",
                    "product_name": "wofs_summary",
                    "bands": {"frequency": []},
                    "resource_limits": standard_resource_limits,
                    "flags": None,
                    "native_crs": "EPSG:3857",
                    "native_resolution": [25.0, 25.0],
                    "image_processing": {
                        "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                        "fuse_func": "datacube_ows.wms_utils.wofls_fuser",
                    },
                    "wcs": {
                        "default_bands": ["frequency"],
                    },
                    "styling": {
                        "styles": [
                            style_wofs_frequency
                        ]
                    }
                }, ##### End of wofs_summary product definition.

            ]
        },  ### End of Landsat 8 folder.
        {
            # NOTE: This layer is a folder - it is NOT "named layer" that can be selected in GetMap requests
            "title": "Sentinel-2 Products",
            "abstract": "Products containing data ultimately derived from ESA's Sentinel-2 satellite.",
            "keywords": [
                "sentinel2",
            ],
            "layers": [
                {
                    # NOTE: This layer IS a mappable "named layer" that can be selected in GetMap requests
                    "title": "Near Real-Time images from Sentinel-2 Satellites",
                    "abstract": "Imagery from the ESA Sentinel2 Satellites",
                    "name": "sentinel2_nrt",
                    # Multi-product layers merge two separate datacube products with similar metadata (i.e.
                    # projections, bands, pixel quality band format, etc.)
                    "multi_product": True,
                    # For multi-product layers, use "product_names" for the list of constituent ODC products.
                    "product_names": ["s2a_nrt_granule", "s2b_nrt_granule"],
                    "bands": sentinel2_bands,
                    "resource_limits": standard_resource_limits,
                    # Near Real Time datasets are being regularly updated - do not cache ranges in memory.
                    "dynamic": True,
                    "native_crs": "EPSG:3577",
                    "native_resolution": [10.0, 10.0],
                    "flags": {
                        "band": "quality",
                        "ignore_time": False,
                        "ignore_info_flags": [],
                        "manual_merge": False,
                    },
                    "image_processing": {
                        "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                        "always_fetch_bands": [],
                        "fuse_func": None,
                        "manual_merge": False,
                        "apply_solar_corrections": False,
                    },
                    "wcs": {
                        "default_bands": ["red", "green", "blue"],
                    },
                    "identifiers": {
                        "auth": "s2_nrt_multi",
                    },
                    "urls": {
                        "features": [
                            {
                                "url": "http://domain.tld/path/to/page.html",
                                "format": "text/html"
                            }
                        ],
                        "data": [
                            {
                                "url": "http://abc.xyz/data-link.xml",
                                "format": "application/xml"
                            }
                        ]
                    },
                    "styling": {
                        "default_style": "simple_rgb",
                        "styles": [style_rgb],
                    }
                } ##### End of sentinel2_nrt multi-product definition
            ],
        },   #### End of Sentinel-2 folder
        {
            # NOTE: This layer IS a mappable "named layer" that can be selected in GetMap requests
            # NOTE: Named layers can sit at the same heirarchical level as folder layers.
            "name": "mangrove_cover",
            "title": "Mangrove Canopy Cover",
            "abstract": "Mangrove Canopy Cover - example of bitflag value-mapped style.",
            "product_names": "mangrove_cover",
            "bands": {"canopy_cover_class": [], "extent": []},
            "resource_limits": standard_resource_limits,
            "flags": None,
            "image_processing": {
                "extent_mask_func": "datacube_ows.ogc_utils.mask_by_extent_flag",
                "always_fetch_bands": ["extent"],
                "fuse_func": None,
                "manual_merge": False,
                "apply_solar_corrections": False,
            },
            "wcs": {
                "default_bands": ["canopy_cover_class"],
            },
            "identifiers": {
                "auth": "mangrove_canopy_cover",
            },
            "urls": {
                "features": [
                    {
                        "url": "http://domain.tld/path/to/page.html",
                        "format": "text/html"
                    }
                ],
                "data": [
                    {
                        "url": "http://abc.xyz/data-link.xml",
                        "format": "application/xml"
                    }
                ]
            },
            "styling": {
                "default_style": "mangrove",
                "styles": [style_mangrove],
            }
        } ##### End of mangrove_cover definition
    ]  ##### End of "layers" list.
} #### End of example configuration object
