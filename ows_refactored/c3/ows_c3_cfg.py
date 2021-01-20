from ows_refactored.ows_legend_cfg import legend_idx_0_1_5ticks

bands_c3_ls_common = {
    "nbart_blue": ["nbart_blue"],
    "nbart_green": ["nbart_green"],
    "nbart_red": ["nbart_red"],
    "nbart_nir": ["nbart_nir", "nbart_near_infrared"],
    "nbart_swir_1": ["nbart_swir_1", "nbart_shortwave_infrared_1"],
    "nbart_swir_2": ["nbart_swir_2", "nbart_shortwave_infrared_2"],
}


bands_c3_ls_7 = bands_c3_ls_common.copy()
bands_c3_ls_7.update({
    "nbart_panchromatic": [],
})


bands_c3_ls_8 = bands_c3_ls_7.copy()
bands_c3_ls_8.update({
    "nbart_coastal_aerosol": ["coastal_aerosol",  "nbart_coastal_aerosol"],
})



style_c3_pure_aerosol = {
    "name": "aerosol",
    "title": "Narrow Blue - 440",
    "abstract": "Coastal Aerosol or Narrow Blue band, approximately 435nm to 450nm",
    "components": {
        "red": {"nbart_coastal_aerosol": 1.0},
        "green": {"nbart_coastal_aerosol": 1.0},
        "blue": {"nbart_coastal_aerosol": 1.0},
    },
    "scale_range": [0.0, 3000.0],
}

style_c3_pure_panchromatic = {
    "name": "panchromatic",
    "title": "Narrow Blue - 440",
    "abstract": "panchromatic",
    "components": {
        "red": {"nbart_panchromatic": 1.0},
        "green": {"nbart_panchromatic": 1.0},
        "blue": {"nbart_panchromatic": 1.0},
    },
    "scale_range": [0.0, 3000.0],
}

style_c3_simple_rgb = {
    "name": "simple_rgb",
    "title": "Simple RGB",
    "abstract": "Simple true-colour image, using the red, green and blue bands",
    "components": {"red": {"nbart_red": 1.0}, "green": {"nbart_green": 1.0}, "blue": {"nbart_blue": 1.0}},
    "scale_range": [0.0, 3000.0],
}

style_c3_false_colour = {
    "name": "false_colour",
    "title": "False Colour",
    "abstract": "Simple false-colour image using ASTER Bands 3 as red, 2 as green and 1 as blue",
    "components": {
        "red": {"nbart_green": 1.0},
        "green": {"nbart_swir_1": 1.0},
        "blue": {"nbart_nir": 1.0},
    },
    "scale_range": [0.0, 255.0],
}

style_c3_ndvi = {
    "name": "ndvi",
    "title": "NDVI - Red, NIR",
    "abstract": "Normalised Difference Vegetation Index - a derived index that correlates well with the existence of vegetation",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "mapped_bands": True,
        "kwargs": {"band1": "nbart_nir", "band2": "nbart_red"},
    },
    "needed_bands": ["nbart_red", "nbart_nir"],
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
    "legend": legend_idx_0_1_5ticks,
}

style_c3_ndwi = {
    "name": "ndwi",
    "title": "NDWI - Green, NIR",
    "abstract": "Normalised Difference Water Index - a derived index that correlates well with the existence of water (McFeeters 1996)",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "mapped_bands": True,
        "kwargs": {"band1": "nbart_green", "band2": "nbart_nir"},
    },
    "needed_bands": ["nbart_green", "nbart_nir"],
    "color_ramp": [
        {"value": -0.1, "color": "#f7fbff", "alpha": 0.0},
        {
            "value": 0.0,
            "color": "#d8e7f5",
        },
        {"value": 0.1, "color": "#b0d2e8"},
        {
            "value": 0.2,
            "color": "#73b3d8",
        },
        {"value": 0.3, "color": "#3e8ec4"},
        {
            "value": 0.4,
            "color": "#1563aa",
        },
        {
            "value": 0.5,
            "color": "#08306b",
        },
    ],
    "legend": {
        "begin": "0.0",
        "end": "0.5",
        "decimal_places": 1,
        "ticks": ["0.0", "0.2", "0.4", "0.5"],
        "tick_labels": {
            "0.0": {"prefix": "<"},
            "0.2": {"label": "0.2"},
            "0.4": {"label": "0.4"},
            "0.5": {"prefix": ">"},
        },
    },
}

