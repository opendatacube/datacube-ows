# pylint: skip-file
# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import os

if os.environ.get("DATACUBE_OWS_CFG", "").startswith("integration_tests"):
    cfgbase = "integration_tests.cfg."
    trans_dir = "."
else:
    cfgbase = "config."
    trans_dir = "/code"


# THIS IS A TESTING FILE
# Please refer to datacube_ows/ows_cfg_example.py for EXAMPLE CONFIG

# REUSABLE CONFIG FRAGMENTS - Band alias maps
bands_sentinel = {
    "B01": ["coastal_aerosol"],
    "B02": ["blue"],
    "B03": ["green"],
    "B04": ["red"],
    "B05": ["red_edge_1"],
    "B06": ["red_edge_2"],
    "B07": ["red_edge_3"],
    "B08": ["nir", "nir_1"],
    "B8A": ["nir_narrow", "nir_2"],
    "B09": ["water_vapour"],
    "B11": ["swir_1", "swir_16"],
    "B12": ["swir_2", "swir_22"],
    "AOT": ["aerosol_optical_thickness"],
    "WVP": ["scene_average_water_vapour"],
    "SCL": ["mask", "qa"],
}


bands_fc_3 = {
    "bs": ["bare_soil"],
    "pv": ["photosynthetic_vegetation", "green_vegetation"],
    "npv": ["non_photosynthetic_vegetation", "brown_vegetation"],
    "ue": [],
}

bands_sentinel2_ard_nbart = {
    "nbart_coastal_aerosol": [
        "nbar_coastal_aerosol",
        "coastal_aerosol",
        "nbart_coastal_aerosol",
        "nbart_narrow_blue",
        "nbar_narrow_blue",
        "narrow_blue",
    ],
    "nbart_blue": ["nbar_blue", "blue", "nbart_blue"],
    "nbart_green": ["nbar_green", "green", "nbart_green"],
    "nbart_red": ["nbar_red", "red", "nbart_red"],
    "nbart_red_edge_1": ["nbar_red_edge_1", "red_edge_1", "nbart_red_edge_1"],
    "nbart_red_edge_2": ["nbar_red_edge_2", "red_edge_2", "nbart_red_edge_2"],
    "nbart_red_edge_3": ["nbar_red_edge_3", "red_edge_3", "nbart_red_edge_3"],
    "nbart_nir_1": ["nbar_nir_1", "nir", "nir_1", "nbart_nir_1"],
    "nbart_nir_2": ["nbar_nir_2", "nir2", "nbart_nir_2"],
    "nbart_swir_2": ["nbar_swir_2", "swir_2", "nbart_swir_2"],
    "nbart_swir_3": ["nbar_swir_3", "swir_3", "nbart_swir_3"],
    "fmask": ["fmask", "fmask_alias"],
}


# REUSABLE CONFIG FRAGMENTS - Style definitions

s2_nrt_fmask = [
    {
        "band": "fmask_alias",
        "values": [0, 2, 3],
        "invert": True,
    },
    {
        "band": "land",
        "invert": True,
        "values": [1],
    },
]


style_s2_mndwi = {
    # Cannot reuse landsat as we need swir_2 to landsat's swir_1
    "name": "mndwi",
    "title": "Modified Normalised Difference Water Index - Green, SWIR",
    "abstract": "Modified Normalised Difference Water Index - a derived index that correlates well with the existence of water (Xu 2006)",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "mapped_bands": True,
        "kwargs": {"band1": "nbart_green", "band2": "nbart_swir_2"},
    },
    "needed_bands": ["nbart_green", "nbart_swir_2"],
    "color_ramp": [
        {"value": -0.1, "color": "#f7fbff", "alpha": 0.0},
        {"value": 0.0, "color": "#d8e7f5"},
        {"value": 0.2, "color": "#b0d2e8"},
        {"value": 0.4, "color": "#73b3d8"},
        {"value": 0.6, "color": "#3e8ec4"},
        {"value": 0.8, "color": "#1563aa"},
        {"value": 1.0, "color": "#08306b"},
    ],
    "pq_masks": s2_nrt_fmask,
    "multi_date": [
        {
            "allowed_count_range": [2, 2],
            "preserve_user_date_order": True,
            "aggregator_function": {
                "function": "datacube_ows.band_utils.multi_date_delta"
            },
            "mpl_ramp": "RdYlBu",
            "range": [-1.0, 1.0],
            "pq_masks": s2_nrt_fmask,
            "legend": {
                "begin": "-1.0",
                "end": "1.0",
                "ticks": [
                    "-1.0",
                    "0.0",
                    "1.0",
                ],
            },
            "feature_info_label": "mndwi_delta",
        }
    ],
}

