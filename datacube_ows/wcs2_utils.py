from __future__ import absolute_import, division, print_function

from dateutil.parser import parse

import datacube
import numpy
import xarray
from affine import Affine

from datacube.utils import geometry
from rasterio import MemoryFile

from datacube_ows.cube_pool import get_cube, release_cube, cube
from datacube_ows.data import DataStacker
from datacube_ows.ogc_exceptions import WCS2Exception
from datacube_ows.ogc_utils import ProductLayerException
from datacube_ows.ows_configuration import get_config
from datacube_ows.utils import opencensus_trace_call, get_opencensus_tracer

tracer = get_opencensus_tracer()

@opencensus_trace_call(tracer=tracer)
def get_coverage_data(req):
    #pylint: disable=too-many-locals, protected-access

    cfg = get_config()

     # Argument: Coverage (required)
    if "coverage" not in args:
        raise WCS1Exception("No coverage specified",
                            WCS2Exception.MISSING_PARAMETER_VALUE,
                            locator="COVERAGE parameter")
    self.product_name = args["coverage"]
    self.product = cfg.product_index.get(self.product_name)
    if not self.product or not self.product.wcs:
        raise WCS2Exception("Invalid coverage: %s" % self.product_name,
                            WCS2Exception.COVERAGE_NOT_DEFINED,
                            locator="COVERAGE parameter")


    with cube():
        pass


    # times =




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
        # TODO: Return an empty coverage file with full metadata?
        extents = dc.load(dask_chunks={}, product=req.product.product.name, geopolygon=req.geobox.extent, time=stacker._time)
        cfg = get_config()
        x_range = (req.minx, req.maxx)
        y_range = (req.miny, req.maxy)
        xname = cfg.published_CRSs[req.request_crsid]["horizontal_coord"]
        yname = cfg.published_CRSs[req.request_crsid]["vertical_coord"]
        if xname in extents:
            xvals = extents[xname]
        else:
            xvals = numpy.linspace(
                x_range[0],
                x_range[1],
                num=req.width
            )
        if yname in extents:
            yvals = extents[yname]
        else:
            yvals = numpy.linspace(
                y_range[0],
                y_range[1],
                num=req.height
            )
        if cfg.published_CRSs[req.request_crsid]["vertical_coord_first"]:
            nparrays = {
                band: ((yname, xname),
                       numpy.full((len(yvals), len(xvals)),
                                  req.product.nodata_dict[band])
                      )
                for band in req.bands
            }
        else:
            nparrays = {
                band: ((xname, yname),
                       numpy.full((len(xvals), len(yvals)),
                                  req.product.nodata_dict[band])
                      )
                for band in req.bands
            }
        data = xarray.Dataset(
            nparrays,
            coords={
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

    if req.format["multi-time"] and len(req.times) > 1:
        # Group by solar day
        group_by = datacube.api.query.query_group_by(time=req.times, group_by='solar_day')
        datasets = dc.group_datasets(datasets, group_by)

    stacker = DataStacker(req.product,
                          req.geobox,
                          req.times[0],
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

