# reslim
reslim_landsat = {
    "wms": {
        "zoomed_out_fill_colour": [150,180,200,160],
        "min_zoom_factor": 35.0,
        # "max_datasets": 16, # Defaults to no dataset limit
    },
    "wcs": {
        # "max_datasets": 16, # Defaults to no dataset limit
    }
}



reslim_srtm = {
    "wms": {
        "zoomed_out_fill_colour": [150,180,200,160],
        "min_zoom_factor": 10.0,
        # "max_datasets": 16, # Defaults to no dataset limit
    },
    "wcs": {
        # "max_datasets": 16, # Defaults to no dataset limit
    }
}

reslim_wofs = {
    "wms": {
        "zoomed_out_fill_colour": [150,180,200,160],
        "min_zoom_factor": 0.0,
        # "max_datasets": 16, # Defaults to no dataset limit
    },
    "wcs": {
        # "max_datasets": 16, # Defaults to no dataset limit
    }
}
reslim_wofs_daily = {
    "wms": {
        "zoomed_out_fill_colour": [200, 180, 180, 160],
        "min_zoom_factor": 35.0,
        "max_datasets_wms": 6,
    },
    "wcs": {
        "max_datasets": 16, # Defaults to no dataset limit
    }
}

reslim_wofs_dry = {
    "wms": {
        "zoomed_out_fill_colour": [150,180,200,160],
        "min_zoom_factor": 15.0,
        # "max_datasets": 16, # Defaults to no dataset limit
    },
    "wcs": {
        # "max_datasets": 16, # Defaults to no dataset limit
    }
}
reslim_alos_palsar = reslim_srtm


# bands

bands_ls = {
    "red": [],
    "green": [],
    "blue": [ ],
    "nir": [ "near_infrared" ],
    "swir1": [ "shortwave_infrared_1", "near_shortwave_infrared" ],
    "swir2": [ "shortwave_infrared_2", "far_shortwave_infrared" ],
}

bands_sentinel = {
    "B01": ["band_01", "coastal_aerosol"],
    "B02": ["band_02", "blue"],
    "B03": ["band_03", "green"],
    "B04": ["band_04", "red"],
    "B05": ["band_05", "red_edge_1"],
    "B06": ["band_06", "red_edge_2"],
    "B07": ["band_07", "red_edge_3"],
    "B08": ["band_08", "nir", "nir_1"],
    "B8A": ["band_8a", "nir_narrow", "nir_2"],
    "B09": ["band_09", "water_vapour"],
    "B11": ["band_11", "swir_1", "swir_16"],
    "B12": ["band_12", "swir_2", "swir_22"],
    "AOT": ["aerosol_optical_thickness"],
    "WVP": ["scene_average_water_vapour"],
    "SCL": ["mask", "qa"]
}

bands_ls8c = {
    "red": [],
    "green": [],
    "blue": [],
    "nir": [],
    "swir_1": [],
    "swir_2": [],
}


bands_wofs_obs = {
    "water": [],
}

bands_wofs_wet = {
    "count_wet": [],
}

bands_wofs_frequency =  {
    "frequency": [],
}

bands_usgs_wofs_summary = {
    "count_wet": [],
    "count_dry": [],
    "frequency": []
}

bands_wofs_2_annual_summary = {
    "frequency": [],
    "count_clear": [],
    "count_wet": []
}

bands_wofs_dry = {
    "count_dry": []
}

bands_wofs_count_clear = {
    "count_clear": []
}

bands_fc = {
    "BS": [ "bare_soil" ],
    "PV": [ "photosynthetic_vegetation", "green_vegetation" ],
    "NPV": [ "non_photosynthetic_vegetation", "brown_vegetation" ],
    "UE": [ "unmixing_error" ]
}


bands_elevation = {
    "elevation": [],
}

bands_alos = {
    "hh": [],
    "hv": [],
    "mask": [],
    "date": [],
    "linci": []
}
# Style
style_ls_simple_rgb = {
        "name": "simple_rgb",
        "title": "Simple RGB",
        "abstract": "Simple true-colour image, using the red, green and blue bands",
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
}

style_gals_simple_rgb = {
        "name": "simple_rgb",
        "title": "Simple RGB",
        "abstract": "Simple true-colour image, using the red, green and blue bands",
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
        # The raw band value range to be compressed to an 8 bit range for the output image tiles.
        # Band values outside this range are clipped to 0 or 255 as appropriate.
        "scale_range": [7272.0, 18181.0]
}

style_fc_simple_rgb  = {
        "name": "simple_rgb",
        "title": "Simple RGB",
        "abstract": "Simple true-colour image, using the red, green and blue bands",
        "components": {
            "red": {
                "BS_PC_50": 1.0
            },
            "green": {
                "PV_PC_50": 1.0
            },
            "blue": {
                "NPV_PC_50": 1.0
            }
        },
        "scale_range": [0.0, 100.0],
        "pq_masks": [
            {
                "flags": {
                    'sea': True,
                },
                "invert": True,
            },
        ],
}
style_gals_irg = {
    "name": "infrared_green",
    "title": "False colour - Green, SWIR, NIR",
    "abstract": "False Colour image with SWIR1->Red, NIR->Green, and Green->Blue",
    "components": {
        "red": {
            "swir_1": 1.0
        },
        "green": {
            "nir": 1.0
        },
        "blue": {
            "green": 1.0
        }
    },
    "scale_range": [7272.0, 18181.0]
}

style_s2_irg = {
    "name": "infrared_green",
    "title": "False colour - Green, SWIR, NIR",
    "abstract": "False Colour image with SWIR1->Red, NIR->Green, and Green->Blue",
    "components": {
        "red": {
            "swir_1": 1.0
        },
        "green": {
            "nir": 1.0
        },
        "blue": {
            "green": 1.0
        }
    },
    "scale_range": [0, 3000]
}

style_ls_irg = {
    "name": "infrared_green",
    "title": "False colour - Green, SWIR, NIR",
    "abstract": "False Colour image with SWIR1->Red, NIR->Green, and Green->Blue",
    "components": {
        "red": {
            "swir1": 1.0
        },
        "green": {
            "nir": 1.0
        },
        "blue": {
            "green": 1.0
        }
    },
    "scale_range": [0.0, 3000.0]
}

style_ls_ndvi = {
    "name": "ndvi",
    "title": "NDVI - Red, NIR",
    "abstract": "Normalised Difference Vegetation Index - a derived index that correlates well with the existence of vegetation",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "pass_product_cfg": True,
        "kwargs": {
            "band1": "nir",
            "band2": "red"
        }
    },
    "needed_bands": ["red", "nir"],
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
    ]
}

style_ls_ndwi = {
    "name": "ndwi",
    "title": "NDWI - Green, NIR",
    "abstract": "Normalised Difference Water Index - a derived index that correlates well with the existence of water (McFeeters 1996)",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "pass_product_cfg": True,
        "kwargs": {
            "band1": "green",
            "band2": "nir"
        }
    },
    "needed_bands": ["green", "nir"],
    "color_ramp": [
        {
            "value": -0.1,
            "color": "#f7fbff",
            "alpha": 0.0
        },
        {
            "value": 0.0,
            "color": "#d8e7f5",
            "legend": {
                "prefix": "<"
            }
        },
        {
            "value": 0.1,
            "color": "#b0d2e8"
        },
        {
            "value": 0.2,
            "color": "#73b3d8",
            "legend": {}
        },
        {
            "value": 0.3,
            "color": "#3e8ec4"
        },
        {
            "value": 0.4,
            "color": "#1563aa",
            "legend": {}
        },
        {
            "value": 0.5,
            "color": "#08306b",
            "legend": {
                "prefix": ">"
            }
        }
    ]
}

style_gals_mndwi = {
    "name": "mndwi",
    "title": "MNDWI - Green, SWIR",
    "abstract": "Modified Normalised Difference Water Index - a derived index that correlates well with the existence of water (Xu 2006)",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "pass_product_cfg": True,
        "kwargs": {
            "band1": "green",
            "band2": "swir_1"
        }
    },
    "needed_bands": ["green", "swir_1"],
    "color_ramp": [
        {
            "value": -0.1,
            "color": "#f7fbff",
            "alpha": 0.0
        },
        {
            "value": 0.0,
            "color": "#d8e7f5"
        },
        {
            "value": 0.2,
            "color": "#b0d2e8"
        },
        {
            "value": 0.4,
            "color": "#73b3d8"
        },
        {
            "value": 0.6,
            "color": "#3e8ec4"
        },
        {
            "value": 0.8,
            "color": "#1563aa"
        },
        {
            "value": 1.0,
            "color": "#08306b"
        }
    ]
}

style_ls_mndwi = {
    "name": "mndwi",
    "title": "MNDWI - Green, SWIR",
    "abstract": "Modified Normalised Difference Water Index - a derived index that correlates "
                "well with the existence of water (Xu 2006)",
    "index_function": {
        "function": "datacube_ows.band_utils.norm_diff",
        "pass_product_cfg": True,
        "kwargs": {
            "band1": "green",
            "band2": "swir1"
        }
    },
    "needed_bands": ["green", "swir1"],
    "color_ramp": [
        {
            "value": -0.1,
            "color": "#f7fbff",
            "alpha": 0.0
        },
        {
            "value": 0.0,
            "color": "#d8e7f5"
        },
        {
            "value": 0.2,
            "color": "#b0d2e8"
        },
        {
            "value": 0.4,
            "color": "#73b3d8"
        },
        {
            "value": 0.6,
            "color": "#3e8ec4"
        },
        {
            "value": 0.8,
            "color": "#1563aa"
        },
        {
            "value": 1.0,
            "color": "#08306b"
        }
    ]
}

style_gals_pure_blue = {
    "name": "blue",
    "title": "Blue - 480",
    "abstract": "Blue band, centered on 480nm",
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
    "scale_range": [7272.0, 18181.0]
}

