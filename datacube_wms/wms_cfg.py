# Static config for the wms metadata.

response_cfg = {
    "Access-Control-Allow-Origin": "*",   # CORS header
}

service_cfg = {
    # Required config
    "title": "WMS server for Australian Landsat Datacube",
    "url": "http://localhost:5000/",
    "published_CRSs": {
        "EPSG:3857": { # Web Mercator
            "geographic": False,
            "horizontal_coord": "x",
            "vertical_coord": "y",
        },
        "EPSG:4326": { # WGS-84
            "geographic": True,
        },
        "EPSG:3577": { # GDA-94, internal representation
            "geographic": False,
            "horizontal_coord": "easting",
            "vertical_coord": "northing",
        },
    },
    
    # Technically optional config, but strongly recommended
    "layer_limit": 1,
    "max_width": 512,
    "max_height": 512,

    # Optional config - may be set to blank/empty
    "abstract": """Historic Landsat imagery for Australia.""",
    "keywords": [
        "landsat",
        "australia",
        "time-series",
    ],
    "contact_info": {
        "person": "David Gavin",
        "organisation": "Geoscience Australia",
        "position": "Technical Lead",
        "address": {
            "type": "postal",
            "address": "GPO Box 378",
            "city": "Canberra",
            "state": "ACT",
            "postcode": "2906",
            "country": "Australia",
        },
        "telephone": "+61 2 1234 5678",
        "fax": "+61 2 1234 6789",
        "email": "test@example.com",
    },
    "fees": "",
    "access_constraints": "",
}

layer_cfg = [
    # Layer Config is a list of platform configs
    {
        # Name and title of the platform layer.
        # Platform layers are not mappable. The name is for internal server use only.
        "name": "LANDSAT_8",
        "title": "Landsat 8",
        "abstract": "Images from the Landsat 8 satellite",

        # Products available for this platform.
        # For each product, the "name" is the Datacube name, and the label is used
        # to describe the label to end-users.
        "products": [
            {
                "label": "NBAR-T",
                "type": "surface reflectance",
                "variant": "terrain corrected",
                "name": "ls8_nbart_albers",
                "product_name": "ls8_nbart_albers",
                "pq_dataset": "ls8_pq_albers",
                "pq_band": "pixelquality",
                "min_zoom_factor": 500.0,
                "zoomed_out_fill_colour": [ 150, 180, 200, 160]
            },
        ],
        # Styles.
        # The various available spectral bands, and ways to combine them
        # into a single rgb image.
        # The examples here are ad hoc and the format only supports linear combinations of bands.
        # More specialised mappings could be adapted from this site, but most would require support for
        # non-linear band combinations and colour gradient mapping:
        # LS7:  http://www.indexdatabase.de/db/s-single.php?id=8
        # LS8:  http://www.indexdatabase.de/db/s-single.php?id=168
        # TODO: What about masking rules?
        "styles": [
            {
                "name": "simple_rgb",
                "title": "Simple RGB",
                "abstract": "Simple true-colour image, using the red, green and blue bands",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            },
            {
                "name": "cloud_masked_rgb",
                "title": "Simple RGB with cloud masking",
                "abstract": "Simple true-colour image, using the red, green and blue bands, with cloud masking",
                "heat_mapped": False,
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
                "pq_mask_flags": {
                    "cloud_acca": "no_cloud",
                    "cloud_fmask": "no_cloud",
                },
                "scale_factor": 12.0
            },
            {
                "name": "extended_rgb",
                "title": "Extended RGB",
                "abstract": "Extended true-colour image, incorporating the coastal aerosol band",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            },
            {
                "name": "wideband",
                "title": "Wideband false-colour",
                "abstract": "False-colour image, incorporating all available spectral bands",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            },
            {
                "name": "infra_red",
                "title": "False colour multi-band infra-red",
                "abstract": "Simple false-colour image, using the near and short-wave infra-red bands",
                "heat_mapped": False,
                "components": {
                    "red": {
                        "swir1": 1.0
                    },
                    "green": {
                        "swir2": 1.0
                    },
                    "blue": {
                        "nir": 1.0
                    }
                },
                "scale_factor": 12.0
            },
            {
                "name": "coastal_aerosol",
                "title": "Spectral band 1 - Coastal aerosol",
                "abstract": "Coastal aerosol band, approximately 435nm to 450nm",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            },
            {
                "name": "blue",
                "title": "Spectral band 2 - Blue",
                "abstract": "Blue band, approximately 453nm to 511nm",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            },
            {
                "name": "green",
                "title": "Spectral band 3 - Green",
                "abstract": "Green band, approximately 534nm to 588nm",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            },
            {
                "name": "red",
                "title": "Spectral band 4 - Red",
                "abstract": "Red band, roughly 637nm to 672nm",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            },
            {
                "name": "nir",
                "title": "Spectral band 5 - Near infra-red",
                "abstract": "Near infra-red band, roughly 853nm to 876nm",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            },
            {
                "name": "swir1",
                "title": "Spectral band 6 - Short wave infra-red 1",
                "abstract": "Short wave infra-red band 1, roughly 1575nm to 1647nm",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            },
            {
                "name": "swir2",
                "title": "Spectral band 7 - Short wave infra-red 2",
                "abstract": "Short wave infra-red band 2, roughly 2117nm to 2285nm",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            },
            {
                "name": "ndvi",
                "title": "NDVI",
                "abstract": "Normalised Difference Vegetation Index - a derived index that correlates well with the existence of vegetation",
                "heat_mapped": True,
                "index_function": lambda data: (data["nir"] - data["red"]) / (data["nir"] + data["red"]),
                "needed_bands": [ "red", "nir" ],
                "range": [ 0.0, 1.0 ],
            },
            {
                "name": "ndwi",
                "title": "NDWI",
                "abstract": "Normalised Difference Water Index - a derived index that correlates well with the existence of water",
                "heat_mapped": True,
                "index_function": lambda data: (data["green"] - data["nir"]) / (data["nir"] + data["green"]),
                "needed_bands": [ "green", "nir" ],
                "range": [ 0.0, 1.0 ],
            },
            {
                "name": "ndbi",
                "title": "NDBI",
                "abstract": "Normalised Difference Buildup Index - a derived index that correlates with the existence of urbanisation",
                "heat_mapped": True,
                "index_function": lambda data: (data["swir2"] - data["nir"]) / (data["swir2"] + data["nir"]),
                "needed_bands": [ "swir2", "nir" ],
                "range": [ 0.0, 1.0 ],
            }
        ],
        # Default style (if request does not specify style)
        # MUST be defined in the styles list above.
        # (Looks like Terria assumes this is the first style in the list, but this is
        #  not required by the standard.)
        "default_style": "simple_rgb",
    },
]

