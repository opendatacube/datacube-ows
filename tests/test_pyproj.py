import osr

SUPPORTED_CRS = [
   'EPSG:3857', # Web Mercator
   'EPSG:4326', # WGS-84
   'EPSG:3577', # GDA-94
   'EPSG:3111', # VicGrid94
   'EPSG:32648', # WGS 84 / Cambodiacube
   'ESRI:102022', # Africa
   # 'EPSG:102022', # Depreciated Africa
   'EPSG:6933', # Africa
]

def test_gdal_crs():
   for crs_string in SUPPORTED_CRS:
      srs = osr.SpatialReference()
      assert (srs.SetFromUserInput(crs_string) == 0), "{} is not supported".format(crs_string)