style_ls_pure_blue = {
    "name": "blue",
    "title": "Blue - 480",
    "abstract": "Blue band, centered on 480nm",
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

style_sentinel_pure_blue = {
    "name": "blue",
    "title": "Blue - 490",
    "abstract": "Blue band, centered on 490nm",
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

style_gals_pure_green = {
    "name": "green",
    "title": "Green - 560",
    "abstract": "Green band, centered on 560nm",
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
    "scale_range": [7272.0, 18181.0]
}

style_ls_pure_green = {
    "name": "green",
    "title": "Green - 560",
    "abstract": "Green band, centered on 560nm",
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

style_gals_pure_red = {
    "name": "red",
    "title": "Red - 660",
    "abstract": "Red band, centered on 660nm",
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
    "scale_range": [7272.0, 18181.0]
}

style_ls_pure_red = {
    "name": "red",
    "title": "Red - 660",
    "abstract": "Red band, centered on 660nm",
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

style_gals_pure_nir = {
    "name": "nir",
    "title": "Near Infrared (NIR) - 840",
    "abstract": "Near infra-red band, centered on 840nm",
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
    "scale_range": [7272.0, 18181.0]
}

style_ls_pure_nir  = {
    "name": "nir",
    "title": "Near Infrared (NIR) - 840",
    "abstract": "Near infra-red band, centered on 840nm",
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

style_sentinel_pure_nir = {
    "name": "nir",
    "title": "Near Infrared (NIR) - 870",
    "abstract": "Near infra-red band, centered on 870nm",
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

style_gals_pure_swir1 = {
    "name": "swir_1",
    "title": "Shortwave Infrared (SWIR) - 1610",
    "abstract": "Short wave infra-red band 1, centered on 1610nm",
    "components": {
        "red": {
            "swir_1": 1.0
        },
        "green": {
            "swir_1": 1.0
        },
        "blue": {
            "swir_1": 1.0
        }
    },
    "scale_range": [7272.0, 18181.0]
}


style_s2_pure_swir1 = {
    "name": "swir_1",
    "title": "Shortwave Infrared (SWIR) - 1610",
    "abstract": "Short wave infra-red band 1, centered on 1610nm",
    "components": {
        "red": {
            "B11": 1.0
        },
        "green": {
            "B11": 1.0
        },
        "blue": {
            "B11": 1.0
        }
    },
    "scale_range": [0.0, 3000.0]
}

style_ls_pure_swir1 = {
    "name": "swir1",
    "title": "Shortwave Infrared (SWIR) - 1650",
    "abstract": "Short wave infra-red band 1, centered on 1650nm",
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

style_sentinel_pure_swir1 =  {
    "name": "swir1",
    "title": "Shortwave Infrared (SWIR) - 1610",
    "abstract": "Short wave infra-red band 1, centered on 1610nm",
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

style_gals_pure_swir2 = {
    "name": "swir_2",
    "title": "Shortwave Infrared (SWIR) - 2200",
    "abstract": "Short wave infra-red band 2, centered on 2200nm",
    "components": {
        "red": {
            "swir_2": 1.0
        },
        "green": {
            "swir_2": 1.0
        },
        "blue": {
            "swir_2": 1.0
        }
    },
    "scale_range": [7272.0, 18181.0]
}

style_s2_pure_swir2 = {
    "name": "swir_2",
    "title": "Shortwave Infrared (SWIR) - 2200",
    "abstract": "Short wave infra-red band 2, centered on 2200nm",
    "components": {
        "red": {
            "swir_2": 1.0
        },
        "green": {
            "swir_2": 1.0
        },
        "blue": {
            "swir_2": 1.0
        }
    },
    "scale_range": [0, 3000.0]
}

style_ls_pure_swir2 = {
    "name": "swir2",
    "title": "Shortwave Infrared (SWIR) - 2220",
    "abstract": "Short wave infra-red band 2, centered on 2220nm",
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

style_s2_ndci = {
    "name": "ndci",
    "title": "NDCI - Red Edge, Red",
    "abstract": "Normalised Difference Chlorophyll Index - a derived index that correlates well with the existence of chlorophyll",
    "index_function": {
        "function": "datacube_ows.band_utils.sentinel2_ndci",
        "pass_product_cfg": True,
        "kwargs": {
            "b_red_edge": "red_edge_1",
            "b_red": "red",
            "b_green": "green",
            "b_swir": "swir_2",
        }
    },
    "needed_bands": ["red_edge_1", "red", "green", "swir_2"],
    "color_ramp": [
        {
            "value": -0.1,
            "color": "#1696FF",
            "legend": {
                "prefix" : "<"
            }
        },
        {
            "value": -0.1,
            "color": "#1696FF"
        },
        {
            "value": 0.0,
            "color": "#00FFDF",
            "legend": { }
        },
        {
            "value": 0.1,
            "color": "#FFF50E",
        },
        {
            "value": 0.2,
            "color": "#FFB50A",
            "legend": { }
        },
        {
            "value": 0.4,
            "color": "#FF530D",
        },
        {
            "value": 0.5,
            "color": "#FF0000",
            "legend": {
                "prefix": ">"
            }
        }
    ]
}

style_s2_pure_aerosol = {
    "name": "aerosol",
    "title": "Narrow Blue - 440",
    "abstract": "Coastal Aerosol or Narrow Blue band, approximately 435nm to 450nm",
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


style_s2_pure_redge_1 = {
    "name": "red_edge_1",
    "title": "Vegetation Red Edge - 710",
    "abstract": "Near infra-red band, centred on 710nm",

    "components": {
        "red": {
            "red_edge_1": 1.0
        },
        "green": {
            "red_edge_1": 1.0
        },
        "blue": {
            "red_edge_1": 1.0
        }
    },
    "scale_range": [0.0, 3000.0]
}


style_s2_pure_redge_2 = {
    "name": "red_edge_2",
    "title": "Vegetation Red Edge - 740",
    "abstract": "Near infra-red band, centred on 740nm",

    "components": {
        "red": {
            "red_edge_2": 1.0
        },
        "green": {
            "red_edge_2": 1.0
        },
        "blue": {
            "red_edge_2": 1.0
        }
    },
    "scale_range": [0.0, 3000.0]
}


style_s2_pure_redge_3 = {
    "name": "red_edge_3",
    "title": "Vegetation Red Edge - 780",
    "abstract": "Near infra-red band, centred on 780nm",

    "components": {
        "red": {
            "red_edge_3": 1.0
        },
        "green": {
            "red_edge_3": 1.0
        },
        "blue": {
            "red_edge_3": 1.0
        }
    },
    "scale_range": [0.0, 3000.0]
}

style_s2_pure_narrow_nir = {
    "name": "narrow_nir",
    "title": "Narrow Near Infrared - 870",
    "abstract": "Near infra-red band, centred on 865nm",
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

style_sentinel_pure_swir2 = {
    "name": "swir2",
    "title": "Shortwave Infrared (SWIR) - 2200",
    "abstract": "Short wave infra-red band 2, centered on 2200nm",
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

style_wofs_count_wet = {
    "name": "water_observations",
    "title": "Count Wet",
    "abstract": "WOfS summary showing the count of water observations",
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "count_wet",
        }
    },
    "needed_bands": ["count_wet"],
    "include_in_feature_info": False,
    "color_ramp": [
        {
            "value": 0,
            "color": "#666666",
            "alpha": 0
        },
        {
            # purely for legend display
            # we should not get fractional
            # values in this styles
            "value": 0.2,
            "color": "#890000",
            "alpha": 1
        },
        {
            "value": 20,
            "color": "#990000"
        },
        {
            "value": 30,
            "color": "#E38400"
        },
        {
            "value": 40,
            "color": "#E3DF00"
        },
        {
            "value": 50,
            "color": "#A6E300"
        },
        {
            "value": 60,
            "color": "#00E32D"
        },
        {
            "value": 70,
            "color": "#00E3C8"
        },
        {
            "value": 80,
            "color": "#0097E3"
        },
        {
            "value": 90,
            "color": "#005FE3"
        },
        {
            "value": 100,
            "color": "#000FE3"
        },
        {
            "value": 110,
            "color": "#000EA9"
        },
        {
            "value": 120,
            "color": "#5700E3",
            "legend": {
                "prefix": ">"
            }
        }
    ],
    "legend": {
        "radix_point": 0,
        "scale_by": 1,
        "major_ticks": 20
    }
}

style_wofs_water_annual_wet = {
    "name": "water_observations",
    "title": "Count Wet",
    "abstract": "WOfS summary showing the count of water observations",
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "count_wet",
        }
    },
    "needed_bands": ["count_wet"],
    "color_ramp": [
        {
            "value": 0,
            "color": "#666666",
            "alpha": 0
        },
        {
            # purely for legend display
            # we should not get fractional
            # values in this styles
            "value": 0.2,
            "color": "#990000",
            "alpha": 1
        },
        {
            "value": 2,
            "color": "#990000"
        },
        {
            "value": 4,
            "color": "#E38400"
        },
        {
            "value": 6,
            "color": "#E3DF00"
        },
        {
            "value": 8,
            "color": "#00E32D"
        },
        {
            "value": 10,
            "color": "#00E3C8"
        },
        {
            "value": 12,
            "color": "#0097E3"
        },
        {
            "value": 14,
            "color": "#005FE3"
        },
        {
            "value": 16,
            "color": "#000FE3"
        },
        {
            "value": 18,
            "color": "#000EA9"
        },
        {
            "value": 20,
            "color": "#5700E3",
            "legend": {
                "prefix": ">"
            }
        }
    ],
    "legend": {
        "radix_point": 0,
        "scale_by": 1,
        "major_ticks": 10
    }
}

style_wofs_frequency = {
    "name": "WOfS_frequency",
    "title": " Water Summary",
    "abstract": "WOfS summary showing the frequency of Wetness",
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "frequency",
        }
    },
    "needed_bands": ["frequency"],
    "include_in_feature_info": False,
    "color_ramp": [
        {
            "value": 0.0,
            "color": "#000000",
            "alpha": 0.0
        },
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
            "color": "#5700e3"
        }
    ],
    "legend": {
        "url": "https://data.dea.ga.gov.au/WOfS/filtered_summary/v2.1.0/wofs_full_summary_legend.png",
    }
}

style_wofs_annual_summary_frequency = {
    "name": "WOfS_frequency",
    "title": " Water Summary",
    "abstract": "WOfS summary showing the frequency of Wetness",
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "frequency",
        }
    },
    "needed_bands": ["frequency"],
    "include_in_feature_info": False,
    "color_ramp": [
        {
            "value": 0.0,
            "color": "#000000",
            "alpha": 0.0
        },
        {
            "value": 0.02,
            "color": "#000000",
            "alpha": 0.0
        },
        {
            "value": 0.05,
            "color": "#8e0101",
            "alpha": 0.25
        },
        {
            "value": 0.1,
            "color": "#cf2200",
            "alpha": 0.75
        },
        {
            "value": 0.2,
            "color": "#e38400"
        },
        {
            "value": 0.3,
            "color": "#e3df00"
        },
        {
            "value": 0.4,
            "color": "#a6e300"
        },
        {
            "value": 0.5,
            "color": "#00e32d"
        },
        {
            "value": 0.6,
            "color": "#00e3c8"
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
            "color": "#5700e3"
        }
    ],
    "legend": {
        "units": "%",
        "radix_point": 0,
        "scale_by": 100.0,
        "major_ticks": 0.1
    }
}

style_wofs_annual_frequency = {
    "name": "WOfS_frequency",
    "title": " Water Summary",
    "abstract": "WOfS summary showing the frequency of Wetness",
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "frequency",
        }
    },
    "needed_bands": ["frequency"],
    "color_ramp": [
        {
            "value": 0.0,
            "color": "#000000",
            "alpha": 0.0
        },
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
            "color": "#5700e3"
        }
    ],
    "legend": {
        "units": "%",
        "radix_point": 0,
        "scale_by": 100.0,
        "major_ticks": 0.1
    }
}

