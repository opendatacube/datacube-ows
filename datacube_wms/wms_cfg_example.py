import re

# Static config for the wms metadata.
# pylint: skip-file

response_cfg = {
    "Access-Control-Allow-Origin": "*",  # CORS header
}


service_cfg = {
    ## Which web service(s) should be supported by this instance
    # Defaults: wms: True, wcs: False, wmts: False
    # Notes:
    #   WMTS support is implemented as a thin proxy to WMS. Some corners of the spec are interpreted
    #   somewhat loosely. In particular exception documents are directly translated from the underlying
    #   WMS error and are unlikely to be fully compliant with the WMTS standard.
    "wcs": True,
    "wms": True,
    "wmts": True,

    ## Required config for WMS and/or WCS
    # Service title - appears e.g. in Terria catalog
    "title": "WMS server for Australian Landsat Datacube",
    # Service URL.  Should a fully qualified URL or a list of fully qualified URLs that the service can return
    # in the GetCapabilities document based on the requesting url
    "url": [ "http://9xjfk12.nexus.csiro.au/datacube_wms", "http://alternateurl.nexus.csiro.au/datacube_wms" ],
    # URL that humans can visit to learn more about the WMS or organization
    # should be fully qualified
    "human_url": "http://csiro.au",

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
            #   * A WCSRequest object
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
    # If True this will not calculate spatial extents
    # in update_ranges.py but will instead use a default
    # extent covering much of Australia for all
    # temporal extents
    # False by default (calculate spatial extents)
    "use_default_extent": True,
    # If using GeoTIFFs as storage
    # this will set the rasterio env
    # GDAL Config for GTiff Georeferencing
    # See https://www.gdal.org/frmt_gtiff.html#georeferencing
    "geotiff_georeference_source": "INTERNAL",
    # Attribution.  This entire section is optional.  If provided, it is taken as the
    #               default attribution for any layer that does not override it.
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
    }
}