style_ls_simple_rgb = {
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
        "green": {"green": 1.0},
        "blue": {"blue": 1.0},
    },
    # The raw band value range to be compressed to an 8 bit range for the output image tiles.
    # Band values outside this range are clipped to 0 or 255 as appropriate.
    "scale_range": [0.0, 3000.0],
    "pq_masks": [
        {
            "band": "SCL",
            "invert": True,
            "values": [0],
        }
    ],
    "legend": {
        "show_legend": True,
        "url": {
            "en": "https://user-images.githubusercontent.com/4548530/112120795-b215b880-8c12-11eb-8bfa-1033961fb1ba.png"
        }
    }

}

style_fc_c3_rgb_unmasked = {
    "name": "fc_rgb_unmasked",
    "title": "Three-band Fractional Cover Unmasked (Warning: includes invalid data)",
    "abstract": "Fractional cover medians - red is bare soil, green is green vegetation and blue is non-green vegetation",
    "components": {
        "red": {"bs": 1.0},
        "green": {"pv": 1.0},
        "blue": {"npv": 1.0},
    },
    "scale_range": [0.0, 100.0],
    "legend": {
        "show_legend": True,
        "url": "https://data.dea.ga.gov.au/fractional-cover/FC_legend.png",
    },
}

style_ls_simple_rgb_clone = {
    "inherits": {"layer": "s2_l2a", "style": "simple_rgb"},
    "name": "style_ls_simple_rgb_clone",
    "title": "Simple RGB Clone",
    "scale_range": [0.0, 3000.0],
}

style_infrared_false_colour = {
    "name": "infra_red",
    "title": "False colour multi-band infra-red",
    "abstract": "Simple false-colour image, using the near and short-wave infra-red bands",
    "components": {
        "red": {
            "B11": 1.0,
            # The special dictionary value 'scale_range' can be used to provide a component-specific
            # scale_range that overrides the style scale_range below.
            # (N.B. if you are unlucky enough to have a native band called "scale_range", you can access it
            # by defining a band alias.)
            "scale_range": [5.0, 4000.0],
        },
        "green": {
            "B12": 1.0,
            "scale_range": [25.0, 4000.0],
        },
        "blue": {
            "B08": 1.0,
            "scale_range": [0.0, 3000.0],
        },
    },
    # The style scale_range can be omitted if all components have a component-specific scale_range defined.
    # "scale_range": [0.0, 3000.0]
}

style_sentinel_pure_blue = {
    "name": "blue",
    "title": "Blue - 490",
    "abstract": "Blue band, centered on 490nm",
    "components": {"red": {"blue": 1.0}, "green": {"blue": 1.0}, "blue": {"blue": 1.0}},
    "scale_range": [0.0, 3000.0],
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
    "legend": {
        "units": "dimensionless",
        "tick_labels": {
            "0.0": {
                "label": "low",
            },
            "1.0": {
                "label": "high",
            }
        }
    }
}

style_ndvi_expr = {
    "name": "ndvi_expr",
    "title": "NDVI",
    "abstract": "Normalised Difference Vegetation Index - a derived index that correlates well with the existence of vegetation",
    "index_expression": "(nir-red)/(nir+red)",
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

style_ls_ndvi_delta = {
    "name": "ndvi_delta",
    "title": "NDVI - Red, NIR",
    "abstract": "Normalised Difference Vegetation Index - a derived index that correlates well with the existence of vegetation",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "mapped_bands": True,
        "kwargs": {"band1": "nir", "band2": "red"},
    },
    "needed_bands": ["red", "nir"],
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
    "multi_date": [
        {
            "allowed_count_range": [2, 2],
            "animate": False,
            "preserve_user_date_order": True,
            "aggregator_function": {
                "function": "datacube_ows.band_utils.multi_date_delta",
            },
            "mpl_ramp": "RdYlBu",
            "range": [-1.0, 1.0],
            "legend": {
                "begin": "-1.0",
                "end": "1.0",
                "ticks": [
                    "-1.0",
                    "0.0",
                    "1.0",
                ]
            },
            "feature_info_label": "ndvi_delta",
        },
        {"allowed_count_range": [3, 4], "animate": True},
    ],
}