style_wofs_frequency_blue = {
    "name": "WOfS_frequency_blues_transparent",
    "title": "Water Summary (Blue)",
    "abstract": "WOfS summary showing the frequency of Wetness",
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "frequency",
        }
    },
    "include_in_feature_info": False,
    "needed_bands": ["frequency"],
    "color_ramp": [
        {
            "value": 0.0,
            "color": "#ffffff",
            "alpha": 0.0,
        },
        {
            "value": 0.001,
            "color": "#d5fef9",
            "alpha": 0.0,
        },
        {
            "value": 0.02,
            "color": "#d5fef9",
        },
        {
            "value": 0.2,
            "color": "#71e3ff"
        },
        {
            "value": 0.4,
            "color": "#01ccff"
        },
        {
            "value": 0.6,
            "color": "#0178ff"
        },
        {
            "value": 0.8,
            "color": "#2701ff"
        },
        {
            "value": 1.0,
            "color": "#5700e3"
        }
    ],
    "legend": {
        "units": "%",
        "radix_point": 0,
        "scale_by": 100.0,
        "major_ticks": 0.1
    }

}

style_wofs_annual_summary_frequency_blue = {
    "name": "WOfS_frequency_blues_transparent",
    "title": "Water Summary (Blue)",
    "abstract": "WOfS summary showing the frequency of Wetness",
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "frequency",
        }
    },
    "include_in_feature_info": False,
    "needed_bands": ["frequency"],
    "color_ramp": [
        {
            "value": 0.0,
            "color": "#ffffff",
            "alpha": 0.0,
        },
        {
            "value": 0.001,
            "color": "#d5fef9",
            "alpha": 0.0,
        },
        {
            "value": 0.02,
            "color": "#d5fef9",
        },
        {
            "value": 0.2,
            "color": "#71e3ff"
        },
        {
            "value": 0.4,
            "color": "#01ccff"
        },
        {
            "value": 0.6,
            "color": "#0178ff"
        },
        {
            "value": 0.8,
            "color": "#2701ff"
        },
        {
            "value": 1.0,
            "color": "#5700e3"
        }
    ],
    "legend": {
        "units": "%",
        "radix_point": 0,
        "scale_by": 100.0,
        "major_ticks": 0.1
    }

}

style_wofs_annual_frequency_blue = {
    "name": "WOfS_frequency_blues_transparent",
    "title": "Water Summary (Blue)",
    "abstract": "WOfS summary showing the frequency of Wetness",
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "frequency",
        }
    },
    "needed_bands": ["frequency"],
    "color_ramp": [
        {
            "value": 0.0,
            "color": "#ffffff",
            "alpha": 0.0,
        },
        {
            "value": 0.001,
            "color": "#d5fef9",
            "alpha": 0.0,
        },
        {
            "value": 0.02,
            "color": "#d5fef9",
        },
        {
            "value": 0.2,
            "color": "#71e3ff"
        },
        {
            "value": 0.4,
            "color": "#01ccff"
        },
        {
            "value": 0.6,
            "color": "#0178ff"
        },
        {
            "value": 0.8,
            "color": "#2701ff"
        },
        {
            "value": 1.0,
            "color": "#5700e3"
        }
    ],
    "legend": {
        "units": "%",
        "radix_point": 0,
        "scale_by": 100.0,
        "major_ticks": 0.1
    }

}

style_wofs_summary_clear = {
    "name": "annual_clear_observations",
    "title": "Clear Count",
    "abstract": "WOfS annual summary showing the count of clear observations",
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "count_clear",
        }
    },
    "include_in_feature_info": False,
    "needed_bands": ["count_clear"],
    "color_ramp": [
        {
            "value": 0,
            "color": "#FFFFFF",
            "alpha": 0
        },
        {
            # purely for legend display
            # we should not get fractional
            # values in this styles
            "value": 0,
            "color": "#B21800",
            "alpha": 1
        },
        {
            "value": 20,
            "color": "#B21800"
        },
        {
            "value": 30,
            "color": "#ef8500"
        },
        {
            "value": 40,
            "color": "#ffb800"
        },
        {
            "value": 60,
            "color": "#ffd000"
        },
        {
            "value": 80,
            "color": "#fff300"
        },
        {
            "value": 100,
            "color": "#fff300"
        },
        {
            "value": 120,
            "color": "#c1ec00"
        },
        {
            "value": 140,
            "color": "#6ee100"
        },
        {
            "value": 160,
            "color": "#39a500"
        },
        {
            "value": 180,
            "color": "#026900",
            "legend": {
                "prefix": ">"
            }
        }
    ],
    "legend": {
        "radix_point": 0,
        "scale_by": 1,
        "major_ticks": 20,
        "axes_position": [0.05, 0.5, 0.89, 0.15]
    }
}

style_wofs_beta_summary_clear = {
    "name": "annual_clear_observations",
    "title": "Clear Count",
    "abstract": "WOfS annual summary showing the count of clear observations",
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "count_clear",
        }
    },
    "include_in_feature_info": False,
    "needed_bands": ["count_clear"],
    "color_ramp": [
        {
            "value": 0,
            "color": "#FFFFFF",
            "alpha": 0
        },
        {
            # purely for legend display
            # we should not get fractional
            # values in this styles
            "value": 0,
            "color": "#B21800",
            "alpha": 1
        },
        {
            "value": 3,
            "color": "#B21800"
        },
        {
            "value": 6,
            "color": "#ef8500"
        },
        {
            "value": 10,
            "color": "#ffb800"
        },
        {
            "value": 12,
            "color": "#ffd000"
        },
        {
            "value": 15,
            "color": "#fff300"
        },
        {
            "value": 18,
            "color": "#fff300"
        },
        {
            "value": 20,
            "color": "#c1ec00"
        },
        {
            "value": 24,
            "color": "#6ee100"
        },
        {
            "value": 27,
            "color": "#39a500"
        },
        {
            "value": 30,
            "color": "#026900",
            "legend": {
                "prefix": ">"
            }
        }
    ],
    "legend": {
        "radix_point": 0,
        "scale_by": 1,
        "major_ticks": 10,
    }
}


style_wofs_annual_clear = {
    "name": "annual_clear_observations",
    "title": "Clear Count",
    "abstract": "WOfS annual summary showing the count of clear observations",
    "needed_bands": ["count_dry"],
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "count_dry",
        }
    },
    "color_ramp": [
        {
            "value": 0,
            "color": "#FFFFFF",
            "alpha": 0
        },
        {
            # purely for legend display
            # we should not get fractional
            # values in this styles
            "value": 0.2,
            "color": "#B21800",
            "alpha": 1
        },
        {
            "value": 1,
            "color": "#B21800"
        },
        {
            "value": 6,
            "color": "#ef8500"
        },
        {
            "value": 10,
            "color": "#ffb800"
        },
        {
            "value": 14,
            "color": "#ffd000"
        },
        {
            "value": 18,
            "color": "#fff300"
        },
        {
            "value": 22,
            "color": "#fff300"
        },
        {
            "value": 28,
            "color": "#c1ec00"
        },
        {
            "value": 32,
            "color": "#6ee100"
        },
        {
            "value": 36,
            "color": "#39a500"
        },
        {
            "value": 40,
            "color": "#026900",
            "legend": {
                "prefix": ">"
            }
        }
    ],
    "legend": {
        "radix_point": 0,
        "scale_by": 1,
        "major_ticks": 10,
        "axes_position": [0.05, 0.5, 0.89, 0.15]
    }
}

