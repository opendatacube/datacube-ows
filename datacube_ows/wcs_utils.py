from __future__ import absolute_import, division, print_function

from dateutil.parser import parse

import numpy
import xarray
from affine import Affine

from datacube.utils import geometry
from rasterio import MemoryFile

from datacube_ows.cube_pool import get_cube, release_cube
from datacube_ows.data import DataStacker
from datacube_ows.ogc_exceptions import WCS1Exception
from datacube_ows.ogc_utils import ProductLayerException
from datacube_ows.ows_configuration import get_config
from datacube_ows.utils import opencensus_trace_call, get_opencensus_tracer

tracer = get_opencensus_tracer()

class WCS1GetCoverageRequest():
    #pylint: disable=too-many-instance-attributes, too-many-branches, too-many-statements, too-many-locals
    @opencensus_trace_call(tracer=tracer)
    def __init__(self, args):
        self.args = args
        cfg = get_config()

        # Argument: Coverage (required)
        if "coverage" not in args:
            raise WCS1Exception("No coverage specified",
                                WCS1Exception.MISSING_PARAMETER_VALUE,
                                locator="COVERAGE parameter")
        self.product_name = args["coverage"]
        self.product = cfg.product_index.get(self.product_name)
        if not self.product or not self.product.wcs:
            raise WCS1Exception("Invalid coverage: %s" % self.product_name,
                                WCS1Exception.COVERAGE_NOT_DEFINED,
                                locator="COVERAGE parameter")

        # Argument: FORMAT (required)
        if "format" not in args:
            raise WCS1Exception("No FORMAT parameter supplied",
                                WCS1Exception.MISSING_PARAMETER_VALUE,
                                locator="FORMAT parameter")
        if args["format"] not in cfg.wcs_formats:
            raise WCS1Exception("Unsupported format: %s" % args["format"],
                                WCS1Exception.INVALID_PARAMETER_VALUE,
                                locator="FORMAT parameter")
        self.format = cfg.wcs_formats[args["format"]]

        # Argument: (request) CRS (required)
        if "crs" not in args:
            raise WCS1Exception("No request CRS specified",
                                WCS1Exception.MISSING_PARAMETER_VALUE,
                                locator="CRS parameter")
        self.request_crsid = args["crs"]
        if self.request_crsid not in cfg.published_CRSs:
            raise WCS1Exception("%s is not a supported CRS" % self.request_crsid,
                                WCS1Exception.INVALID_PARAMETER_VALUE,
                                locator="CRS parameter")
        self.request_crs = geometry.CRS(self.request_crsid)

        # Argument: response_crs (optional)
        if "response_crs" in args:
            self.response_crsid = args["response_crs"]
            if self.response_crsid not in cfg.published_CRSs:
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
        # For WCS 1.0.0 all bboxes will be specified as minx, miny, maxx, maxy
        if "bbox" not in args:
            raise WCS1Exception("No BBOX parameter supplied",
                                WCS1Exception.MISSING_PARAMETER_VALUE,
                                locator="BBOX or TIME parameter")
        try:
            self.minx, self.miny, self.maxx, self.maxy = map(float, args['bbox'].split(','))
        except:
            raise WCS1Exception("Invalid BBOX parameter",
                                WCS1Exception.INVALID_PARAMETER_VALUE,
                                locator="BBOX parameter")

        # Argument: TIME
        # if self.product.wcs_sole_time:
        #    self.times = [parse(self.product.wcs_sole_time).date()]
        if "time" not in args:
            #      CEOS treats no supplied time argument as all time.
            # I'm really not sure what the right thing to do is, but QGIS wants us to do SOMETHING
            self.times = [self.product.ranges["times"][-1]]
        else:
            # TODO: the min/max/res format option?
            # It's a bit underspeced. I'm not sure what the "res" would look like.
            times = args["time"].split(",")
            self.times = []
            if times == "now":
                pass
            else:
                for t in times:
                    try:
                        time = parse(t).date()
                        if time not in self.product.ranges["time_set"]:
                            raise WCS1Exception(
                                "Time value '%s' not a valid date for coverage %s" % (t, self.product_name),
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

            if len(times) == 0:
                raise WCS1Exception(
                    "No valid ISO-8601 dates",
                    WCS1Exception.INVALID_PARAMETER_VALUE,
                    locator="TIME parameter"
                )
            elif len(times) > 1 and not self.format["multi-time"]:
                raise WCS1Exception(
                    "Cannot select more than one time slice with the %s format" % self.format["name"],
                    WCS1Exception.INVALID_PARAMETER_VALUE,
                    locator="TIME and FORMAT parameters"
                )

        # Range constraint parameter: MEASUREMENTS
        # No default is set in the DescribeCoverage, so it is required
        # But QGIS wants us to work without one, so take default from config
        if "measurements" in args:
            bands = args["measurements"]
            self.bands = []
            for b in bands.split(","):
                try:
                    self.bands.append(self.product.band_idx.band(b))
                except ProductLayerException:
                    raise WCS1Exception("Invalid measurement '%s'" % b,
                                        WCS1Exception.INVALID_PARAMETER_VALUE,
                                        locator="MEASUREMENTS parameter")
            if not bands:
                raise WCS1Exception("No measurements supplied",
                                    WCS1Exception.INVALID_PARAMETER_VALUE,
                                    locator="MEASUREMENTS parameter")
        elif "styles" in args and args["styles"]:
            # Use style bands.
            # Non-standard protocol extension.
            #
            # As we have correlated WCS and WMS service implementations,
            # we can accept a style from WMS, and return the bands used for it.
            styles = args["styles"].split(",")
            if len(styles) != 1:
                raise WCS1Exception("Multiple style parameters not supported")
            style = self.product.style_index.get(styles[0])
            if style:
                self.bands = style.needed_bands
            else:
                self.bands = self.product.wcs_default_bands
        else:
            self.bands = self.product.wcs_default_bands

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
                self.height = int(args["height"])
                if self.height < 1:
                    raise ValueError()
            except ValueError:
                raise WCS1Exception("HEIGHT parameter must be a positive integer",
                                    WCS1Exception.INVALID_PARAMETER_VALUE,
                                    locator="HEIGHT parameter")
            try:
                self.width = int(args["width"])
                if self.width < 1:
                    raise ValueError()
            except ValueError:
                raise WCS1Exception("WIDTH parameter must be a positive integer",
                                    WCS1Exception.INVALID_PARAMETER_VALUE,
                                    locator="WIDTH parameter")
            self.resx = (self.maxx - self.minx) / self.width
            self.resy = (self.maxy - self.miny) / self.height
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
            self.width = (self.maxx - self.minx) / self.resx
            self.height = (self.maxy - self.miny) / self.resy
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
                                        (self.minx, self.miny)
                                       ],
                                       self.request_crs
                                      )

        xscale = (self.maxx - self.minx)/self.width
        yscale = (self.miny - self.maxy)/self.height
        trans_aff = Affine.translation(self.minx, self.maxy)
        scale_aff = Affine.scale(xscale, yscale)
        self.affine = trans_aff * scale_aff
        self.geobox = geometry.GeoBox(self.width, self.height, self.affine, self.request_crs)

