# Static config for the wms metadata.
# pylint: skip-file
response_cfg = {
    "Access-Control-Allow-Origin": "*",  # CORS header
}

service_cfg = {
    ## Which web service(s) should be supported by this instance
    "wcs": True,
    "wms": True,
    "wmts": False,

    ## Required config for WMS and/or WCS
    # Service title - appears e.g. in Terria catalog
    "title": "WMS server for Australian Landsat Datacube",
    # Service URL.  Should a fully qualified URL
    "url": "http://9xjfk12.nexus.csiro.au/datacube_wms",

    # Supported co-ordinate reference systems
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

    ## Required config for WCS
    # Must be a geographic CRS in the published_CRSs list.  EPSG:4326 is recommended, but any geographic CRS should work.
    "default_geographic_CRS": "EPSG:4326",

    # Supported WCS formats
    "wcs_formats": {
        # Key is the format name, as used in DescribeCoverage XML
        "GeoTIFF": {
            # Renderer is the FQN of a Python function that takes:
            #   * A WCS Request object
            #   * Some ODC data to be rendered.
            "renderer": "datacube_wms.wcs_utils.get_tiff",
            # The MIME type of the image, as used in the Http Response.
            "mime": "image/geotiff",
            # The file extension to add to the filename.
            "extension": "tif",
            # Whether or not the file format supports multiple time slices.
            "multi-time": False
        },
        "netCDF": {
            "renderer": "datacube_wms.wcs_utils.get_netcdf",
            "mime": "application/x-netcdf",
            "extension": "nc",
            "multi-time": True,
        }
    },
    # The native wcs format must be declared in wcs_formats above.
    "native_wcs_format": "GeoTIFF",

    ## Optional config for instances supporting WMS
    # Max tile height/width.  If not specified, default to 256x256
    "max_width": 512,
    "max_height": 512,

    # Optional config for all services (WMS and/or WCS) - may be set to blank/empty, no defaults
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
                # Included as a keyword  for the layer
                "label": "NBAR-T",
                # Included as a keyword  for the layer
                "type": "surface reflectance",
                # Included as a keyword  for the layer
                "variant": "terrain corrected",
                # The WMS name for the layer
                "name": "ls8_nbart_albers",
                # The Datacube name for the associated data product
                "product_name": "ls8_nbart_albers",
                # The Datacube name for the associated pixel-quality product (optional)
                # The name of the associated Datacube pixel-quality product
                "pq_dataset": "ls8_pq_albers",
                # The name of the measurement band for the pixel-quality product
                # (Only required if pq_dataset is set)
                "pq_band": "pixelquality",
                # Min zoom factor - sets the zoom level where the cutover from indicative polygons
                # to actual imagery occurs.
                "min_zoom_factor": 500.0,
                # Min zoom factor (above) works well for small-tiled requests, (e.g. 256x256 as sent by Terria).
                # However, for large-tiled requests (e.g. as sent by QGIS), large and intensive queries can still
                # go through to the datacube.
                # max_datasets_wms specifies a maximum number of datasets that a GetMap request can retrieve.
                # Indicatative polygons are displayed if a request exceeds the limits imposed by EITHER max_dataset_wms
                # OR min_zoom_factor.
                # max_datasets_wms should be set in conjunction with min_zoom_factor so that Terria style 256x256
                # tiled requests respond consistently - you never want to see a mixture of photographic tiles and polygon
                # tiles at a given zoom level.  i.e. max_datasets_wms should be greater than the number of datasets
                # required for most intensive possible photographic query given the min_zoom_factor.
                # Note that the ideal value may vary from product to product depending on the size of the dataset
                # extents for the product.
                # Defaults to zero, which is interpreted as no dataset limit.
                # 6 seems to work with a min_zoom_factor of 500.0 for "old-style" Net-CDF albers tiled data.
                "max_datasets_wms": 6,
                # max_datasets_wcs is the WCS equivalent of max_datasets_wms.  The main requirement for setting this
                # value is to avoid gateway timeouts on overly large WCS requests (and reduce server load).
                "max_datasets_wcs": 16,
                # The fill-colour of the indicative polygons when zoomed out.
                # Triplets (rgb) or quadruplets (rgba) of integers 0-255.
                "zoomed_out_fill_colour": [150, 180, 200, 160],
                # Extent mask function
                # Determines what portions of dataset is potentially meaningful data.
                "extent_mask_func": lambda data, band: (data[band] != data[band].attrs['nodata']),
                # Flags listed here are ignored in GetFeatureInfo requests.
                # (defaults to empty list)
                "ignore_info_flags": [],

                # Styles.
                #
                # See band_mapper.py
                #
                # The various available spectral bands, and ways to combine them
                # into a single rgb image.
                # The examples here are ad hoc
                #
                # LS7:  http://www.indexdatabase.de/db/s-single.php?id=8
                # LS8:  http://www.indexdatabase.de/db/s-single.php?id=168
                "styles": [
                    # Examples of styles which are linear combinations of the available spectral bands.
                    #
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
                        # The raw band value range to be compressed to an 8 bit range for the output image tiles.
                        # Band values outside this range are clipped to 0 or 255 as appropriate.
                        "scale_range": [0.0, 3000.0]
                    },
                    {
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
                        "pq_masks": [
                            {
                                "flags": {
                                    "cloud_acca": "no_cloud",
                                    "cloud_fmask": "no_cloud",
                                },
                            },
                        ],
                        "scale_range": [0.0, 3000.0]
                    },
                    {
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
                        "scale_range": [0.0, 3000.0]
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
                        "scale_range": [0.0, 3000.0]
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
                        "scale_range": [0.0, 3000.0]
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
                        "scale_range": [0.0, 3000.0]
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
                        "scale_range": [0.0, 3000.0]
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
                        "scale_range": [0.0, 3000.0]
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
                        "scale_range": [0.0, 3000.0]
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
                        "scale_range": [0.0, 3000.0]
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
                        "scale_range": [0.0, 3000.0]
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
                        "scale_range": [0.0, 3000.0]
                    },
                    #
                    # Examples of non-linear heat-mapped styles.
                    {
                        "name": "ndvi",
                        "title": "NDVI",
                        "abstract": "Normalised Difference Vegetation Index - a derived index that correlates well with the existence of vegetation",
                        "heat_mapped": True,
                        "index_function": lambda data: (data["nir"] - data["red"]) / (data["nir"] + data["red"]),
                        "needed_bands": ["red", "nir"],
                        # Areas where the index_function returns outside the range are masked.
                        "range": [0.0, 1.0],
                    },
                    {
                        "name": "ndvi_cloudmask",
                        "title": "NDVI with cloud masking",
                        "abstract": "Normalised Difference Vegetation Index (with cloud masking) - a derived index that correlates well with the existence of vegetation",
                        "heat_mapped": True,
                        "index_function": lambda data: (data["nir"] - data["red"]) / (data["nir"] + data["red"]),
                        "needed_bands": ["red", "nir"],
                        # Areas where the index_function returns outside the range are masked.
                        "range": [0.0, 1.0],
                        "pq_masks": [
                            {
                                "flags": {
                                    "cloud_acca": "no_cloud",
                                    "cloud_fmask": "no_cloud",
                                 },
                            },
                        ],
                    },
                    {
                        "name": "ndwi",
                        "title": "NDWI",
                        "abstract": "Normalised Difference Water Index - a derived index that correlates well with the existence of water",
                        "heat_mapped": True,
                        "index_function": lambda data: (data["green"] - data["nir"]) / (data["nir"] + data["green"]),
                        "needed_bands": ["green", "nir"],
                        "range": [0.0, 1.0],
                    },
                    {
                        "name": "ndwi_cloudmask",
                        "title": "NDWI with cloud and cloud-shadow masking",
                        "abstract": "Normalised Difference Water Index (with cloud and cloud-shadow masking) - a derived index that correlates well with the existence of water",
                        "heat_mapped": True,
                        "index_function": lambda data: (data["green"] - data["nir"]) / (data["nir"] + data["green"]),
                        "needed_bands": ["green", "nir"],
                        "range": [0.0, 1.0],
                        "pq_masks": [
                            {
                                "flags": {
                                    "cloud_acca": "no_cloud",
                                    "cloud_fmask": "no_cloud",
                                },
                            },
                        ],
                    },
                    {
                        "name": "ndbi",
                        "title": "NDBI",
                        "abstract": "Normalised Difference Buildup Index - a derived index that correlates with the existence of urbanisation",
                        "heat_mapped": True,
                        "index_function": lambda data: (data["swir2"] - data["nir"]) / (data["swir2"] + data["nir"]),
                        "needed_bands": ["swir2", "nir"],
                        "range": [0.0, 1.0],
                    },
                    # Mask layers - examples of how to display raw pixel quality data.
                    # This works by creatively mis-using the Heatmap style class.
                    {
                        "name": "cloud_mask",
                        "title": "Cloud Mask",
                        "abstract": "Highlight pixels with cloud.",
                        "heat_mapped": True,
                        "index_function": lambda data: data["red"] * 0.0 + 0.1,
                        "needed_bands": ["red"],
                        "range": [0.0, 1.0],
                        # Mask flags normally describe which areas SHOULD be shown.
                        # (i.e. pixels for which any of the declared flags are true)
                        # pq_mask_invert is intended to invert this logic.
                        # (i.e. pixels for which none of the declared flags are true)
                        #
                        # i.e. Specifying like this shows pixels which are not clouds in either metric.
                        #      Specifying "cloud" and setting the "pq_mask_invert" to False would
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
                    },
                    {
                        "name": "cloud_and_shadow_mask",
                        "title": "Cloud and Shadow Mask",
                        "abstract": "Highlight pixels with cloud or cloud shadow.",
                        "heat_mapped": True,
                        "index_function": lambda data: data["red"] * 0.0 + 0.6,
                        "needed_bands": ["red"],
                        "range": [0.0, 1.0],
                        "pq_masks": [
                            {
                                "invert": True,
                                "flags": {
                                    "cloud_acca": "no_cloud",
                                    "cloud_fmask": "no_cloud",
                                    "cloud_shadow_acca": "no_cloud_shadow",
                                    "cloud_shadow_fmask": "no_cloud_shadow",
                                },
                            },
                        ],
                    },
                    {
                        "name": "cloud_acca",
                        "title": "Cloud acca Mask",
                        "abstract": "Highlight pixels with cloud.",
                        "heat_mapped": True,
                        "index_function": lambda data: data["red"] * 0.0 + 0.4,
                        "needed_bands": ["red"],
                        "range": [0.0, 1.0],
                        "pq_masks": [
                            {
                                "flags": {
                                    "cloud_acca": "cloud",
                                },
                            },
                        ],
                    },
                    {
                        "name": "cloud_fmask",
                        "title": "Cloud fmask Mask",
                        "abstract": "Highlight pixels with cloud.",
                        "heat_mapped": True,
                        "index_function": lambda data: data["red"] * 0.0 + 0.8,
                        "needed_bands": ["red"],
                        "range": [0.0, 1.0],
                        "pq_masks": [
                            {
                                "flags": {
                                    "cloud_fmask": "cloud",
                                },
                            },
                        ],
                    },
                    {
                        "name": "contiguous_mask",
                        "title": "Contiguous Data Mask",
                        "abstract": "Highlight pixels with non-contiguous data",
                        "heat_mapped": True,
                        "index_function": lambda data: data["red"] * 0.0 + 0.3,
                        "needed_bands": ["red"],
                        "range": [0.0, 1.0],
                        "pq_masks": [
                            {
                                "flags": {
                                    "contiguous": False
                                },
                            },
                        ],
                    },
                    # Hybrid style - mixes a linear mapping and a heat mapped index
                    {
                        "name": "rgb_ndvi",
                        "title": "NDVI plus RGB",
                        "abstract": "Normalised Difference Vegetation Index (blended with RGB) - a derived index that correlates well with the existence of vegetation",
                        "component_ratio": 0.6,
                        "heat_mapped": True,
                        "index_function": lambda data: (data["nir"] - data["red"]) / (data["nir"] + data["red"]),
                        "needed_bands": ["red", "nir"],
                        # Areas where the index_function returns outside the range are masked.
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
                    },
                    {
                        "name": "rgb_ndvi_cloudmask",
                        "title": "NDVI plus RGB (Cloud masked)",
                        "abstract": "Normalised Difference Vegetation Index (blended with RGB and cloud masked) - a derived index that correlates well with the existence of vegetation",
                        "component_ratio": 0.6,
                        "heat_mapped": True,
                        "index_function": lambda data: (data["nir"] - data["red"]) / (data["nir"] + data["red"]),
                        "needed_bands": ["red", "nir"],
                        # Areas where the index_function returns outside the range are masked.
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
                ],
                # Default style (if request does not specify style)
                # MUST be defined in the styles list above.

                # (Looks like Terria assumes this is the first style in the list, but this is
                #  not required by the standard.)
                "default_style": "simple_rgb",
            },
            {
                # Included as a keyword  for the layer
                "label": "WOfS",
                # Included as a keyword  for the layer
                "type": "Water Observations from Space",
                # Included as a keyword  for the layer
                "variant": "",
                # The WMS name for the layer
                "name": "ls8_wofs",
                # The Datacube name for the associated data product
                "product_name": "ls8_nbart_albers",
                # The Datacube name for the associated pixel-quality product (optional)
                # The name of the associated Datacube pixel-quality product
                "pq_dataset": "LS8_OLI_WATER",
                # The name of the measurement band for the pixel-quality product
                # (Only required if pq_dataset is set)
                "pq_band": "water",
                # Min zoom factor - sets the zoom level where the cutover from indicative polygons
                # to actual imagery occurs.
                "min_zoom_factor": 500.0,
                # Min zoom factor (above) works well for small-tiled requests, (e.g. 256x256 as sent by Terria).
                # However, for large-tiled requests (e.g. as sent by QGIS), large and intensive queries can still
                # go through to the datacube.
                # max_datasets_wms specifies a maximum number of datasets that a GetMap request can retrieve.
                # Indicatative polygons are displayed if a request exceeds the limits imposed by EITHER max_dataset_wms
                # OR min_zoom_factor.
                # max_datasets_wms should be set in conjunction with min_zoom_factor so that Terria style 256x256
                # tiled requests respond consistently - you never want to see a mixture of photographic tiles and polygon
                # tiles at a given zoom level.  i.e. max_datasets_wms should be greater than the number of datasets
                # required for most intensive possible photographic query given the min_zoom_factor.
                # Note that the ideal value may vary from product to product depending on the size of the dataset
                # extents for the product.
                # Defaults to zero, which is interpreted as no dataset limit.
                # 6 seems to work with a min_zoom_factor of 500.0 for "old-style" Net-CDF albers tiled data.
                "max_datasets_wms": 6,
                # max_datasets_wcs is the WCS equivalent of max_datasets_wms.  The main requirement for setting this
                # value is to avoid gateway timeouts on overly large WCS requests (and reduce server load).
                "max_datasets_wcs": 16,
                # The fill-colour of the indicative polygons when zoomed out.
                # Triplets (rgb) or quadruplets (rgba) of integers 0-255.
                "zoomed_out_fill_colour": [200, 180, 180, 160],
                # Extent mask function
                # Determines what portions of dataset is potentially meaningful data.
                "extent_mask_func": lambda data, band: (~data[band] & data[band].attrs['nodata']),
                # When pq_manual_merge is set to true, individual PQ datasets
                # are masked against the extent_mask_func individually before
                # merging into a single DataArray.  Carries a performance
                # hit, so only set to True for datasets that does not have
                # proper extents recorded in their meta-data.
                # (Defaults to false)
                "pq_manual_merge": True,
                # Flags listed here are ignored in GetFeatureInfo requests.
                # (defaults to empty list)
                "ignore_flags_info": [
                    "nodata",
                    "noncontiguous",
                ],

                # Styles.
                #
                # See band_mapper.py
                #
                # The various available spectral bands, and ways to combine them
                # into a single rgb image.
                # The examples here are ad hoc
                #
                # LS7:  http://www.indexdatabase.de/db/s-single.php?id=8
                # LS8:  http://www.indexdatabase.de/db/s-single.php?id=168
                "styles": [
                    {
                        "name": "water_masked",
                        "title": "Water (masked)",
                        "abstract": "Water, with clouds, terrain shadows, etc. masked",
                        "heat_mapped": True,
                        "index_function": lambda data: data["red"] * 0.0 + 0.25,
                        "needed_bands": ["red"],
                        "range": [0.0, 1.0],
                        # Invert True: Show if no flags match (Hide if any match)
                        # (Invert False: Show if any flags match - Hide if none match)

                        "pq_masks": [
                            {
                                "flags": {
                                    'terrain_or_low_angle': False,
                                    'high_slope': False,
                                    'cloud_shadow': False,
                                    'cloud': False,
                                },
                            },
                            {
                                "flags": {
                                    'water': True,
                                },
                            },
                        ]
                    },
                    {
                        "name": "water",
                        "title": "Water (unmasked)",
                        "abstract": "Simple water data, no masking",
                        "heat_mapped": True,
                        "index_function": lambda data: data["red"] * 0.0 + 0.25,
                        "needed_bands": ["red"],
                        "range": [0.0, 1.0],
                        # Invert True: Show if no flags match
                        "pq_masks": [
                            {
                                "flags": {
                                    'water': True,
                                },
                            },
                        ],
                    }
                ],
                # Default style (if request does not specify style)
                # MUST be defined in the styles list above.

                # (Looks like Terria assumes this is the first style in the list, but this is
                #  not required by the standard.)
                "default_style": "water_masked",
            },
        ],
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
        },
        {
            "name": "wideband",
            "title": "Wideband false-colour",
            "abstract": "False-colour image, incorporating all available spectral bands",
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
            "scale_range": [0.0, 3000.0]
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
            "name": "blue",
            "title": "Spectral band 1 - Blue",
            "abstract": "Blue band, approximately 450nm to 520nm",
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