style_annual_wofs_summary_frequency = {
    "name": "annual_WOfS_frequency",
    "title": "Water Summary",
    "abstract": "WOfS annual summary showing the frequency of Wetness",
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "frequency",
        }
    },
    "include_in_feature_info": False,
    "needed_bands": ["frequency"],
    "color_ramp": [
        {
            "value": 0.0,
            "color": "#000000",
            "alpha": 0.0
        },
        {
            "value": 0.02,
            "color": "#000000",
            "alpha": 0.0
        },
        {
            "value": 0.05,
            "color": "#8e0101",
            "alpha": 0.25
        },
        {
            "value": 0.1,
            "color": "#cf2200",
            "alpha": 0.75
        },
        {
            "value": 0.2,
            "color": "#e38400"
        },
        {
            "value": 0.3,
            "color": "#e3df00"
        },
        {
            "value": 0.4,
            "color": "#62e300"
        },
        {
            "value": 0.5,
            "color": "#00e32d"
        },
        {
            "value": 0.6,
            "color": "#00e3c8"
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
            "color": "#5700e3"
        }
    ],
    "legend": {
        "units": "%",
        "radix_point": 0,
        "scale_by": 100.0,
        "major_ticks": 0.1
    }
}

style_seasonal_wofs_summary_frequency = {
    "name": "seasonal_WOfS_frequency",
    "title": " Water Summary",
    "abstract": "WOfS seasonal summary showing the frequency of Wetness",
    "needed_bands": ["frequency"],
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "frequency",
        }
    },
    "color_ramp": [
        {
            "value": 0.0,
            "color": "#000000",
            "alpha": 0.0
        },
        {
            "value": 0.02,
            "color": "#000000",
            "alpha": 0.0
        },
        {
            "value": 0.05,
            "color": "#8e0101",
            "alpha": 0.25
        },
        {
            "value": 0.1,
            "color": "#cf2200",
            "alpha": 0.75
        },
        {
            "value": 0.2,
            "color": "#e38400"
        },
        {
            "value": 0.3,
            "color": "#e3df00"
        },
        {
            "value": 0.4,
            "color": "#62e300"
        },
        {
            "value": 0.5,
            "color": "#00e32d"
        },
        {
            "value": 0.6,
            "color": "#00e3c8"
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
            "color": "#5700e3"
        }
    ],
    "legend": {
        "units": "%",
        "radix_point": 0,
        "scale_by": 100.0,
        "major_ticks": 0.1
    }
}



style_wofs_obs = {
    "name": "observations",
    "title": "Observations",
    "abstract": "Classified as water by the decision tree",
    "value_map": {
        "water": [
            {
                "title": "Invalid",
                "abstract": "Slope or Cloud",
                "flags": {
                    "or": {
                        "cloud_shadow": True,
                        "cloud": True
                    }
                },
                "color": "#707070"
            },
            {
                "title": "Dry",
                "abstract": "Dry",
                "flags": {
                    "dry": True,
                    "sea": False,
                    "cloud_shadow": False,
                    "cloud": False,
                    "nodata": False
                },
                "color": "#D99694"
            },
            {
                "title": "Wet",
                "abstract": "Wet or Sea",
                "flags": {
                    "or": {
                        "wet": True,
                        "sea": True
                    }
                },
                "color": "#4F81BD"
            }
        ]
    }
}

style_wofs_obs_wet_only = {
    "name": "wet",
    "title": "Wet Only",
    "abstract": "Clear and Wet",
    "value_map": {
        "water": [
            {
                "title": "Invalid",
                "abstract": "Slope or Cloud",
                "flags": {
                    "or": {
                        "cloud_shadow": True,
                        "cloud": True,
                        "nodata": True,
                    }
                },
                "color": "#707070",
                "mask": True
            },
            {
                "title": "Dry",
                "abstract": "Dry",
                "flags": {
                    "dry": True,
                    "sea": False,
                },
                "color": "#D99694",
                "mask": True
            },
            {
                "title": "Wet",
                "abstract": "Wet or Sea",
                "flags": {
                    "or": {
                        "wet": True,
                        "sea": True
                    }
                },
                "color": "#4F81BD"
            }
        ]
    }
}

style_wofs_dry_observations = {
    "name": "dry_observations",
    "title": "Count Dry",
    "abstract": "WOfS summary showing the count of dry observations",
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "count_dry",
        }
    },
    "needed_bands": ["count_dry"],
    "color_ramp": [
        {
            "value": 0,
            "color": "#FFFFFF",
            "alpha": 0
        },
        {
            # purely for legend display
            # we should not get fractional
            # values in this styles
            "value": 10,
            "color": "#b21800",
            "alpha": 1
        },
        {
            "value": 100,
            "color": "#ef8500"
        },
        {
            "value": 200,
            "color": "#ffb800"
        },
        {
            "value": 300,
            "color": "#ffd300"
        },
        {
            "value": 400,
            "color": "#ffe300"
        },
        {
            "value": 500,
            "color": "#fff300"
        },
        {
            "value": 600,
            "color": "#d0f800"
        },
        {
            "value": 700,
            "color": "#a0fd00"
        },
        {
            "value": 800,
            "color": "#6ee100"
        },
        {
            "value": 901,
            "color": "#39a500"
        },
        {
            "value": 1000,
            "color": "#026900",
            "legend": {
                "prefix": ">"
            }
        }
    ],
    "legend": {
        "radix_point": 0,
        "scale_by": 1,
        "major_ticks": 100,
        "axes_position": [0.05, 0.5, 0.89, 0.15]
    }
}

style_fc_simple = {
    "name": "simple_fc",
    "title": "Fractional Cover",
    "abstract": "Fractional cover representation, with green vegetation in green, dead vegetation in blue, and bare soil in red",
    "components": {
        "red": {
            "BS": 1.0
        },
        "green": {
            "PV": 1.0
        },
        "blue": {
            "NPV": 1.0
        }
    },
    "scale_range": [0.0, 100.0],
    "legend": {
        "url": "https://data.digitalearth.africa/usgs/pc2/ga_ls8c_fractional_cover_2/FC_legend.png",
    }
}



style_alos_hh = {
    "name": "hh",
    "title": "HH",
    "abstract": "HH band",
    "needed_bands": ["hh"],
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "hh",
        }
    },
    "color_ramp": [
        {
            "value": 0,
            "color": "#f7fcf5"
        },
        {
            "value": 750,
            "color": "#e2f4dd"
        },
        {
            "value": 1000,
            "color": "#c0e6b9"
        },
        {
            "value": 1500,
            "color": "#94d390"
        },
        {
            "value": 2500,
            "color": "#60ba6c"
        },
        {
            "value": 4000,
            "color": "#329b51"
        },
        {
            "value": 6000,
            "color": "#0c7835"
        },
        {
            "value": 8000,
            "color": "#00441b",
            "legend": {
                "prefix": ">"
            }
        }
    ],
    "legend": {
        "radix_point": 0,
        "scale_by": 1,
        "major_ticks": 500
    }
}

style_alos_hv = {
    "name": "hv",
    "title": "HV",
    "abstract": "HV band",
    "needed_bands": ["hv"],
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "hv",
        }
    },
    "color_ramp": [
        {
            "value": 0,
            "color": "#f7fcf5"
        },
        {
            "value": 250,
            "color": "#e2f4dd"
        },
        {
            "value": 300,
            "color": "#c0e6b9"
        },
        {
            "value": 500,
            "color": "#94d390"
        },
        {
            "value": 800,
            "color": "#60ba6c"
        },
        {
            "value": 2000,
            "color": "#329b51"
        },
        {
            "value": 3500,
            "color": "#0c7835"
        },
        {
            "value": 4500,
            "color": "#00441b",
            "legend": {
                "prefix": ">"
            }
        }
    ],
    "legend": {
        "radix_point": 0,
        "scale_by": 1,
        "major_ticks": 500
    }
}

style_alos_hh_over_hv = {
    "name": "hh_hv_hh_over_hv",
    "title": "HH, HV and HH/HV",
    "abstract": "False colour representation of HH, HV and HH over HV for R, G and B respectively",
    # Mixing ratio between linear components and colour ramped index. 1.0 is fully linear components, 0.0 is fully colour ramp.
    "component_ratio": 0.5,
    "index_function": {
        "function": "datacube_ows.band_utils.band_quotient",
        "pass_product_cfg": True,
        "kwargs": {
            "band1": "hh",
            "band2": "hv"
        }
    },
    "needed_bands": ["hh", "hv"],
    "range": [0.01, 2.0],
    "components": {
        "red": {
            "hh": 1.0
        },
        "green": {
            "hv": 1.0
        },
        "blue": {
            "hh": 0.0
        }
    },
    "scale_range": [0.0, 5000.0],
    "color_ramp": [
        {
            "value": 0.0,
            "color": "#000000",
        },
        {
            "value": 6.0,
            "color": "#0000ff"
        }
    ],
}

style_alos_hv_over_hh = {
    "name": "hh_hv_hv_over_hh",
    "title": "HH, HV and HV/HH",
    "abstract": "False colour representation of HH, HV and HV over HH for R, G and B respectively",
    # Mixing ratio between linear components and colour ramped index. 1.0 is fully linear components, 0.0 is fully colour ramp.
    "component_ratio": 0.5,
    "index_function": {
        "function": "datacube_ows.band_utils.band_quotient",
        "pass_product_cfg": True,
        "kwargs": {
            "band1": "hh",
            "band2": "hv"
        }
    },
    "needed_bands": ["hh", "hv"],
    "range": [0.01, 2.0],
    "components": {
        "red": {
            "hh": 1.0
        },
        "green": {
            "hv": 1.0
        },
        "blue": {
            "hh": 0.0
        }
    },
    "scale_range": [0.0, 5000.0],
    "color_ramp": [
        {
            "value": 0.0,
            "color": "#000000",
        },
        {
            "value": 0.6,
            "color": "#0000ff"
        }
    ]
}


