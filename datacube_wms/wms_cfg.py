# Static config for the wms metadata.

response_cfg = {
    "Access-Control-Allow-Origin": "*",   # CORS header
}

service_cfg = {
    # Required config
    "title": "WMS server for Australian Landsat Datacube",
    "url": "http://localhost:5000/",
    "published_CRSs": [
        "EPSG:3857",   # Web Mercator
        "EPSG:4326",   # WGS-84
        "EPSG:3577"    # GDA-94, internal representation
    ],
    
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
                "scale_factor": 12.0
            },
            {
                "name": "wideband",
                "title": "Wideband false-colour",
                "abstract": "False-colour image, incorporating all available spectral bands",
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
        # Default style (if request does not specify style)
        # MUST be defined in the styles list above.
        # (Looks like Terria assumes this is the first style in the list, but this is
        #  not required by the standard.)
        "default_style": "simple_rgb",
    }
]