layer_cfg = [
    # Layer Config is a list of platform configs
    {
        # Name and title of the platform layer.
        # Platform layers are not mappable. The name is for internal server use only.
        "name": "LANDSAT_8",
        "title": "Landsat 8",
        "abstract": "Images from the Landsat 8 satellite",

        # Attribution.  This entire section is optional.  If provided, it overrides any
        #               attribution defined in the service_cfg for all layers under this
        #               platform that do not define their own attribution.
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
                "bands": {
                    "red": ["crimson"],
                    "green": [],
                    "blue": [ "azure" ],
                    "nir": [ "near_infrared" ],
                    "swir1": [ "shortwave_infrared_1", "near_shortwave_infrared" ],
                    "swir2": [ "shortwave_infrared_2", "far_shortwave_infrared" ],
                    "coastal_aerosol": [ "far_blue" ],
                },
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
                # Multiple extent mask functions are supported - see USGS Level 1 example below.
                #
                # Three formats are supported:
                # 1. A function object or lambda
                #    e.g. "extent_mask_func": lambda data, band: (data[band] != data[band].attrs['nodata']),
                #
                # 2. A string containing a fully qualified path to a python function (e.g. as shown below)
                #
                # 3. A dict containing the following elements:
                #    a) "function" (required): A string containing the fully qualified path to a python function
                #    b) "args" (optional): An array of additional positional arguments that will always be passed to the function.
                #    c) "kwargs" (optional): An array of additional keyword arguments that will always be passed to the function.
                #    d) "pass_product_cfg" (optional): Boolean (defaults to False). If true, the relevant ProductLayerConfig is passed
                #       to the function as a keyword argument named "product_cfg".  This is useful if you are passing band aliases
                #       to the function in the args or kwargs.  The product_cfg allows the index function to convert band aliases to
                #       to band names.
                #
                # The function is assumed to take two arguments, data (an xarray Dataset) and band (a band name).  (Plus any additional
                # arguments required by the args and kwargs values in format 3, possibly including product_cfg.)
                #
                "extent_mask_func": "datacube_wms.ogc_utils.mask_by_val",
                # Fuse func
                # Determines how multiple dataset arrays are compressed into a single time array
                # All the formats described above for "extent_mask_func" are supported here as well.
                "fuse_func": "datacube_wms.wms_utils.wofls_fuser",
                # PQ Fuse func
                # Determines how multiple dataset arrays are compressed into a single time array for the PQ layer
                # All the formats described above for "extent_mask_func" are supported here as well.
                "pq_fuse_func": "datacube.helpers.ga_pq_fuser",
                # PQ Ignore time
                # Doesn't use the time from the data to find a corresponding mask layer
                # Used when you have a mask layer that doesn't have time
                "pq_ignore_time": True,
                # Flags listed here are ignored in GetFeatureInfo requests.
                # (defaults to empty list)
                "ignore_info_flags": [],
                # Include an additional list of utc dates in the WMS Get Feature Info
                # HACK: only used for GSKY non-solar day lookup
                "feature_info_include_utc_dates": True,
                # Set to true if the band product dataset extents include nodata regions.
                "data_manual_merge": False,
                # Set to true if the pq product dataset extents include nodata regions.
                "pq_manual_merge": False,
                # Bands to always fetch from the Datacube, even if it is not used by the active style.
                # Useful for when a particular band is always needed for the extent_mask_func,
                "always_fetch_bands": [ ],
                # Apply corrections for solar angle, for "Level 1" products.
                # (Defaults to false - should not be used for NBAR/NBAR-T or other Analysis Ready products
                "apply_solar_corrections": False,
                # If this value is set then WCS works exclusively with the configured
                # date and advertises no time dimension in GetCapabilities.
                # Intended mostly for WCS debugging.
                "wcs_sole_time": "2017-01-01",
                # The default bands for a WCS request.
                # 1. Must be provided if WCS is activated.
                # 2. Must contain at least one band.
                # 3. All bands must exist
                # 4. Bands may be referred to by either native name or alias
                "wcs_default_bands": [ "red", "green", "azure" ],
                # The "native" CRS for WCS.
                # Can be omitted if the product has a single native CRS, as this will be used in preference.
                "native_wcs_crs": "EPSG:3577",
                # The resolution (x,y) for WCS.
                # This is the number of CRS units (e.g. degrees, metres) per pixel in the horizontal and vertical
                # directions for the native resolution.  E.g. for a EPSG:3577  (25.0,25.0) for Landsat-8 and (10.0,10.0 for Sentinel-2)
                "native_wcs_resolution": [ 25.0, 25.0 ],
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
                            # The component keys MUST be "red", "green" and "blue" (and optionally "alpha")
                            "red": {
                                # Band aliases may be used here.
                                "crimson": 1.0
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
                        # All pixels where any of the listed flags are true are masked out.
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
                    # Examples of non-linear colour-ramped styles.
                    {
                        "name": "ndvi",
                        "title": "NDVI",
                        "abstract": "Normalised Difference Vegetation Index - a derived index that correlates well with the existence of vegetation",
                        # The index function is continuous value from which the heat map is derived.
                        #
                        # Three formats are supported:
                        # 1. A function object or lambda
                        #    e.g. "index_function": lambda data: (data["nir"] - data["red"]) / (data["nir"] + data["red"]),
                        #    Note that lambdas CANNOT use band aliases - they MUST use the native band name
                        #
                        # 2. A string containing a fully qualified path to a python function
                        #    e.g. "index_function": "datacube_wms.ogc_utils.not_a_real_function_name",
                        #
                        # 3. A dict containing the following elements:
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
                            "function": "datacube_wms.band_utils.norm_diff",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band1": "nir",
                                "band2": "red"
                            }
                        },
                        # Band aliases can be used here.
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
                                # if no alpha is specified, alpha will default to 1.0
                                # or max opacity
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
                        ]
                    },
                    {
                        "name": "ndvi_cloudmask",
                        "title": "NDVI with cloud masking",
                        "abstract": "Normalised Difference Vegetation Index (with cloud masking) - a derived index that correlates well with the existence of vegetation",
                        "index_function": {
                            "function": "datacube_wms.band_utils.norm_diff",
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
                        "index_function": {
                            "function": "datacube_wms.band_utils.norm_diff",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band1": "green",
                                "band2": "nir"
                            }
                        },
                        "needed_bands": ["green", "nir"],
                        "range": [0.0, 1.0],
                    },
                    {
                        "name": "ndwi_cloudmask",
                        "title": "NDWI with cloud and cloud-shadow masking",
                        "abstract": "Normalised Difference Water Index (with cloud and cloud-shadow masking) - a derived index that correlates well with the existence of water",
                        "index_function": {
                            "function": "datacube_wms.band_utils.norm_diff",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band1": "green",
                                "band2": "nir"
                            }
                        },
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
                        "index_function": {
                            "function": "datacube_wms.band_utils.norm_diff",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band1": "swir2",
                                "band2": "nir"
                            }
                        },
                        "needed_bands": ["swir2", "nir"],
                        "range": [0.0, 1.0],
                    },
                    # Mask layers - examples of how to display raw pixel quality data.
                    # This works by creatively mis-using the colormap styles.
                    # The index function returns a constant, so the output is a flat single colour, masked by the
                    # relevant pixel quality flags.
                    {
                        "name": "cloud_mask",
                        "title": "Cloud Mask",
                        "abstract": "Highlight pixels with cloud.",
                        "index_function": {
                            "function": "datacube_wms.band_utils.constant",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band": "red",
                                "const": "0.1"
                            }
                        },
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
                        "index_function": {
                            "function": "datacube_wms.band_utils.constant",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band": "red",
                                "const": "0.6"
                            }
                        },
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
                        "index_function": {
                            "function": "datacube_wms.band_utils.constant",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band": "red",
                                "const": "0.4"
                            }
                        },
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
                        "index_function": {
                            "function": "datacube_wms.band_utils.constant",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band": "red",
                                "const": "0.8"
                            }
                        },
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
                        "index_function": {
                            "function": "datacube_wms.band_utils.constant",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band": "red",
                                "const": "0.3"
                            }
                        },
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
                    # Hybrid style - blends a linear mapping and an colour-ramped index style
                    # There is no scientific justification for these styles, I just think they look cool.  :)
                    {
                        "name": "rgb_ndvi",
                        "title": "NDVI plus RGB",
                        "abstract": "Normalised Difference Vegetation Index (blended with RGB) - a derived index that correlates well with the existence of vegetation",
                        # Mixing ration between linear components and colour ramped index. 1.0 is fully linear components, 0.0 is fully colour ramp.
                        "component_ratio": 0.6,
                        "index_function": {
                            "function": "datacube_wms.band_utils.norm_diff",
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
                        "scale_range": [0.0, 3000.0]
                    },
                    {
                        "name": "rgb_ndvi_cloudmask",
                        "title": "NDVI plus RGB (Cloud masked)",
                        "abstract": "Normalised Difference Vegetation Index (blended with RGB and cloud masked) - a derived index that correlates well with the existence of vegetation",
                        "component_ratio": 0.6,
                        "index_function": {
                            "function": "datacube_wms.band_utils.norm_diff",
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
                ],
                # Default style (if request does not specify style)
                # MUST be defined in the styles list above.

                # (Looks like Terria assumes this is the first style in the list, but this is
                #  not required by the standard.)
                "default_style": "simple_rgb",

                # Attribution.  This entire section is optional.  If not provided, the default attribution
                #               from the parent platform or the service config is used.
                #               If no attribution is defined at any level, no attribution will be published.
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
                }
            },
            {
                # Example for USGS Level 1 Cloud-Optimised GeoTiffs in the AWS PDS.
                "label": "USGS Level 1",
                "type": "surface radiance",
                "variant": "PDS",
                # The WMS name for the layer
                "name": "ls8_level1_usgs",
                # The Datacube name for the associated data product
                "product_name": "ls8_level1_usgs",
                # Pixel quality is stored in the same datacube product as the band data
                "pq_dataset": "ls8_level1_usgs",
                # The name of the measurement band for the pixel-quality product
                "pq_band": "quality",
                # Min zoom factor - sets the zoom level where the cutover from indicative polygons
                # to actual imagery occurs.
                "min_zoom_factor": 500.0,
                # The fill-colour of the indicative polygons when zoomed out.
                # Triplets (rgb) or quadruplets (rgba) of integers 0-255.
                "zoomed_out_fill_colour": [150, 180, 200, 160],
                # Extent mask functions
                # Determines what portions of dataset is potentially meaningful data.
                # Multiple extent mask functions are required for this data.
                "extent_mask_func": [
                    "datacube_wms.ogc_utils.mask_by_quality",
                    "datacube_wms.ogc_utils.mask_by_val",
                ],
                # Flags listed here are ignored in GetFeatureInfo requests.
                # (defaults to empty list)
                "ignore_info_flags": [],
                # Include legends for listed styles.  Note that only style types that support
                # legends should be included (i.e. colour ramped styles.)
                "legend": {
                    # the styles to include in a legend for this product
                    "styles": ["ndvi", "ndwi", "ndbi"]
                },

                # Set to true if the band product dataset extents include nodata regions.
                "data_manual_merge": True,
                # Set to true if the pq product dataset extents include nodata regions.
                "pq_manual_merge": True,
                # Bands to always fetch from the Datacube, even if it is not used by the active style.
                # Useful for when a particular band is always needed for the extent_mask_func,
                "always_fetch_bands": [ "quality", ],
                # Apply corrections for solar angle, for "Level 1" products.
                "apply_solar_corrections": True,

                # A function that extracts the "sub-product" id (e.g. path number) from a dataset. Function should return a (small) integer
                # If None or not specified, the product has no sub-layers.
                # All the formats supported for extent_mask_func as described above are supported here as well.
                # The function is assumed to take a datacube dataset object and return a sub-product id.
                "sub_product_extractor": "datacube_wms.ogc_utils.ls8_subproduct",
                # A prefix used to describe the sub-layer in the GetCapabilities response.
                # E.g. sub-layer 109 will be described as "Landsat Path 109"
                "sub_product_label": "Landsat Path",

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
                        "scale_range": [ 9500, 22000 ],
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
                                    "cloud": False,
                                },
                            },
                        ],
                        "scale_range": [ 9500, 22000 ],
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
                        "scale_range": [ 9500, 22000 ],
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
                        "scale_range": [ 9500, 22000 ],
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
                        "scale_range": [ 9500, 22000 ],
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
                        "scale_range": [ 9500, 22000 ],
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
                        "scale_range": [ 9500, 22000 ],
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
                        "scale_range": [ 9500, 22000 ],
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
                        "scale_range": [ 9500, 22000 ],
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
                        "scale_range": [ 9500, 22000 ],
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
                        "scale_range": [ 9500, 22000 ],
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
                        "scale_range": [ 9500, 22000 ],
                    },
                    #
                    # Examples of non-linear heat-mapped styles.
                    {
                        "name": "ndvi",
                        "title": "NDVI",
                        "abstract": "Normalised Difference Vegetation Index - a derived index that correlates well with the existence of vegetation",
                        "index_function": {
                            "function": "datacube_wms.band_utils.norm_diff",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band1": "nir",
                                "band2": "red"
                            }
                        },
                        "needed_bands": ["red", "nir"],
                        # Areas where the index_function returns outside the range are masked.
                        "range": [0.0, 1.0],
                    },
                    {
                        "name": "ndvi_cloudmask",
                        "title": "NDVI with cloud masking",
                        "abstract": "Normalised Difference Vegetation Index (with cloud masking) - a derived index that correlates well with the existence of vegetation",
                        "index_function": {
                            "function": "datacube_wms.band_utils.norm_diff",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band1": "nir",
                                "band2": "red"
                            }
                        },
                        "needed_bands": ["red", "nir"],
                        # Areas where the index_function returns outside the range are masked.
                        "range": [0.0, 1.0],
                        "pq_masks": [
                            {
                                "flags": {
                                    "cloud": False,
                                 },
                            },
                        ],
                    },
                    {
                        "name": "ndwi",
                        "title": "NDWI",
                        "abstract": "Normalised Difference Water Index - a derived index that correlates well with the existence of water",
                        "index_function": {
                            "function": "datacube_wms.band_utils.norm_diff",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band1": "green",
                                "band2": "nir"
                            }
                        },
                        "needed_bands": ["green", "nir"],
                        "range": [0.0, 1.0],
                    },
                    {
                        "name": "ndwi_cloudmask",
                        "title": "NDWI with cloud and cloud-shadow masking",
                        "abstract": "Normalised Difference Water Index (with cloud and cloud-shadow masking) - a derived index that correlates well with the existence of water",
                        "index_function": {
                            "function": "datacube_wms.band_utils.norm_diff",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band1": "green",
                                "band2": "nir"
                            }
                        },
                        "needed_bands": ["green", "nir"],
                        "range": [0.0, 1.0],
                        "pq_masks": [
                            {
                                "flags": {
                                    "cloud": False,
                                },
                            },
                        ],
                    },
                    {
                        "name": "ndbi",
                        "title": "NDBI",
                        "abstract": "Normalised Difference Buildup Index - a derived index that correlates with the existence of urbanisation",
                        "index_function": {
                            "function": "datacube_wms.band_utils.norm_diff",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band1": "swir2",
                                "band2": "nir"
                            }
                        },
                        "needed_bands": ["swir2", "nir"],
                        "range": [0.0, 1.0],
                    },
                    # Mask layers - examples of how to display raw pixel quality data.
                    # This works by creatively mis-using the Heatmap style class.
                    {
                        "name": "cloud_mask",
                        "title": "Cloud Mask",
                        "abstract": "Highlight pixels with cloud.",
                        "index_function": {
                            "function": "datacube_wms.band_utils.constant",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band": "red",
                                "const": "0.1"
                            }
                        },
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
                                    "cloud": False,
                                },
                            },
                        ],
                    },
                    # Hybrid style - blends a linear mapping and an colour-ramped index style
                    # There is no scientific justification for these styles, I just think they look cool.  :)
                    {
                        "name": "rgb_ndvi",
                        "title": "NDVI plus RGB",
                        "abstract": "Normalised Difference Vegetation Index (blended with RGB) - a derived index that correlates well with the existence of vegetation",
                        "component_ratio": 0.6,
                        "index_function": {
                            "function": "datacube_wms.band_utils.norm_diff",
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
                        "scale_range": [ 9500, 22000 ],
                    },
                    {
                        "name": "rgb_ndvi_cloudmask",
                        "title": "NDVI plus RGB (Cloud masked)",
                        "abstract": "Normalised Difference Vegetation Index (blended with RGB and cloud masked) - a derived index that correlates well with the existence of vegetation",
                        "component_ratio": 0.6,
                        "index_function": {
                            "function": "datacube_wms.band_utils.norm_diff",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band1": "nir",
                                "band2": "red"
                            }
                        },
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
                                    "cloud": False,
                                },
                            },
                        ],
                        "scale_range": [ 9500, 22000 ],
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
                "extent_mask_func": "datacube_wms.ogc_utils.mask_by_bitflag",
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
                        "index_function": {
                            "function": "datacube_wms.band_utils.constant",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band": "red",
                                "const": "0.25"
                            }
                        },
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
                        "index_function": {
                            "function": "datacube_wms.band_utils.constant",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band": "red",
                                "const": "0.25"
                            }
                        },
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
            {
                # Included as a keyword  for the layer
                "label": "WOfS_Summary",
                # Included as a keyword  for the layer
                "type": "WOfS_Summary",
                # Included as a keyword  for the layer
                "variant": "Summary",
                # The WMS name for the layer
                "name": "wofs_summary",
                # The Datacube name for the associated data product
                "product_name": "wofs_summary",
                "abstract": "test",
                # The Datacube name for the associated pixel-quality product (optional)
                # The name of the associated Datacube pixel-quality product
                #"pq_dataset": "wofs_albers",
                # The name of the measurement band for the pixel-quality product
                # (Only required if pq_dataset is set)
                #"pq_band": "water",
                # Min zoom factor - sets the zoom level where the cutover from indicative polygons
                # to actual imagery occurs.
                "min_zoom_factor": 5.0,
                # The fill-colour of the indicative polygons when zoomed out.
                # Triplets (rgb) or quadruplets (rgba) of integers 0-255.
                "zoomed_out_fill_colour": [150, 180, 200, 160],
                # Extent mask function
                # Determines what portions of dataset is potentially meaningful data.
                "extent_mask_func": "datacube_wms.ogc_utils.mask_by_val",
                # Flags listed here are ignored in GetFeatureInfo requests.
                # (defaults to empty list)
                "ignore_info_flags": [],
                "legend": {
                    # "url": ""
                    # the styles to include in a legend for this product
                    "styles": ["WOfS_frequency"] 
                },
                "styles": [
                    {
                        "name": "WOfS_frequency",
                        "title": " Wet and Dry Count",
                        "abstract": "WOfS summary showing the frequency of Wetness",
                        "needed_bands": ["frequency"],
                        "index_function": {
                            "function": "datacube_wms.band_utils.single_band",
                            "pass_product_cfg": True,
                            "kwargs": {
                                "band": "frequency",
                            }
                        },
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
                                # If defined this label
                                # will include a prefix and suffix
                                # string as shown
                                # if label is defined, the scaled valued
                                # will be replaced by that string
                                "legend": {
                                    "prefix": ">",
                                    #"label": "foo"
                                    "suffix": "<"
                                }
                            }
                        ],
                        # defines the format of the legend generated
                        # for this style
                        "legend": {
                            # appended to the title of the legend
                            # if missing will use 'unitless'
                            "units": "%",
                            # radix places to round tick labels to
                            # set to 0 for ints
                            "radix_point": 0,
                            # values will be scaled by this amount
                            # to generate tick labels
                            # e.g. for a percentage stored as 0 - 1.0
                            # this should be 100
                            "scale_by": 100.0,
                            # tick labels will be created for values that
                            # are modulo 0 by this value
                            "major_ticks": 0.1
                        }
                    },
                ],
                # Default style (if request does not specify style)
                # MUST be defined in the styles list above.

                # (Looks like Terria assumes this is the first style in the list, but this is
                #  not required by the standard.)
                "default_style": "WOfS_frequency",
            },
        ],
    },
    {
        "name": "sentinel2",
        "title": "Sentinel-2",
        "abstract": "Near Real-Time images from Sentinel-2 satellites",
        "products": [
            # Multi-product example.
            #
            # Combines Sentinel 2A and 2B products into a single OWS layer.
            # Assumes that member products do not overlap in space-time and have identical bands.
            # (i.e. pretty specialised for the Sentinel-2 use case.  Could in theory be used for something
            # like Landsat 7 and 8, but only if the Landsat-8-only coastal_aerosol band is excluded.)
            #
            # The following functionality is not yet supported for multi-products: path-number sub-layers.
            {
                "label": "sentinel-2 (a and b) nrt (s3)",
                "type": "surface reflectance",
                "variant": "near real time",
                "name": "sentinel2_nrt",
                # Multi_product defaults to False
                "multi_product": True,
                # If multi_product is true, then supply a list of product names for product_name
                #
                # N.B. This example does not use a separate PQ product. For multi-products that do
                # require a separate PQ product, the "pq_dataset" field should also be a list of datasets,
                # of the same length as the product_name list, with each PQ dataset in the position
                # corresponding to the related product_name.  Other PQ related config items remain
                # as described above, and are assumed to be the same for all listed PQ datasets.
                "product_name": ["s2a_nrt_granule", "s2b_nrt_granule"],
                "bands": {
                    "nbar_coastal_aerosol": [],
                    "nbar_blue": [],
                    "nbar_green": [],
                    "nbar_red": [],
                    "nbar_red_edge_1": [],
                    "nbar_red_edge_2": [],
                    "nbar_red_edge_3": [],
                    "nbar_nir_1":  [ "nbar_near_infrared_1" ],
                    "nbar_nir_2":  [ "nbar_near_infrared_2" ],
                    "nbar_swir_2": [ "nbar_shortwave_infrared_2" ],
                    "nbar_swir_3": [ "nbar_shortwave_infrared_3" ],
                    "nbart_coastal_aerosol": [],
                    "nbart_blue": [],
                    "nbart_green": [],
                    "nbart_red": [],
                    "nbart_red_edge_1": [],
                    "nbart_red_edge_2": [],
                    "nbart_red_edge_3": [],
                    "nbart_nir_1":  [ "nbart_near_infrared_1" ],
                    "nbart_nir_2":  [ "nbart_near_infrared_2" ],
                    "nbart_swir_2": [ "nbart_shortwave_infrared_2" ],
                    "nbart_swir_3": [ "nbart_shortwave_infrared_3" ],
                },
                "min_zoom_factor": 15.0,
                "max_datasets_wms": 12,
                "max_datasets_wcs": 32,
                "native_wcs_crs": "epsg:3577",
                "native_wcs_resolution": [ 10.0, 10.0 ],
                "zoomed_out_fill_colour": [200, 180, 150, 160],
                "time_zone": 9,
                "extent_mask_func": "datacube_wms.ogc_utils.mask_by_val",
                "ignore_info_flags": [],
                "data_manual_merge": False,
                "pq_manual_merge": False,
                "always_fetch_bands": [],
                "apply_solar_corrections": False,
                "wcs_default_bands": [ "nbart_red", "nbart_green", "nbart_blue" ],
                "legend": {
                    "styles": [],
                },
                "styles": [
                    {
                        "name": "nbar_rgb",
                        "title": "nbar rgb",
                        "abstract": "true-colour image, using the red, green and blue bands without terrain correction",
                        "components": {
                            "red": {
                                "nbar_red": 1.0
                            },
                            "green": {
                                "nbar_green": 1.0
                            },
                            "blue": {
                                "nbar_blue": 1.0
                            }
                        },
                        "scale_range": [100.0, 3200.0]
                    },
                ],
                "default_style": "nbar_rgb",
            },
        ],
    },
    {
        "name": "mangrove_cover",
        "title": "Mangrove Canopy Cover",
        "abstract": "",
        "products": [
            {
                "label": "Mangrove Canopy Cover",
                "abstract": "test",
                "type": "100km tile",
                "variant": "25m",
                "name": "mangrove_cover",
                "product_name": "mangrove_cover",
                "min_zoom_factor": 15.0,
                "zoomed_out_fill_colour": [150, 180, 200, 160],
                "extent_mask_func": "datacube_wms.ogc_utils.mask_by_extent_flag",
                "ignore_info_flags": [],
                "data_manual_merge": False,
                "always_fetch_bands": ["extent"],
                "apply_solar_corrections": False,
                "legend": {
                    "styles": ["mangrove"]
                },
                "styles": [
                    # Describes a style which uses bitflags
                    # to create a style
                    {
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
                    }
                ],
                # Default style (if request does not specify style)
                # MUST be defined in the styles list above.
                # (Looks like Terria assumes this is the first style in the list, but this is
                #  not required by the standard.)
                "default_style": "mangrove",
            },
        ]
    },
]