style_greyscale = {
    "name": "greyscale",
    "title": "Greyscale",
    "abstract": "Greyscale elevation",
    "needed_bands": ["elevation"],
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "elevation",
        }
    },
    "color_ramp": [
        {
            "value": -0,
            "color": "#383838",
            "alpha": 0.0
        },
        {
            "value": 0.1,
            "color": "#383838"
        },
        {
            "value": 250,
            "color": "#5e5e5e"
        },
        {
            "value": 500,
            "color": "#858585"
        },
        {
            "value": 1000,
            "color": "#adadad"
        },
        {
            "value": 2000,
            "color": "#d4d4d4"
        },
        {
            "value": 4000,
            "color": "#fafafa",
            "legend": {
                "prefix": ">"
            }
        }
    ],
    "legend": {
        "title": "Elevation ",
        "radix_point": 0,
        "scale_by": 1,
        "major_ticks": 100,
        "units": "m"
    }
}

style_colours = {
    "name": "colours",
    "title": "Coloured",
    "abstract": "Coloured elevation",
    "needed_bands": ["elevation"],
    "index_function": {
        "function": "datacube_ows.band_utils.single_band",
        "pass_product_cfg": True,
        "kwargs": {
            "band": "elevation",
        }
    },
    "color_ramp": [
        {
            "value": -0,
            "color": "#e1f2ff",
            "alpha": 0.0
        },
        {
            "value": 0.1,
            "color": "#41c23c"
        },
        {
            "value": 150,
            "color": "#f9a80e"
        },
        {
            "value": 300,
            "color": "#cb5f3e"
        },
        {
            "value": 400,
            "color": "#9d387d"
        },
        {
            "value": 500,
            "color": "#ba6daa"
        },
        {
            "value": 900,
            "color": "#d7a2d6"
        },
        {
            "value": 1200,
            "color": "#e6c8e6"
        },
        {
            "value": 4000,
            "color": "#ffecf9",
            "legend": {
                "prefix": ">"
            }
        }
    ],
    "legend": {
        "title": "Elevation ",
        "radix_point": 0,
        "scale_by": 1,
        "major_ticks": 400,
        "units": "m"
    }
}

# Actual Configuration

