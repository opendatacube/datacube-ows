import datetime
from collections import OrderedDict

import datacube
import numpy
import xarray
from affine import Affine

from datacube.utils import geometry
from rasterio import MemoryFile

from datacube_wms.cube_pool import get_cube, release_cube
from datacube_wms.data import DataStacker
from datacube_wms.ogc_exceptions import WCS1Exception
from datacube_wms.wms_layers import get_layers, get_service_cfg

class WCS1GetCoverageRequest(object):
    def __init__(self, args):
        self.args = args
        layers = get_layers()
        svc_cfg = get_service_cfg()

        # Argument: Coverage (required)
        if "coverage" not in args:
            raise WCS1Exception("No coverage specified",
                                WCS1Exception.MISSING_PARAMETER_VALUE,
                                locator="COVERAGE parameter")
        self.product_name = args["coverage"]
        self.product = layers.product_index.get(self.product_name)
        if not self.product:
            raise WCS1Exception("Invalid coverage: %s" % self.product_name,
                                WCS1Exception.COVERAGE_NOT_DEFINED,
                                locator="COVERAGE parameter")

        # Argument: (request) CRS (required)
        if "crs" not in args:
            raise WCS1Exception("No request CRS specified",
                                WCS1Exception.MISSING_PARAMETER_VALUE,
                                locator="CRS parameter")
        self.request_crsid = args["crs"]
        if self.request_crsid not in svc_cfg.published_CRSs:
            raise WCS1Exception("%s is not a supported CRS" % self.request_crsid,
                                WCS1Exception.INVALID_PARAMETER_VALUE,
                                locator="CRS parameter")
        self.request_crs = geometry.CRS(self.request_crsid)

        # Argument: response_crs (optional)
        if "response_crs" in args:
            self.response_crsid = args["response_crs"]
            if self.response_crsid not in svc_cfg.published_CRSs:
                raise WCS1Exception("%s is not a supported CRS" % self.request_crsid,
                                    WCS1Exception.INVALID_PARAMETER_VALUE,
                                    locator="RESPONSE_CRS parameter")
            self.response_crs = geometry.CRS(self.response_crsid)
        else:
            self.response_crsid = self.request_crsid
            self.response_crs = self.request_crs

        # Arguments: One of BBOX or TIME is required
        #if "bbox" not in args and "time" not in args:
        #    raise WCS1Exception("At least one of BBOX or TIME parameters must be supplied",
        #                        WCS1Exception.MISSING_PARAMETER_VALUE,
        #                        locator="BBOX or TIME parameter"
        #                        )

        # Argument: BBOX (technically not required if TIME supplied, but
        #       it's not clear to me what that would mean.)
        if "bbox" not in args:
            raise WCS1Exception("No BBOX parameter supplied",
                                WCS1Exception.MISSING_PARAMETER_VALUE,
                                locator="BBOX or TIME parameter")
        try:
            if svc_cfg.published_CRSs[self.request_crsid]["vertical_coord_first"]:
                self.miny, self.minx, self.maxy, self.maxx = map(float, args['bbox'].split(','))
            else:
                self.minx, self.miny, self.maxx, self.maxy = map(float, args['bbox'].split(','))
        except:
            raise WCS1Exception("Invalid BBOX parameter",
                                WCS1Exception.INVALID_PARAMETER_VALUE,
                                locator="BBOX parameter")

        # Argument: TIME (not 100% sure whether strictly required, but
        #           not clear what it means if missing)
        if "time" not in args:
            raise WCS1Exception("No TIME parameter supplied",
                                WCS1Exception.MISSING_PARAMETER_VALUE,
                                locator="TIME parameter")
        # TODO: the min/max/res format option?
        # It's a bit underspeced. I'm not sure what the "res" would look like.
        times = args["time"].split(",")
        self.times = []
        if times == "now":
            pass
        else:
            for t in times:
                try:
                    time = datetime.datetime.strptime(t, "%Y-%m-%d").date()
                    if time not in self.product.ranges["time_set"]:
                        raise WCS1Exception(
                            "Time value '%s' not a valid date for coverage %s" % (t,self.product_name),
                            WCS1Exception.INVALID_PARAMETER_VALUE,
                            locator="TIME parameter"
                        )
                    self.times.append(time)
                except ValueError:
                    raise WCS1Exception(
                        "Time value '%s' not a valid ISO-8601 date" % t,
                        WCS1Exception.INVALID_PARAMETER_VALUE,
                        locator="TIME parameter"
                    )
            self.times.sort()

        # Range constraint parameter: MEASUREMENTS
        # No default is set in the DescribeCoverage, so it is required
        if "measurements" not in args:
            raise WCS1Exception("No measurements specified",
                                WCS1Exception.MISSING_PARAMETER_VALUE,
                                locator="MEASUREMENTS parameter")
        bands = args["measurements"]
        self.bands = []
        for b in bands.split(","):
            if b not in self.product.bands:
                raise WCS1Exception("Invalid measurement '%s'" % b,
                                    WCS1Exception.INVALID_PARAMETER_VALUE,
                                    locator="MEASUREMENTS parameter")
            self.bands.append(b)
        if not bands:
            raise WCS1Exception("No measurements supplied",
                                WCS1Exception.INVALID_PARAMETER_VALUE,
                                locator="MEASUREMENTS parameter")

        # Argument: FORMAT (required)
        if "format" not in args:
            raise WCS1Exception("No FORMAT parameter supplied",
                                WCS1Exception.MISSING_PARAMETER_VALUE,
                                locator="FORMAT parameter")
        if args["format"] != "GeoTIFF":
            raise WCS1Exception("Unsupported format: " % args["format"],
                                WCS1Exception.INVALID_PARAMETER_VALUE,
                                locator="FORMAT parameter")
        self.format = args["format"]

        # Argument: EXCEPTIONS (optional - defaults to XML)
        if "exceptions" in args and args["exceptions"] != "application/vnd.ogc.se_xml":
            raise WCS1Exception("Unsupported exception format: " % args["exceptions"],
                                WCS1Exception.INVALID_PARAMETER_VALUE,
                                locator="EXCEPTIONS parameter")

        # Argument: INTERPOLATION (optional only nearest-neighbour currently supported.)
        #      If 'none' is supported in future, validation of width/height/res will need to change.
        if "interpolation" in args and args["interpolation"] != "nearest neighbor":
            raise WCS1Exception("Unsupported interpolation method: " % args["interpolation"],
                                WCS1Exception.INVALID_PARAMETER_VALUE,
                                locator="INTERPOLATION parameter")

        if "width" in args:
            if "height" not in args:
                raise WCS1Exception("WIDTH parameter supplied without HEIGHT parameter",
                                    WCS1Exception.MISSING_PARAMETER_VALUE,
                                    locator="WIDTH/HEIGHT parameters")
            if "resx" in args or "resy" in args:
                raise WCS1Exception("Specify WIDTH/HEIGHT parameters OR RESX/RESY parameters - not both",
                                    WCS1Exception.MISSING_PARAMETER_VALUE,
                                    locator="RESX/RESY/WIDTH/HEIGHT parameters")
            try:
                self.height=int(args["height"])
                if self.height < 1:
                    raise ValueError()
            except ValueError:
                raise WCS1Exception("HEIGHT parameter must be a positive integer",
                                    WCS1Exception.INVALID_PARAMETER_VALUE,
                                    locator="HEIGHT parameter")
            try:
                self.width=int(args["width"])
                if self.width < 1:
                    raise ValueError()
            except ValueError:
                raise WCS1Exception("WIDTH parameter must be a positive integer",
                                    WCS1Exception.INVALID_PARAMETER_VALUE,
                                    locator="WIDTH parameter")
            self.resx = ( self.maxx - self.minx) / self.width
            self.resy = ( self.maxy - self.miny) / self.height
        elif "resx" in args:
            if "resy" not in args:
                raise WCS1Exception("RESX parameter supplied without RESY parameter",
                                    WCS1Exception.MISSING_PARAMETER_VALUE,
                                    locator="RESX/RESY parameters")
            if "height" in args:
                raise WCS1Exception("Specify WIDTH/HEIGHT parameters OR RESX/RESY parameters - not both",
                                    WCS1Exception.MISSING_PARAMETER_VALUE,
                                    locator="RESX/RESY/WIDTH/HEIGHT parameters")
            try:
                self.resx = float(args["resx"])
                if self.resx <= 0.0:
                    raise ValueError(0)
            except ValueError:
                raise WCS1Exception("RESX parameter must be a positive number",
                                    WCS1Exception.INVALID_PARAMETER_VALUE,
                                    locator="RESX parameter")
            try:
                self.resy = float(args["resy"])
                if self.resy <= 0.0:
                    raise ValueError(0)
            except ValueError:
                raise WCS1Exception("RESY parameter must be a positive number",
                                    WCS1Exception.INVALID_PARAMETER_VALUE,
                                    locator="RESY parameter")
            self.width = ( self.maxx - self.minx) / self.resx
            self.height = ( self.maxy - self.miny) / self.resy
            self.width = int(self.width + 0.5)
            self.height = int(self.height + 0.5)
        elif "height" in args:
            raise WCS1Exception("HEIGHT parameter supplied without WIDTH parameter",
                                WCS1Exception.MISSING_PARAMETER_VALUE,
                                locator="WIDTH/HEIGHT parameters")
        elif "resy" in args:
            raise WCS1Exception("RESY parameter supplied without RESX parameter",
                                WCS1Exception.MISSING_PARAMETER_VALUE,
                                locator="RESX/RESY parameters")
        else:
            raise WCS1Exception("You must specify either the WIDTH/HEIGHT parameters or RESX/RESY",
                                WCS1Exception.MISSING_PARAMETER_VALUE,
                                locator="RESX/RESY/WIDTH/HEIGHT parameters")

        self.extent = geometry.polygon([(self.minx, self.miny),
                                 (self.minx, self.maxy),
                                 (self.maxx, self.maxy),
                                 (self.maxx, self.miny),
                                 (self.minx, self.miny)],
                                self.request_crs)

        self.affine = Affine.translation(self.minx, self.maxy) * Affine.scale((self.maxx-self.minx)/self.width, (self.maxy-self.miny)/self.height)
        self.geobox = geometry.GeoBox(self.width, self.height, self.affine, self.request_crs)