styles_s2_list = [
    style_ls_simple_rgb,
    style_ls_simple_rgb_clone,
    style_infrared_false_colour,
    style_sentinel_pure_blue,
    style_ndvi,
    style_ndvi_expr,
    style_rgb_ndvi,
    style_ls_ndvi_delta,
]

style_s2_ndci = {
    "name": "ndci",
    "title": "Normalised Difference Chlorophyll Index - Red Edge, Red",
    "abstract": "Normalised Difference Chlorophyll Index - a derived index that correlates well with the existence of chlorophyll",
    "index_function": {
        "function": "datacube_ows.band_utils.sentinel2_ndci",
        "mapped_bands": True,
        "kwargs": {
            "b_red_edge": "nbart_red_edge_1",
            "b_red": "nbart_red",
            "b_green": "nbart_green",
            "b_swir": "nbart_swir_2",
        },
    },
    "needed_bands": ["nbart_red_edge_1", "nbart_red", "nbart_green", "nbart_swir_2"],
    "color_ramp": [
        {
            "value": -0.1,
            "color": "#1696FF",
        },
        {"value": -0.1, "color": "#1696FF"},
        {
            "value": 0.0,
            "color": "#00FFDF",
        },
        {
            "value": 0.1,
            "color": "#FFF50E",
        },
        {
            "value": 0.2,
            "color": "#FFB50A",
        },
        {
            "value": 0.4,
            "color": "#FF530D",
        },
        {
            "value": 0.5,
            "color": "#FF0000",
        },
    ],
    "legend": {
        "begin": "-0.1",
        "end": "0.5",
        "ticks_every": "0.1",
        "units": "unitless",
        "tick_labels": {"-0.1": {"prefix": "<"}, "0.5": {"prefix": ">"}},
    },
}


styles_s2_ga_list = [
    style_s2_ndci,
    style_s2_mndwi,
]

# Describes a style which uses several bitflags to create a style

# REUSABLE CONFIG FRAGMENTS - resource limit declarations
dataset_cache_rules = [
    {
        "min_datasets": 5,
        "max_age": 60 * 60 * 24,
    },
    {
        "min_datasets": 9,
        "max_age": 60 * 60 * 24 * 7,
    },
    {
        "min_datasets": 17,
        "max_age": 60 * 60 * 24 * 30,
    },
    {
        "min_datasets": 65,
        "max_age": 60 * 60 * 24 * 120,
    },
]

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


reslim_for_sentinel2 = {
    "wms": {
        "zoomed_out_fill_colour": [150, 180, 200, 160],
        "min_zoom_factor": 5.9,
        "dataset_cache_rules": dataset_cache_rules,
    },
    "wcs": {
        "max_datasets": 32,  # Defaults to no dataset limit
    },
}