ows_cfg = {
    "global": {
        # Master config for all services and products.
        "response_headers": {
            "Access-Control-Allow-Origin": "*",  # CORS header
        },
        "services": {
            "wms": True,
            "wcs": True,
            "wmts": True,
        },
        "published_CRSs": {
            "EPSG:3857": {  # Web Mercator
                "geographic": False,
                "horizontal_coord": "x",
                "vertical_coord": "y",
            },
            "EPSG:3577": {  # GDA-94, Australian Albers. Not sure why, but it's required!
                "geographic": False,
                "horizontal_coord": "x",
                "vertical_coord": "y",
            },
            "EPSG:4326": {  # WGS-84
                "geographic": True,
                "vertical_coord_first": True
            },
            "EPSG:6933": {  # Cylindrical equal area
                "geographic": False,
                "horizontal_coord": "x",
                "vertical_coord": "y",
            },
            "ESRI:102022": {
                "geographic": False,
                "horizontal_coord": "x",
                "vertical_coord": "y",
            }
        },
        "allowed_urls": [
                "https://ows.digitalearth.africa"
        ],
        # Metadata to go straight into GetCapabilities documents
        "title": "Digital Earth Africa - OGC Web Services",
        "abstract": """Digital Earth Africa OGC Web Services""",
        "info_url": "dea.ga.gov.au/",
        "keywords": [
            "landsat",
            "africa",
            "WOfS",
            "fractional-cover",
            "time-series",
        ],
        "contact_info": {
            "person": "Digital Earth Africa",
            "organisation": "Geoscience Australia",
            "position": "",
            "address": {
                "type": "postal",
                "address": "GPO Box 378",
                "city": "Canberra",
                "state": "ACT",
                "postcode": "2609",
                "country": "Australia",
            },
            "telephone": "+61 2 6249 9111",
            "fax": "",
            "email": "earth.observation@ga.gov.au",
        },
        "fees": "",
        "access_constraints": "© Commonwealth of Australia (Geoscience Australia) 2018. "
                              "This product is released under the Creative Commons Attribution 4.0 International Licence. "
                              "http://creativecommons.org/licenses/by/4.0/legalcode",
    }, # END OF global SECTION
    "wms": {
        # Config for WMS service, for all products/layers
        "s3_url": "https://data.digitalearth.africa",
        "s3_bucket": "deafrica-data",
        "s3_aws_zone": "ap-southeast-2",

        "max_width": 512,
        "max_height": 512,
    }, # END OF wms SECTION
    "wcs": {
        # Config for WCS service, for all products/coverages
        "default_geographic_CRS": "EPSG:4326",
        "formats": {
            "GeoTIFF": {
                # "renderer": "datacube_ows.wcs_utils.get_tiff",
                "renderers": {
                    "1": "datacube_ows.wcs1_utils.get_tiff",
                    "2": "datacube_ows.wcs2_utils.get_tiff",
                },
                "mime": "image/geotiff",
                "extension": "tif",
                "multi-time": False
            },
            "netCDF": {
                # "renderer": "datacube_ows.wcs_utils.get_netcdf",
                "renderers": {
                    "1": "datacube_ows.wcs1_utils.get_netcdf",
                    "2": "datacube_ows.wcs2_utils.get_netcdf",
                },
                "mime": "application/x-netcdf",
                "extension": "nc",
                "multi-time": True,
            },
        },
        "native_format": "GeoTIFF",
    }, # END OF wcs SECTION
    "layers": [
        {
            "title": "Digital Earth Africa - OGC Web Services",
            "abstract": "Digital Earth Africa OGC Web Services",
            "layers": [
                # Hierarchical list of layers.  May be a combination of unnamed/unmappable folder-layers or named mappable layers.
                {
                    "title": "Landsat",
                    "abstract": """Landsat represents a collection of space-based land remote sensing data. Surface reflectance
                        measures incoming solar radiation reflected from the Earth to the Landsat sensor, which improves comparison
                        between multiple images over the same region. This helps us detect Earth surface changes. This dataset
                        includes Landsat 8 US Geological Survey Collection 1 Higher Level SR scene processed using LaSRC. 30m UTM
                        based projection.""",
                    "layers": [
                    {
                        "title": "Surface Reflectance Landsat 8 (USGS Collection 1)",
                        "name": "ls8_usgs_sr_scene",
                        "abstract": """
Surface reflectance is the fraction of incoming solar radiation that is reflected from Earth's surface. Variations in satellite measured radiance due to atmospheric properties have been corrected for, so images acquired over the same area at different times are comparable and can be used readily to detect changes on Earth’s surface.

DE Africa contains Landsat Collection 1, Level 2 surface reflectance products over five countries (Tanzania, Senegal, Sierra Leone, Ghana, and Kenya). Landsat Collection 1 consists of products generated from the Landsat 8 Operational Land Imager (OLI) / Thermal Infrared Sensor (TIRS), Landsat 7 Enhanced Thematic Mapper Plus (ETM+), Landsat 4-5 Thematic Mapper (TM), and Landsat 1-5 Multispectral Scanner (MSS) instruments. The implementation of collections ensures consistent and known radiometric and geometric quality through time and across instruments and improves control in the calibration and processing parameters.

This product has a spatial resolution of 30 m and a temporal coverage of 2013 to 2019. The surface reflectance values are scaled to be between 0 and 10,000.

It is provided by United States Geological Survey (USGS).

For more information on the Landsat surface reflectance product, see https://www.usgs.gov/land-resources/nli/landsat/landsat-surface-reflectance

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "ls8_usgs_sr_scene",
                        "bands": bands_ls,
                        "resource_limits": reslim_landsat,
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                            "always_fetch_bands": [],
                            "manual_merge": False, # True
                            "apply_solar_corrections": False,
                        },
                        "wcs": {
                            "native_crs": "EPSG:4326",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["red", "green", "blue"]
                        },
                        "styling": {
                            "default_style": "simple_rgb",
                            "styles": [
                                style_ls_simple_rgb,
                                style_ls_irg, style_ls_ndvi, style_ls_ndwi, style_ls_mndwi,
                                style_ls_pure_blue, style_ls_pure_green, style_ls_pure_red,
                                style_sentinel_pure_nir, style_sentinel_pure_swir1, style_sentinel_pure_swir2,
                            ]
                        }
                    },
                    {
                        "title": "Surface Reflectance Landsat 7 (USGS Collection 1)",
                        "name": "ls7_usgs_sr_scene",
                        "abstract": """
Surface reflectance is the fraction of incoming solar radiation that is reflected from Earth's surface. Variations in satellite measured radiance due to atmospheric properties have been corrected for so images acquired over the same area at different times are comparable and can be used readily to detect changes on Earth’s surface.

DE Africa contains Landsat Collection 1, Level 2 surface reflectance products over five countries (Tanzania, Senegal, Sierra Leone, Ghana, and Kenya). Landsat Collection 1 consists of products generated from the Landsat 8 Operational Land Imager (OLI) / Thermal Infrared Sensor (TIRS), Landsat 7 Enhanced Thematic Mapper Plus (ETM+), Landsat 4-5 Thematic Mapper (TM), and Landsat 1-5 Multispectral Scanner (MSS) instruments. The implementation of collections ensures consistent and known radiometric and geometric quality through time and across instruments and improves control in the calibration and processing parameters.

This product has a spatial resolution of 30 m and a temporal coverage of 1999 to 2019. The surface reflectance values are scaled to be between 0 and 10,000.

It is provided by United States Geological Survey (USGS).

For more information on the Landsat surface reflectance product, see https://www.usgs.gov/land-resources/nli/landsat/landsat-surface-reflectance

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "ls7_usgs_sr_scene",
                        "bands": bands_ls,
                        "resource_limits": reslim_landsat,
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                            "always_fetch_bands": [],
                            "manual_merge": False, # True
                            "apply_solar_corrections": False,
                        },
                        "wcs": {
                            "native_crs": "EPSG:4326",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["red", "green", "blue"]
                        },
                        "styling": {
                            "default_style": "simple_rgb",
                            "styles": [
                                style_ls_simple_rgb,
                                style_ls_irg, style_ls_ndvi, style_ls_ndwi, style_ls_mndwi,
                                style_sentinel_pure_blue, style_ls_pure_green, style_ls_pure_red,
                                style_ls_pure_nir, style_ls_pure_swir1, style_ls_pure_swir2,
                            ]
                        }
                    },
                    {
                        "title": "Surface Reflectance Landsat 5 (USGS Collection 1)",
                        "name": "ls5_usgs_sr_scene",
                        "abstract": """
Surface reflectance is the fraction of incoming solar radiation that is reflected from Earth's surface. Variations in satellite measured radiance due to atmospheric properties have been corrected for so images acquired over the same area at different times are comparable and can be used readily to detect changes on Earth’s surface.

DE Africa contains Landsat Collection 1, Level 2 surface reflectance products over five countries (Tanzania, Senegal, Sierra Leone, Ghana, and Kenya). Landsat Collection 1 consists of products generated from the Landsat 8 Operational Land Imager (OLI) / Thermal Infrared Sensor (TIRS), Landsat 7 Enhanced Thematic Mapper Plus (ETM+), Landsat 4-5 Thematic Mapper (TM), and Landsat 1-5 Multispectral Scanner (MSS) instruments. The implementation of collections ensures consistent and known radiometric and geometric quality through time and across instruments and improves control in the calibration and processing parameters.

This product has a spatial resolution of 30 m and a temporal coverage of 1984 to 2011. The surface reflectance values are scaled to be between 0 and 10,000.

It is provided by United States Geological Survey (USGS).

For more information on the Landsat surface reflectance product, see https://www.usgs.gov/land-resources/nli/landsat/landsat-surface-reflectance

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "ls5_usgs_sr_scene",
                        "bands": bands_ls,
                        "resource_limits": reslim_landsat,
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                            "always_fetch_bands": [],
                            "manual_merge": False, # True
                            "apply_solar_corrections": False,
                        },
                        "wcs": {
                            "native_crs": "EPSG:4326",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["red", "green", "blue"]
                        },
                        "styling": {
                            "default_style": "simple_rgb",
                            "styles": [
                                style_ls_simple_rgb,
                                style_ls_irg, style_ls_ndvi, style_ls_ndwi, style_ls_mndwi,
                                style_sentinel_pure_blue, style_ls_pure_green, style_ls_pure_red,
                                style_ls_pure_nir, style_ls_pure_swir1, style_ls_pure_swir2,
                            ]
                        }
                    },
                ]
            },
            {
                    "title": "Sentinel",
                    "abstract": """Sentinel""",
                    "layers": [
                    {
                        "title": "Surface Reflectance Sentinel-2",
                        "name": "s2_l2a",
                        "abstract": """
Surface reflectance is the fraction of incoming solar radiation that is reflected from Earth's surface. Variations in satellite measured radiance due to atmospheric properties have been corrected for, so images acquired over the same area at different times are comparable and can be used readily to detect changes on Earth’s surface.

DE Africa provides Sentinel 2 Level-2A surface reflectance data from European Commission's Copernicus Programme. Sentinel-2 is an Earth observation mission that systematically acquires optical imagery at up to 10 m spatial resolution. The mission is based on a constellation of two identical satellites in the same orbit, 180° apart for optimal coverage and data delivery. Together, they cover all Earth's land surfaces, large islands, inland and coastal waters every 3-5 days. Each of the Sentinel-2 satellites carries a wide swath high-resolution multispectral imager with 13 spectral bands.

This product has a temporal coverage of 2015 to current and is updated as new images are acquired. Images in different spectral bands are provided at spatial resolutions of 10, 20 or 60 m. The surface reflectance values are scaled to be between 0 and 10,000.

Sentinel-2 Level-2A data are provided by the European Space Agency (ESA).  Data prior to 2017 are processed from Level-1C to Level-2A with ESA's Sen2Cor software by Sinergise. All images are converted to Cloud Optimised GeoTIFF format by Element 84, Inc.

For more information on the Sentinel-2 Level-2A surface reflectance product, see https://earth.esa.int/web/sentinel/technical-guides/sentinel-2-msi/level-2a/algorithm

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "s2_l2a",
                        "bands": bands_sentinel,
                        "dynamic": True,
                        "resource_limits": reslim_srtm,
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                            "always_fetch_bands": [],
                            "manual_merge": False, # True
                            "apply_solar_corrections": False,
                        },
                        "wcs": {
                            "native_crs": "EPSG:4326",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["red", "green", "blue"]
                        },
                        "styling": {
                            "default_style": "simple_rgb",
                            "styles": [
                                style_ls_simple_rgb,
                                style_s2_irg,
                                style_ls_ndvi, style_ls_ndwi, style_gals_mndwi, style_s2_ndci,
                                style_s2_pure_aerosol,
                                style_sentinel_pure_blue, style_ls_pure_green, style_ls_pure_red,
                                style_s2_pure_redge_1, style_s2_pure_redge_2, style_s2_pure_redge_3,
                                style_ls_pure_nir, style_s2_pure_narrow_nir,
                                style_s2_pure_swir1, style_s2_pure_swir2,
                            ]
                        }
                    },
                ]
            },
            {
                "title": "Water Observations from Space",
                "abstract": """WOfS""",
                "layers": [
                    {
                        "title": "Water Observations from Space Feature Layer (Development)",
                        "name": "ls_usgs_wofs_scene",
                        "abstract": """
Water Observations from Space (WOfS) provides surface water observations derived from satellite imagery for all of Africa. The WOfS product allows users to get a better understanding of where water is normally present in a landscape, where water is seldom observed, and where inundation has occurred occasionally. Data is provided as Water Observation Feature Layers (WOFLs), in a 1 to 1 relationship with the input satellite data. Hence there is one WOFL for each satellite dataset processed for the occurrence of water.

This product has a spatial resolution of 30 m and a temporal coverage of 1984 to 2019.

It is derived from Landsat 5, 7 and 8 satellites observations as part of Landsat Collection 1, Level 2 surface reflectance products over five countries (Tanzania, Senegal, Sierra Leone, Ghana, and Kenya).

Daily water observations can be used to map historical flood and to understand surface water dynamics.

WOfS shows surface water on the day and time that satellite passed overhead, which might be before, during or after a flood peak. Given the time between satellite passes (approximately once every 16 days) it is unlikely that the satellite will capture the maximum extent of any given flood. Instead, it aims to provide large scale, regional information on surface water.

For more information on the algorithm, see https://doi.org/10.1016/j.rse.2015.11.003

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "ls_usgs_wofs_scene",
                        "bands": bands_wofs_obs,
                        "resource_limits": reslim_wofs_daily,
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_bitflag",
                            "always_fetch_bands": [],
                            "manual_merge": False,
                        },
                        "wcs": {
                            "native_crs": "EPSG:4326",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["water"]
                        },
                        "styling": {
                            "default_style": "observations",
                            "styles": [
                                    style_wofs_obs,  style_wofs_obs_wet_only,
                            ]
                        }
                    },
                    {
                        "title": "Water Observations from Space Feature Layer (Beta)",
                        "name": "ga_ls8c_wofs_2",
                        "abstract": """
Water Observations from Space (WOfS) provides surface water observations derived from satellite imagery for all of Africa. The WOfS product allows users to get a better understanding of where water is normally present in a landscape, where water is seldom observed, and where inundation has occurred occasionally. Data is provided as Water Observation Feature Layers (WOFLs), in a 1 to 1 relationship with the input satellite data. Hence there is one WOFL for each satellite dataset processed for the occurrence of water.

This product has a spatial resolution of 30 m and a temporal coverage of 2013 to 2019.

It is derived from Landsat 8 satellite observations as part of a provisional Landsat Collection 2 surface reflectance product.

Daily water observations can be used to map historical flood and to understand surface water dynamics.

WOfS shows surface water on the day and time that satellite passed overhead, which might be before, during or after a flood peak. Given the time between satellite passes (approximately once every 16 days) it is unlikely that the satellite will capture the maximum extent of any given flood. Instead, it aims to provide large scale, regional information on surface water.

For more information on the algorithm, see https://doi.org/10.1016/j.rse.2015.11.003

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "ga_ls8c_wofs_2",
                        "bands": bands_wofs_obs,
                        "resource_limits": reslim_wofs_daily,
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_bitflag",
                            "always_fetch_bands": [],
                            "manual_merge": False,
                        },
                        "wcs": {
                            "native_crs": "EPSG:4326",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["water"]
                        },
                        "styling": {
                            "default_style": "observations",
                            "styles": [
                                style_wofs_obs,  style_wofs_obs_wet_only,
                            ]
                        }
                    },
                    {
                        "title": "Water Observations from Space Annual Summary (Development)",
                        "name": "wofs_annual_summary_frequency",
                        "abstract": """
Annual water summary is one of the statistical summaries of the Water Observation from Space (WOfS) product that shows what percentage of clear observations were detected as wet (ie. the ration of wet to clear as a percentage) from each calendar year.

This product has a spatial resolution of 30 m and a temporal coverage of 1984 to 2019.

It is derived from Landsat 5, 7 and 8 satellites observations as part of Landsat Collection 1, Level 2 surface reflectance products over five countries (Tanzania, Senegal, Sierra Leone, Ghana, and Kenya).

The annual summaries can be used to understand year to year changes in surface water extent.

WOfS shows surface water on the day and time that satellite passed overhead, which might be before, during or after a flood peak. Given the time between satellite passes (approximately once every 16 days) it is unlikely that the satellite will capture the maximum extent of any given flood. Instead, it aims to provide large scale, regional information on surface water.

For more information on the algorithm, see https://doi.org/10.1016/j.rse.2015.11.003

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "ls_usgs_wofs_summary",
                        "time_resolution": "year",
                        "bands": bands_usgs_wofs_summary,
                        "resource_limits": reslim_wofs_dry,
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                            "always_fetch_bands": [],
                            "manual_merge": False,
                        },
                        "wcs": {
                            "native_crs": "ESRI:102022",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["frequency"]
                        },
                        "styling": {
                            "default_style": "WOfS_frequency",
                            "styles": [
                                    style_wofs_annual_summary_frequency,  style_wofs_annual_frequency_blue,
                            ]
                        }
                    },
#                     {
#                         "title": "Water Observations from Space Annual Count of Wet Observations (Development)",
#                         "name": "wofs_annual_summary_wet",
#                         "abstract": """
# The count of wet observations is one of the statistical summaries of the Water Observation from Space (WOfS) product that shows how many times water was detected in observations that were clear. This product was used as a source layer for calculating annual water summary.

# This product has a spatial resolution of 30 m and a temporal coverage of 1984 to 2019.

# It is derived from Landsat 5, 7 and 8 satellites observations as part of Landsat Collection 1, Level 2 surface reflectance products over five countries (Tanzania, Senegal, Sierra Leone, Ghana, and Kenya).

# For more information on the algorithm, see https://doi.org/10.1016/j.rse.2015.11.003

# This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
# """,
#                         "product_name": "ls_usgs_wofs_summary",
#                         "time_resolution": "year",
#                         "bands": bands_usgs_wofs_summary,
#                         "resource_limits": reslim_wofs_dry,
#                         "image_processing": {
#                             "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
#                             "always_fetch_bands": [],
#                             "manual_merge": False,
#                         },
#                         "wcs": {
#                             "native_crs": "ESRI:102022",
#                             "native_resolution": [25.0, 25.0],
#                             "default_bands": ["count_wet"]
#                         },
#                         "styling": {
#                             "default_style": "water_observations",
#                             "styles": [
#                                     style_wofs_count_wet,
#                             ]
#                         }
#                     },
#                     {
#                         "title": "Water Observations from Space Annual Count of Clear Observations (Development)",
#                         "name": "wofs_annual_summary_clear",
#                         "abstract": """
# The count of clear observations is one of the statistical summaries of the Water Observations from Space (WOfS) product that shows how many times an area could be clearly seen (I.e. not affected by clouds, shadows or other satellite observation problems). This product was used as a source layer for calculating annual water summary.

# This product has a spatial resolution of 30 m and a temporal coverage of 1984 to 2019.

# It is derived from Landsat 5, 7 and 8 satellites observations as part of Landsat Collection 1, Level 2 surface reflectance products over five countries (Tanzania, Senegal, Sierra Leone, Ghana, and Kenya).

# For more information on the algorithm, see https://doi.org/10.1016/j.rse.2015.11.003

# This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
# """,
#                         "product_name": "ls_usgs_wofs_summary",
#                         "bands": bands_usgs_wofs_summary,
#                         "resource_limits": reslim_wofs_dry,
#                         "image_processing": {
#                             "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
#                             "always_fetch_bands": [],
#                             "manual_merge": False,
#                         },
#                         "wcs": {
#                             "native_crs": "ESRI:102022",
#                             "native_resolution": [25.0, 25.0],
#                             "default_bands": ["count_dry"]
#                         },
#                         "styling": {
#                             "default_style": "annual_clear_observations",
#                             "styles": [
#                                     style_wofs_annual_clear,
#                             ]
#                         }
#                     },
                ]
            },
            {
                    "title": "Water Observations from Space c2",
                    "abstract": """WOfS""",
                    "layers": [
                    {
                        "title": "Water Observations from Space Annual Summary (Beta)",
                        "name": "wofs_2_annual_summary_frequency",
                        "abstract": """
Annual water summary is one of the statistical summaries of the Water Observation from Space (WOfS) product that shows what percentage of clear observations were detected as wet (ie. the ration of wet to clear as a percentage) from each calendar year.

This product has a spatial resolution of 30 m and a temporal coverage of 2013 to 2019.

It is derived from Landsat 8 satellite observations as part of a provisional Landsat Collection 2 surface reflectance product.

The annual summaries can be used to understand year to year changes in surface water extent.

WOfS shows surface water on the day and time that satellite passed overhead, which might be before, during or after a flood peak. Given the time between satellite passes (approximately once every 16 days) it is unlikely that the satellite will capture the maximum extent of any given flood. Instead, it aims to provide large scale, regional information on surface water.

For more information on the algorithm, see https://doi.org/10.1016/j.rse.2015.11.003

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "ga_ls8c_wofs_2_annual_summary",
                        "time_resolution": "year",
                        "bands": bands_wofs_2_annual_summary,
                        "resource_limits": reslim_wofs,
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                            "always_fetch_bands": [],
                            "manual_merge": False,
                        },
                        "wcs": {
                            "native_crs": "EPSG:6933",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["frequency"]
                        },
                        "styling": {
                            "default_style": "WOfS_frequency",
                            "styles": [
                                    style_wofs_annual_summary_frequency, style_wofs_annual_summary_frequency_blue
                            ]
                        }
                    },
                    {
                        "title": "Water Observations from Space Annual Count of Wet Observations (Beta)",
                        "name": "wofs_2_annual_summary_wet",
                        "abstract": """
The count of wet observations is one of the statistical summaries of the Water Observation from Space (WOfS) product that shows how many times water was detected in observations that were clear. This product was used as a source layer for calculating annual water summary.

This product has a spatial resolution of 30 m and a temporal coverage of 2013 to 2019.

It is derived from Landsat 8 satellite observations as part of a provisional Landsat Collection 2 surface reflectance product.

For more information on the algorithm, see https://doi.org/10.1016/j.rse.2015.11.003

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "ga_ls8c_wofs_2_annual_summary",
                        "time_resolution": "year",
                        "bands": bands_wofs_2_annual_summary,
                        "resource_limits": reslim_wofs,
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                            "always_fetch_bands": [],
                            "manual_merge": False,
                        },
                        "wcs": {
                            "native_crs": "EPSG:6933",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["count_wet"]
                        },
                        "styling": {
                            "default_style": "water_observations",
                            "styles": [
                                    style_wofs_water_annual_wet,
                            ]
                        }
                    },
                    {
                        "title": "Water Observations from Space Annual Count of Clear Observations (Beta)",
                        "name": "wofs_2_annual_summary_clear",
                        "abstract": """
The count of clear observations is one of the statistical summaries of the Water Observations from Space (WOfS) product that shows how many times an area could be clearly seen (I.e. not affected by clouds, shadows or other satellite observation problems). This product was used as a source layer for calculating annual water summary.

This product has a spatial resolution of 30 m and a temporal coverage of 2013 to 2019.

It is derived from Landsat 8 satellite observations as part of a provisional Landsat Collection 2 surface reflectance product.

For more information on the algorithm, see https://doi.org/10.1016/j.rse.2015.11.003

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "ga_ls8c_wofs_2_annual_summary",
                        "time_resolution": "year",
                        "bands": bands_wofs_2_annual_summary,
                        "resource_limits": reslim_wofs,
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                            "always_fetch_bands": [],
                            "manual_merge": False,
                        },
                        "wcs": {
                            "native_crs": "EPSG:6933",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["count_clear"]
                        },
                        "styling": {
                            "default_style": "annual_clear_observations",
                            "styles": [
                                    style_wofs_beta_summary_clear,
                            ]
                        }
                    },
                    {
                        "title": "Water Observations from Space All Time Summary (Beta)",
                        "name": "wofs_2_summary_frequency",
                        "abstract": """
All time water summary is one of the statistical summaries of the Water Observation from Space (WOfS) product that shows what percentage of clear observations were detected as wet (ie. the ration of wet to clear as a percentage) over time.

This product has a spatial resolution of 30 m and a temporal coverage of 2013 to 2019.

It is derived from Landsat 8 satellite observations as part of a provisional Landsat Collection 2 surface reflectance product.

All time water summary can be used to understand water availability and flooding risk in a historical context.

WOfS shows surface water on the day and time that satellite passed overhead, which might be before, during or after a flood peak. Given the time between satellite passes (approximately once every 16 days) it is unlikely that the satellite will capture the maximum extent of any given flood. Instead, it aims to provide large scale, regional information on surface water.

For more information on the algorithm, see https://doi.org/10.1016/j.rse.2015.11.003

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "ga_ls8c_wofs_2_summary",
                        "bands": bands_wofs_2_annual_summary,
                        "time_resolution": "year",
                        "resource_limits": reslim_wofs,
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                            "always_fetch_bands": [],
                            "manual_merge": False,
                        },
                        "wcs": {
                            "native_crs": "EPSG:6933",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["frequency"]
                        },
                        "styling": {
                            "default_style": "WOfS_frequency",
                            "styles": [
                                    style_wofs_frequency, style_wofs_frequency_blue
                            ]
                        }
                    },
                    {
                        "title": "Water Observations from Space All Time Count of Wet Observations (Beta)",
                        "name": "wofs_2_summary_wet",
                        "abstract": """
The count of wet observations is one of the statistical summaries of the Water Observation from Space (WOfS) product that shows how many times water was detected in observations that were clear. This product was used as a source layer for calculating all time water summary.

This product has a spatial resolution of 30 m and a temporal coverage of 2013 to 2019.

It is derived from Landsat 8 satellite observations as part of a provisional Landsat Collection 2 surface reflectance product.

For more information on the algorithm, see https://doi.org/10.1016/j.rse.2015.11.003

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "ga_ls8c_wofs_2_summary",
                        "time_resolution": "year",
                        "bands": bands_wofs_2_annual_summary,
                        "resource_limits": reslim_wofs,
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                            "always_fetch_bands": [],
                            "manual_merge": False,
                        },
                        "wcs": {
                            "native_crs": "EPSG:6933",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["count_wet"]
                        },
                        "styling": {
                            "default_style": "water_observations",
                            "styles": [
                                    style_wofs_count_wet,
                            ]
                        }
                    },
                    {
                        "title": "Water Observations from Space All Time Count of Clear Observations (Beta)",
                        "name": "wofs_2_summary_clear",
                        "abstract": """
The count of clear observations is one of the statistical summaries of the Water Observations from Space (WOfS) product that shows how many times an area could be clearly seen (I.e. not affected by clouds, shadows or other satellite observation problems). This product was used as a source layer for calculating all time water summary.

This product has a spatial resolution of 30 m and a temporal coverage of 2013 to 2019.

It is derived from Landsat 8 satellite observations as part of a provisional Landsat Collection 2 surface reflectance product.

For more information on the algorithm, see https://doi.org/10.1016/j.rse.2015.11.003

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "ga_ls8c_wofs_2_summary",
                        "bands": bands_wofs_2_annual_summary,
                        "resource_limits": reslim_wofs,
                        "time_resolution": "year",
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                            "always_fetch_bands": [],
                            "manual_merge": False,
                        },
                        "wcs": {
                            "native_crs": "EPSG:6933",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["count_clear"]
                        },
                        "styling": {
                            "default_style": "annual_clear_observations",
                            "styles": [
                                    style_wofs_summary_clear,
                            ]
                        }
                    },

                ]
            },
            {
                "title": "Landsat",
                "abstract": "Landsat Fractional Cover based on USGS Level 2 Scenes",
                "layers": [
                    {
                        "title": "Fractional Cover (development)",
                        "name": "ls_usgs_fc_scene",
                        "abstract": """
Fractional cover describes the landscape in terms of coverage by green vegetation, non-green vegetation (including deciduous trees during autumn, dry grass, etc.) and bare soil. It provides insight into how areas of dry vegetation and/or bare soil and green vegetation are changing over time.

This product has a spatial resolution of 30 m and a temporal coverage of 1984 to 2019.

It is derived from Landsat 5, 7 and 8 satellites observations as part of Landsat Collection 1, Level 2 surface reflectance products over five countries (Tanzania, Senegal, Sierra Leone, Ghana, and Kenya).

Fractional cover allows users to understand the large scale patterns and trends and inform evidence based decision making and policy on topics including wind and water erosion risk, soil carbon dynamics, land surface process monitoring, land management practices, vegetation studies, fuel load estimation, ecosystem modelling, and rangeland condition.

The fractional cover algorithm was developed by the Joint Remote Sensing Research Program, for more information see http://data.auscover.org.au/xwiki/bin/view/Product+pages/Landsat+Seasonal+Fractional+Cover

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "ls_usgs_fc_scene",
                        "bands": bands_fc,
                        "resource_limits": reslim_srtm,
                        #"time_resolution": "year",
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                            "always_fetch_bands": [],
                            "manual_merge": False,
                        },
                        "wcs": {
                            "native_crs": "EPSG:4326",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["BS", "PV", "NPV"]
                        },
                        "styling": {
                            "default_style": "simple_fc",
                            "styles": [
                                style_fc_simple
                            ]
                        }
                    },

                ]
            },
            {
                    "title": "Annual Geometric Median",
                    "abstract": "Landsat Geomedian based on USGS Provisional Collection 2 Level 2 Scenes",
                    "layers": [
                    {
                        "title": "Surface Reflectance Annual Geomedian Landsat 8 (Beta)",
                        "name": "ga_ls8c_gm_2_annual",
                        "abstract": """
Individual remote sensing images can be affected by noisy data, including clouds, cloud shadows, and haze. To produce cleaner images that can be compared more easily across time, we can create 'summary' images or 'composites' that combine multiple images into one image to reveal the median or 'typical' appearance of the landscape for a certain time period. One approach is to create a geomedian. A geomedian is based on a high-dimensional statistic called the 'geometric median' (Small 1990), which effectively trades a temporal stack of poor-quality observations for a single high-quality pixel composite with reduced spatial noise (Roberts et al. 2017).

In contrast to a standard median, a geomedian maintains the relationship between spectral bands. This allows for conducting further analysis on the composite images just as we would on the original satellite images (e.g. by allowing the calculation of common band indices like NDVI). An annual median image is calculated from the surface reflectance values drawn from a calendar year.

This product has a spatial resolution of 30 m and a temporal coverage of 2018. The surface reflectance values are scaled to be between 0 and 65,455.

It is derived from Landsat 8 satellite observations as part of a provisional Landsat Collection 2 surface reflectance product.

Annual geomedian images enable easy visual and algorithmic interpretation, e.g. understanding urban expansion, at annual intervals. They are also useful for characterising permanent landscape features such as woody vegetation.

For more information on the algorithm, see https://doi.org/10.1109/TGRS.2017.2723896

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "ga_ls8c_gm_2_annual",
                        "time_resolution": "year",
                        "bands": bands_ls8c,
                        "resource_limits": reslim_srtm,
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                            "always_fetch_bands": [],
                            "manual_merge": False,
                        },
                        "wcs": {
                            "native_crs": "EPSG:6933",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["red", "green", "blue"]
                        },
                        "styling": {
                            "default_style": "simple_rgb",
                            "styles": [
                                style_gals_simple_rgb,
                                style_gals_irg,
                                style_ls_ndvi, style_ls_ndwi,
                                style_gals_mndwi,
                                style_gals_pure_blue, style_gals_pure_green, style_gals_pure_red,
                                style_gals_pure_nir,
                                style_gals_pure_swir1,
                                style_gals_pure_swir2,
                            ]
                        }
                    },

                ]
            },
            {
                    "title": "ALOS/PALSAR",
                    "abstract": """Annual mosaic of ALOS/PALSAR and ALOS-2/PALSAR-2 data""",
                    "layers": [
                    {
                        "title": "Radar Backscatter Annual Mosaic (ALOS/PALSAR)",
                        "name": "alos_palsar_mosaic",
                        "abstract": """
Synthetic Aperture Radar (SAR) data have been shown to provide different and complementary information to the more common optical remote sensing data. Radar backscatter response is a function of topography, land cover structure, orientation, and moisture characteristics—including vegetation biomass—and the radar signal can penetrate clouds, providing information about the earth’s surface where optical sensors cannot. Digital Earth Africa provides access to Normalized Radar Backscatter data, for which Radiometric Terrain Correction (RTC) has been applied so data acquired with different imaging geometries over the same region can be compared.

The ALOS/PALSAR annual mosaic is a global 25 m resolution dataset that combines data from many images captured by JAXA's PALSAR and PALSAR-2 sensors on ALOS-1 and ALOS-2 satellites respectively.

This product is generated from L-band radar observations. It has a spatial resolution of 25 m and is available annually for 2007 to 2010 (ALOS/PALSAR) and 2015 to current (ALOS-2/PALSAR-2).

It is part of a global dataset provided by the Japan Aerospace Exploration Agency (JAXA) Earth Observation Research Center.

For more information on the product, see https://www.eorc.jaxa.jp/ALOS/en/palsar_fnf/fnf_index.htm

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "alos_palsar_mosaic",
                        "time_resolution": "year",
                        "bands": bands_alos,
                        "resource_limits": reslim_alos_palsar,
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                            "always_fetch_bands": [],
                            "manual_merge": False,
                        },
                        "flags":{
                            "dataset": "alos_palsar_mosaic",
                            "band": "mask",
                            "ignore_info_flags": [],
                        },
                        "wcs": {

                            "native_crs": "EPSG:4326",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["hh", "hv", "mask"]
                        },
                        "styling": {
                            "default_style": "hh",
                            "styles": [
                                style_alos_hh, style_alos_hv, style_alos_hh_over_hv, style_alos_hv_over_hh
                            ]
                        }
                    },

                ]
            },
            {
                    "title": "Shuttle Radar Topography Mission",
                    "abstract": """Digital elevation model from NASA's SRTM<""",
                    "layers": [
                    {
                        "title": "Shuttle Radar Topography Mission Digital Elevation Model",
                        "name": "srtm",
                        "abstract": """
A Digital Elevation Model (DEM) is a digital representation of Earth’s topography. It helps to understand the land surface characteristics in the height dimension. It is also used as an ancillary dataset to calculate illumination and viewing geometry of a satellite imagery. DE Africa provides access to the Shuttle Radar Topography Mission (SRTM) v 3.0 (SRTMGL1) product.

This elevation model has a spatial resolution of 30 m and is derived from data collected by NASA's Shuttle Radar Topography Mission in 2000.

It is provided by NASA's Land Processes Distributed Active Archive Center (LP DAAC).

For more information, see https://lpdaac.usgs.gov/products/srtmgl1v003/

This product is accessible through OGC Web Service (https://ows.digitalearth.africa/), for analysis in DE Africa Sandbox JupyterLab (https://github.com/digitalearthafrica/deafrica-sandbox-notebooks/wiki) and for direct download from AWS S3 (https://data.digitalearth.africa/).
""",
                        "product_name": "srtm",
                        "time_resolution": "year",
                        "bands": bands_elevation,
                        "resource_limits": reslim_srtm,
                        "image_processing": {
                            "extent_mask_func": "datacube_ows.ogc_utils.mask_by_val",
                            "always_fetch_bands": [],
                            "manual_merge": False,
                        },
                        "wcs": {
                            "native_crs": "EPSG:4326",
                            "native_resolution": [25.0, 25.0],
                            "default_bands": ["elevation"]
                        },
                        "styling": {
                            "default_style": "greyscale",
                            "styles": [
                               style_greyscale, style_colours
                            ]
                        }
                    },

                ]
            },
        ]
    }
]
}