def get_coverage_data(req):
    dc = get_cube()
    datasets = []
    for t in req.times:
        # IF t was passed to the datasets method instead of the stacker
        # constructor, we could use the one stacker.
        stacker = DataStacker(req.product,
                              req.geobox,
                              t,
                              bands=req.bands)
        t_datasets = stacker.datasets(dc.index)
        if not t_datasets:
            # No matching data for this date
            continue
        datasets.extend(t_datasets)
    if not datasets:
        # Ideally return an empty coverage file with full metadata.
        raise WCS1Exception("Selected parameters return no coverage data", WCS1Exception.INVALID_PARAMETER_VALUE)
    stacker = DataStacker(req.product,
                          req.geobox,
                          t,
                          bands=req.bands)
    return stacker.data(datasets, manual_merge=req.product.data_manual_merge)


def get_tiff(prod, data, response_crs):
    """Uses rasterio MemoryFiles in order to return a streamable GeoTiff response"""
    # Copied from CEOS.  Does not seem to support multi-time dimension data - is this even possible in GeoTiff?
    supported_dtype_map = {
        'uint8': 1,
        'uint16': 2,
        'int16': 3,
        'uint32': 4,
        'int32': 5,
        'float32': 6,
        'float64': 7,
        'complex': 9,
        'complex64': 10,
        'complex128': 11,
    }

    dtype_list = [data[array].dtype for array in data.data_vars]
    dtype = str(max(dtype_list, key=lambda d: supported_dtype_map[str(d)]))

    data = data.astype(dtype)
    with MemoryFile() as memfile:
        with memfile.open(
                driver="GTiff",
                width=data.dims['longitude'],
                height=data.dims['latitude'],
                count=len(data.data_vars),
                transform=_get_transform_from_xr(data),
                crs=response_crs,
                dtype=dtype) as dst:
            for idx, band in enumerate(data.data_vars, start=1):
                dst.write(data[band].values, idx)
            dst.set_nodatavals(
                [ prod.nodata_dict[band] if band in prod.nodata_dict else 0 for band in data.data_vars ]
            )
        return memfile.read()


def _get_transform_from_xr(dataset):
    """Create a geotransform from an xarray dataset."""
    # Copied from CEOS.
    # Looks like the rasterio equivalent of a Geobox.
    # Not sure if this code will work with a non-geographic CRS??
    from rasterio.transform import from_bounds
    geotransform = from_bounds(dataset.longitude[0], dataset.latitude[-1], dataset.longitude[-1], dataset.latitude[0],
                               len(dataset.longitude), len(dataset.latitude))

    return geotransform