style_c3_mndwi = {
    "name": "mndwi",
    "title": "MNDWI - Green, SWIR",
    "abstract": "Modified Normalised Difference Water Index - a derived index that correlates well with the existence of water (Xu 2006)",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "mapped_bands": True,
        "kwargs": {"band1": "nbart_green", "band2": "nbart_swir_1"},
    },
    "needed_bands": ["nbart_green", "nbart_swir_1"],
    "color_ramp": [
        {"value": -0.1, "color": "#f7fbff", "alpha": 0.0},
        {"value": 0.0, "color": "#d8e7f5"},
        {"value": 0.2, "color": "#b0d2e8"},
        {"value": 0.4, "color": "#73b3d8"},
        {"value": 0.6, "color": "#3e8ec4"},
        {"value": 0.8, "color": "#1563aa"},
        {"value": 1.0, "color": "#08306b"},
    ],
    "legend": legend_idx_0_1_5ticks,
}

style_c3_pure_blue = {
    "name": "blue",
    "title": "Blue - 480",
    "abstract": "Blue band, centered on 480nm",
    "components": {"red": {"nbart_blue": 1.0}, "green": {"nbart_blue": 1.0}, "blue": {"nbart_blue": 1.0}},
    "scale_range": [0.0, 3000.0],
}

style_c3_pure_green = {
    "name": "green",
    "title": "Green - 560",
    "abstract": "Green band, centered on 560nm",
    "components": {
        "red": {"nbart_green": 1.0},
        "green": {"nbart_green": 1.0},
        "blue": {"nbart_green": 1.0},
    },
    "scale_range": [0.0, 3000.0],
}

style_c3_pure_red = {
    "name": "red",
    "title": "Red - 660",
    "abstract": "Red band, centered on 660nm",
    "components": {"red": {"nbart_red": 1.0}, "green": {"nbart_red": 1.0}, "blue": {"nbart_red": 1.0}},
    "scale_range": [0.0, 3000.0],
}


style_c3_pure_nir = {
    "name": "nir",
    "title": "Near Infrared (NIR) - 840",
    "abstract": "Near infra-red band, centered on 840nm",
    "components": {"red": {"nbart_nir": 1.0}, "green": {"nbart_nir": 1.0}, "blue": {"nbart_nir": 1.0}},
    "scale_range": [0.0, 3000.0],
}


style_c3_pure_swir1 = {
    "name": "swir1",
    "title": "Shortwave Infrared (SWIR) - 1650",
    "abstract": "Short wave infra-red band 1, centered on 1650nm",
    "components": {
        "red": {"nbart_swir_1": 1.0},
        "green": {"nbart_swir_1": 1.0},
        "blue": {"nbart_swir_1": 1.0},
    },
    "scale_range": [0.0, 3000.0],
}

style_c3_pure_swir2 = {
    "name": "swir2",
    "title": "Shortwave Infrared (SWIR) - 2220",
    "abstract": "Short wave infra-red band 2, centered on 2220nm",
    "components": {
        "red": {"nbart_swir_2": 1.0},
        "green": {"nbart_swir_2": 1.0},
        "blue": {"nbart_swir_2": 1.0},
    },
    "scale_range": [0.0, 3000.0],
}

style_c3_ls_common = [
    style_c3_simple_rgb,
    style_c3_false_colour,
    style_c3_ndvi,
    style_c3_ndwi,
    style_c3_mndwi,
    style_c3_pure_blue,
    style_c3_pure_green,
    style_c3_pure_red,
    style_c3_pure_nir,
    style_c3_pure_swir1,
    style_c3_pure_swir2,
]

style_c3_ls_7 = style_c3_ls_common.append(style_c3_pure_panchromatic)
# style_c3_ls_8 = style_c3_ls_7.append(style_c3_pure_aerosol)
style_c3_ls_8 = [].append(style_c3_pure_aerosol)


reslim_c3_ls = {
    "wms": {
        "zoomed_out_fill_colour": [150, 180, 200, 160],
        "min_zoom_factor": 15.0,
        # "max_datasets": 16, # Defaults to no dataset limit
    },
    "wcs": {
        # "max_datasets": 16, # Defaults to no dataset limit
    },
}