@opencensus_trace_call(tracer=tracer)
def get_coverage_data(req):
    #pylint: disable=too-many-locals, protected-access
    dc = get_cube()
    stacker = DataStacker(req.product,
                          req.geobox,
                          req.times,
                          bands=req.bands)
    datasets = stacker.datasets(dc.index)
    if not datasets:
        # TODO: Return an empty coverage file with full metadata?
        cfg = get_config()
        x_range = (req.minx, req.maxx)
        y_range = (req.miny, req.maxy)
        xname = cfg.published_CRSs[req.request_crsid]["horizontal_coord"]
        yname = cfg.published_CRSs[req.request_crsid]["vertical_coord"]
        xvals = numpy.linspace(
            x_range[0],
            x_range[1],
            num=req.width
        )
        yvals = numpy.linspace(
            y_range[0],
            y_range[1],
            num=req.height
        )
        if cfg.published_CRSs[req.request_crsid]["vertical_coord_first"]:
            nparrays = {
                band: (("time", yname, xname),
                       numpy.full((len(req.times), len(yvals), len(xvals)),
                                  req.product.nodata_dict[band])
                      )
                for band in req.bands
            }
        else:
            nparrays = {
                band: (("time", xname, yname),
                       numpy.full((len(req.times), len(xvals), len(yvals)),
                                  req.product.nodata_dict[band])
                      )
                for band in req.bands
            }
        data = xarray.Dataset(
            nparrays,
            coords={
                "time": req.times,
                xname: xvals,
                yname: yvals,
            }
        ).astype("int16")
        release_cube(dc)

        return data

    if req.product.max_datasets_wcs > 0 and len(datasets) > req.product.max_datasets_wcs:
        raise WCS1Exception("This request processes too much data to be served in a reasonable amount of time."
                            "Please reduce the bounds of your request and try again."
                            "(max: %d, this request requires: %d)" % (req.product.max_datasets_wcs, len(datasets)))

    stacker = DataStacker(req.product,
                          req.geobox,
                          req.times,
                          bands=req.bands)
    output = stacker.data(datasets, skip_corrections=True)
    release_cube(dc)
    return output

@opencensus_trace_call(tracer=tracer)
def get_tiff(req, data):
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

    data = data.squeeze(dim="time", drop=True)
    data = data.astype(dtype)
    cfg = get_config()
    xname = cfg.published_CRSs[req.request_crsid]["horizontal_coord"]
    yname = cfg.published_CRSs[req.request_crsid]["vertical_coord"]
    nodata = 0
    for band in data.data_vars:
        nodata = req.product.band_idx.nodata_val(band)
    with MemoryFile() as memfile:
        #pylint: disable=protected-access, bad-continuation
        with memfile.open(
            driver="GTiff",
            width=data.dims[xname],
            height=data.dims[yname],
            count=len(data.data_vars),
            transform=req.affine,
            crs=req.response_crsid,
            nodata=nodata,
            tiled=True,
            compress="lzw",
            interleave="band",
            dtype=dtype) as dst:
            for idx, band in enumerate(data.data_vars, start=1):
                dst.write(data[band].values, idx)
                dst.set_band_description(idx, req.product.band_idx.band_label(band))
                dst.update_tags(idx, STATISTICS_MINIMUM=data[band].values.min())
                dst.update_tags(idx, STATISTICS_MAXIMUM=data[band].values.max())
                dst.update_tags(idx, STATISTICS_MEAN=data[band].values.mean())
                dst.update_tags(idx, STATISTICS_STDDEV=data[band].values.std())
        return memfile.read()


@opencensus_trace_call(tracer=tracer)
def get_netcdf(req, data):
    # Cleanup dataset attributes for NetCDF export
    data.attrs["crs"] = req.response_crsid # geometry.CRS(response_crs)
    for v in data.data_vars.values():
        v.attrs["crs"] = req.response_crsid
        if "spectral_definition" in v.attrs:
            del v.attrs["spectral_definition"]
    if "time" in data and "units" in data["time"].attrs:
        del data["time"].attrs["units"]

    # And export to NetCDF
    return data.to_netcdf()