to_be_added_to_layer_cfg = {
        "name": "LANDSAT_7",
        "title": "Landsat 7",
        "abstract": "Images from the Landsat 7 satellite",

        "products": [
            {
                "label": "NBAR-T",
                "type": "surface reflectance",
                "variant": "terrain corrected",
                "name": "ls7_nbart_albers",
                "product_name": "ls7_nbart_albers",
                "pq_dataset": "ls7_pq_albers",
                "pq_band": "pixelquality",
                "pq_mask_flags": {
                    "contiguous": True
                },
                "min_zoom_factor": 500.0
            },
        ],
        "styles": [
            {
                "name": "simple_rgb",
                "title": "Simple RGB",
                "abstract": "Simple true-colour image, using the red, green and blue bands",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            },
            {
                "name": "wideband",
                "title": "Wideband false-colour",
                "abstract": "False-colour image, incorporating all available spectral bands",
                "heat_mapped": False,
                "components": {
                    "red": {
                        "swir2": 0.5,
                        "swir1": 0.5,
                    },
                    "green": {
                        "nir": 0.5,
                        "red": 0.5,
                    },
                    "blue": {
                        "green": 0.5,
                        "blue": 0.5,
                    }
                },
                "scale_factor": 12.0
            },
            {
                "name": "infra_red",
                "title": "False colour multi-band infra-red",
                "abstract": "Simple false-colour image, using the near and short-wave infra-red bands",
                "heat_mapped": False,
                "components": {
                    "red": {
                        "swir1": 1.0
                    },
                    "green": {
                        "swir2": 1.0
                    },
                    "blue": {
                        "nir": 1.0
                    }
                },
                "scale_factor": 12.0
            },
            {
                "name": "blue",
                "title": "Spectral band 1 - Blue",
                "abstract": "Blue band, approximately 450nm to 520nm",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            },
            {
                "name": "green",
                "title": "Spectral band 2 - Green",
                "abstract": "Green band, approximately 530nm to 610nm",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            },
            {
                "name": "red",
                "title": "Spectral band 3 - Red",
                "abstract": "Red band, roughly 630nm to 690nm",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            },
            {
                "name": "nir",
                "title": "Spectral band 4 - Near infra-red",
                "abstract": "Near infra-red band, roughly 780nm to 840nm",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            },
            {
                "name": "swir1",
                "title": "Spectral band 5 - Short wave infra-red 1",
                "abstract": "Short wave infra-red band 1, roughly 1550nm to 1750nm",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            },
            {
                "name": "swir2",
                "title": "Spectral band 6 - Short wave infra-red 2",
                "abstract": "Short wave infra-red band 2, roughly 2090nm to 2220nm",
                "heat_mapped": False,
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
                "scale_factor": 12.0
            }
        ],
        "default_style": "simple_rgb",
}