dea_c3_ls8_ard = {
                            "title": "DEA C3 Landsat 8 ARD",
                            "abstract": """
This product takes Landsat 8 imagery captured over the Australian continent and corrects for inconsistencies across land and coastal fringes. The result is accurate and standardised surface reflectance data, which is instrumental in identifying and quantifying environmental change.

The imagery is captured using the Operational Land Imager (OLI) and Thermal Infra-Red Scanner (TIRS) sensors aboard Landsat 8.

This product is a single, cohesive Analysis Ready Data (ARD) package, which allows you to analyse surface reflectance data as is, without the need to apply additional corrections.

It contains three sub-products that provide corrections or attribution information:

Surface Reflectance NBAR 3 (Landsat 8 OLI-TIRS)
Surface Reflectance NBART 3 (Landsat 8 OLI-TIRS)
Surface Reflectance OA 3 (Landsat 8 OLI-TIRS)
The resolution is a 30 m grid based on the USGS Landsat Collection 1 archive.""",
                            # The WMS name for the layer
                            "name": "ga_ls8c_ard_3",
                            # The Datacube name for the associated data product
                            "product_name": "ga_ls8c_ard_3",
                            "bands": bands_c3_ls_8,
                            "resource_limits": reslim_c3_ls,
                            "image_processing": {
                                "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                                "always_fetch_bands": [],
                                "manual_merge": False,
                            },
                            "wcs": {
                                "native_crs": "EPSG:3577",
                                "native_resolution": [25, -25],
                                "default_bands": ["nbart_red", "nbart_green", "nbart_blue"],
                            },
                            "styling": {
                                "default_style": "simple_rgb",
                                "styles": style_c3_ls_8
                            },
                        },
dea_c3_ls7_ard =        {
                            "title": "DEA C3 Landsat 7 ARD",
                            "abstract": """
The United States Geological Survey's (USGS) Landsat satellite program has been capturing images of the Australian continent for more than 30 years. This data is highly useful for land and coastal mapping studies.
In particular, the light reflected from the Earth’s surface (surface reflectance) is important for monitoring environmental resources – such as agricultural production and mining activities – over time.

We need to make accurate comparisons of imagery acquired at different times, seasons and geographic locations. However, inconsistencies can arise due to variations in atmospheric conditions, sun position, sensor view angle, surface slope and surface aspect. These need to be reduced or removed to ensure the data is consistent and can be compared over time.

For service status information, see https://status.dea.ga.gov.au""",
                            # The WMS name for the layer
                            "name": "ga_ls7e_ard_3",
                            # The Datacube name for the associated data product
                            "product_name": "ga_ls7e_ard_3",
                            "bands": bands_c3_ls_7,
                            "resource_limits": reslim_c3_ls,
                            "image_processing": {
                                "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                                "always_fetch_bands": [],
                                "manual_merge": False,
                            },
                            "wcs": {
                                "native_crs": "EPSG:3577",
                                "native_resolution": [25, -25],
                                "default_bands": ["nbart_red", "nbart_green", "nbart_blue"],
                            },
                            "styling": {
                                "default_style": "simple_rgb",
                                "styles": style_c3_ls_7
                            },
                        },
dea_c3_ls5_ard =        {
                            "title": "DEA C3 Landsat 5 ARD",
                            "abstract": """
The United States Geological Survey's (USGS) Landsat satellite program has been capturing images of the Australian continent for more than 30 years. This data is highly useful for land and coastal mapping studies.

In particular, the light reflected from the Earth’s surface (surface reflectance) is important for monitoring environmental resources – such as agricultural production and mining activities – over time.

We need to make accurate comparisons of imagery acquired at different times, seasons and geographic locations. However, inconsistencies can arise due to variations in atmospheric conditions, sun position, sensor view angle, surface slope and surface aspect. These need to be reduced or removed to ensure the data is consistent and can be compared over time.


For service status information, see https://status.dea.ga.gov.au""",
                            # The WMS name for the layer
                            "name": "ga_ls5t_ard_3",
                            # The Datacube name for the associated data product
                            "product_name": "ga_ls5t_ard_3",
                            "bands": bands_c3_ls_common,
                            "resource_limits": reslim_c3_ls,
                            "image_processing": {
                                "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                                "always_fetch_bands": [],
                                "manual_merge": False,
                            },
                            "wcs": {
                                "native_crs": "EPSG:3577",
                                "native_resolution": [25, -25],
                                "default_bands": ["nbart_red", "nbart_green", "nbart_blue"],
                            },
                            "styling": {
                                "default_style": "simple_rgb",
                                "styles": style_c3_ls_common
                            },
                        },