reslim_continental = {
    "wms": {
        "zoomed_out_fill_colour": [150, 180, 200, 160],
        "min_zoom_factor": 10.0,
        # "max_datasets": 16, # Defaults to no dataset limit
        "dataset_cache_rules": dataset_cache_rules,
    },
    "wcs": {
        "max_datasets": 32,  # Defaults to no dataset limit
    },
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
        "message_file": f"{trans_dir}/integration_tests/cfg/message.po",
        "translations_directory": f"{trans_dir}/integration_tests/cfg/translations",
        "supported_languages": ["en", "de"],

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

        "caps_cache_maxage": 5,
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
        "default_desc_cache_maxage": 300, # 5 minutes
    },  ###### End of "wcs" section
    # Products published by this datacube_ows instance.
    # The layers section is a list of layer definitions.  Each layer may be either:
    # 1) A folder-layer.  Folder-layers are not named and can contain a list of child layers.  Folder-layers are
    #    only used by WMS and WMTS - WCS does not support a hierarchical index of coverages.
    # 2) A mappable named layer that can be requested in WMS GetMap or WMTS GetTile requests.  A mappable named layer
    #    is also a coverage, that may be requested in WCS DescribeCoverage or WCS GetCoverage requests.
    "layers": [
        {
            "title": "s2",
            "abstract": "Images from the sentinel 2 satellite",
            "keywords": ["sentinel2"],
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
                    "url": "https://user-images.githubusercontent.com/4548530/112120795-b215b880-8c12-11eb-8bfa-1033961fb1ba.png",
                    # Image MIME type for the logo - should match type referenced in the logo url (required if logo specified.)
                    "format": "image/png",
                },
            },
            "label": "sentinel2",
            "layers": [
                {
                    "title": "Surface reflectance (Sentinel-2)",
                    "name": "s2_l2a",
                    "abstract": """layer s2_l2a""",
                    "product_name": "s2_l2a",
                    "bands": bands_sentinel,
                    "dynamic": True,
                    "resource_limits": reslim_continental,
                    "image_processing": {
                        "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                        "always_fetch_bands": [],
                        "manual_merge": False,  # True
                        "apply_solar_corrections": False,
                    },
                    "flags": [
                        {
                            "band": "SCL",
                            "product": "s2_l2a",
                            "ignore_time": False,
                            "ignore_info_flags": [],
                            # This band comes from main product, so cannot set flags manual_merge independently
                            # "manual_merge": True,
                        },
                    ],
                    "native_crs": "EPSG:3857",
                    "native_resolution": [30.0, -30.0],
                    "styling": {
                        "default_style": "simple_rgb",
                        "styles": styles_s2_list,
                    },
                },
                {
                    "inherits": {
                        "layer": "s2_l2a",
                    },
                    "title": "s2_l2a Clone",
                    "abstract": "Imagery from the s2_l2a Clone",
                    "name": "s2_l2a_clone",
                    "low_res_product_name": "s2_l2a",
                    "image_processing": {
                        "extent_mask_func": [],
                        "manual_merge": True,
                        "apply_solar_corrections": True,
                    },
                    "resource_limits": {
                        "wcs": {
                            "max_image_size": 2000 * 2000 * 3 * 2,
                        }
                    },
                    "time_axis": {
                        "time_interval": 1
                    },
                    "patch_url_function": f"{cfgbase}utils.trivial_identity",
                },
            ]
        },
        {
            "title": "DEA Config Samples",
            "abstract": "",
            "layers": [
                {
                    "title": "DEA Surface Reflectance (Sentinel-2)",
                    "name": "s2_ard_granule_nbar_t",
                    "abstract": """Sentinel-2 Multispectral Instrument - Nadir BRDF Adjusted Reflectance + Terrain Illumination Correction (Sentinel-2 MSI)
                This product has been corrected to account for variations caused by atmospheric properties, sun position and sensor view angle at time of image capture.
                These corrections have been applied to all satellite imagery in the Sentinel-2 archive. This is undertaken to allow comparison of imagery acquired at different times, in different seasons and in different geographic locations.
                These products also indicate where the imagery has been affected by cloud or cloud shadow, contains missing data or has been affected in other ways. The Surface Reflectance products are useful as a fundamental starting point for any further analysis, and underpin all other optical derived Digital Earth Australia products.
                This is a definitive archive of daily Sentinel-2 data. This is processed using correct ancillary data to provide a more accurate product than the Near Real Time.
                The Surface Reflectance product has been corrected to account for variations caused by atmospheric properties, sun position and sensor view angle at time of image capture. These corrections have been applied to all satellite imagery in the Sentinel-2 archive.
                The Normalised Difference Chlorophyll Index (NDCI) is based on the method of Mishra & Mishra 2012, and adapted to bands on the Sentinel-2A & B sensors.
                The index indicates levels of chlorophyll-a (chl-a) concentrations in complex turbid productive waters such as those encountered in many inland water bodies. The index has not been validated in Australian waters, and there are a range of environmental conditions that may have an effect on the accuracy of the derived index values in this test implementation, including:
                - Influence on the remote sensing signal from nearby land and/or atmospheric effects
                - Optically shallow water
                - Cloud cover
                Mishra, S., Mishra, D.R., 2012. Normalized difference chlorophyll index: A novel model for remote estimation of chlorophyll-a concentration in turbid productive waters. Remote Sensing of Environment, Remote Sensing of Urban Environments 117, 394–406. https://doi.org/10.1016/j.rse.2011.10.016
                For more information see http://pid.geoscience.gov.au/dataset/ga/129684
                https://cmi.ga.gov.au/data-products/dea/190/dea-surface-reflectance-nbart-sentinel-2-msi
                For service status information, see https://status.dea.ga.gov.au
                                """,
                    "multi_product": True,
                    "product_names": ["ga_s2am_ard_3", "ga_s2bm_ard_3"],
                    "low_res_product_names": ["ga_s2am_ard_3", "ga_s2bm_ard_3"],
                    "bands": bands_sentinel2_ard_nbart,
                    "resource_limits": reslim_for_sentinel2,
                    "native_crs": "EPSG:3577",
                    "native_resolution": [10.0, -10.0],
                    "image_processing": {
                        "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                        "always_fetch_bands": [],
                        "manual_merge": False,
                    },
                    "flags": [
                        {
                            "band": "fmask_alias",
                            "products": ["ga_s2am_ard_3", "ga_s2bm_ard_3"],
                            "ignore_time": False,
                            "ignore_info_flags": []
                        },
                        {
                            "band": "land",
                            "products": ["geodata_coast_100k", "geodata_coast_100k"],
                            "ignore_time": True,
                            "ignore_info_flags": []
                        },
                    ],
                    "styling": {"default_style": "ndci", "styles": styles_s2_ga_list},
                },
                {
                    "inherits": {
                        "layer": "s2_ard_granule_nbar_t",
                    },
                    "title": "DEA Surface Reflectance Mosaic (Sentinel-2)",
                    "name": "s2_ard_latest_mosaic",
                    "multi_product": True,
                    "abstract": """Sentinel-2 Multispectral Instrument - Nadir BRDF Adjusted Reflectance + Terrain Illumination Correction (Sentinel-2 MSI)

Latest imagery mosaic with no time dimension.
                    """,
                    "mosaic_date_func": {
                        "function": "datacube_ows.ogc_utils.rolling_window_ndays",
                        "pass_layer_cfg": True,
                        "kwargs": {
                            "ndays": 6,
                        }
                    }
                },
                {
                    "title": "DEA Fractional Cover (Landsat)",
                    "name": "ga_ls_fc_3",
                    "abstract": """Geoscience Australia Landsat Fractional Cover Collection 3
                Fractional Cover (FC), developed by the Joint Remote Sensing Research Program, is a measurement that splits the landscape into three parts, or fractions:
                green (leaves, grass, and growing crops)
                brown (branches, dry grass or hay, and dead leaf litter)
                bare ground (soil or rock)
                DEA uses Fractional Cover to characterise every 30 m square of Australia for any point in time from 1987 to today.
                https://cmi.ga.gov.au/data-products/dea/629/dea-fractional-cover-landsat-c3
                For service status information, see https://status.dea.ga.gov.au""",
                    "product_name": "ga_ls_fc_3",
                    "bands": bands_fc_3,
                    "resource_limits": reslim_for_sentinel2,
                    "dynamic": True,
                    "native_crs": "EPSG:3577",
                    "native_resolution": [25, -25],
                    "image_processing": {
                        "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                        "always_fetch_bands": [],
                        "manual_merge": False,
                    },
                    "flags": [
                        # flags is now a list of flag band definitions - NOT a dictionary with identifiers
                        {
                            "band": "land",
                            "product": "geodata_coast_100k",
                            "ignore_time": True,
                            "ignore_info_flags": [],
                        },
                        {
                            "band": "water",
                            "product": "ga_ls_wo_3",
                            "ignore_time": False,
                            "ignore_info_flags": [],
                            "fuse_func": "datacube_ows.wms_utils.wofls_fuser",
                        },
                    ],
                    "styling": {
                        "default_style": "fc_rgb_unmasked",
                        "styles": [style_fc_c3_rgb_unmasked],
                    },
                }
            ]
        }
    ],  ##### End of "layers" list.
}  #### End of test configuration object
