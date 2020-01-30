from __future__ import absolute_import, division, print_function

import logging
from dateutil.parser import parse

import datacube
import numpy
import xarray
from affine import Affine

from datacube.utils import geometry
from rasterio import MemoryFile
from rasterio.warp import calculate_default_transform

from ows.wcs.v20 import (
    Slice, Trim, ScaleSize, ScaleAxis, ScaleExtent
)

from datacube_ows.cube_pool import get_cube, release_cube, cube
from datacube_ows.data import DataStacker
from datacube_ows.ogc_exceptions import WCS2Exception
from datacube_ows.ogc_utils import ProductLayerException
from datacube_ows.ows_configuration import get_config
from datacube_ows.utils import opencensus_trace_call, get_opencensus_tracer

_LOG = logging.getLogger(__name__)

tracer = get_opencensus_tracer()


def uniform_crs(crs):
    " Helper function to transform a URL style EPSG definition to an 'EPSG:nnn' one "
    if crs.startswith('http://www.opengis.net/def/crs/EPSG/'):
        code = crs.rpartition('/')[-1]
        crs = 'EPSG:%s' % code
    elif crs.startswith('urn:ogc:def:crs:EPSG:'):
        code = crs.rpartition(':')[-1]
        crs = 'EPSG:%s' % code
    return crs


@opencensus_trace_call(tracer=tracer)
def get_coverage_data(request):
    #pylint: disable=too-many-locals, protected-access

    cfg = get_config()

    product_name = request.coverage_id
    product = cfg.product_index.get(product_name)
    if not product or not product.wcs:
        raise WCS2Exception("Invalid coverage: %s" % product_name,
                            WCS2Exception.COVERAGE_NOT_DEFINED,
                            locator="COVERAGE parameter")

    dc = get_cube()

    #
    # CRS handling
    #

    native_crs = product.native_CRS
    subsetting_crs = uniform_crs(request.subsetting_crs or native_crs)

    assert subsetting_crs in cfg.published_CRSs

    output_crs = uniform_crs(request.output_crs or subsetting_crs or native_crs)

    assert output_crs in cfg.published_CRSs

    request_crs = geometry.CRS(subsetting_crs)

    #
    # Subsetting/Scaling
    #

    extent_x = (
        product.ranges["bboxes"][subsetting_crs]["left"],
        product.ranges["bboxes"][subsetting_crs]["right"],
    )

    extent_y = (
        product.ranges["bboxes"][subsetting_crs]["bottom"],
        product.ranges["bboxes"][subsetting_crs]["top"],
    )

    times = product.ranges["times"]


    _LOG.info(times)
    subsetting_crs_def = cfg.published_CRSs[subsetting_crs]
    x_name = subsetting_crs_def['horizontal_coord'].lower()
    y_name = subsetting_crs_def['vertical_coord'].lower()

    # TODO: Slices along spatial axes

    subsets = request.subsets
    if len(subsets) != len(set(subset.dimension.lower() for subset in subsets)):
        dimension = 'TODO'
        raise WCS2Exception('Duplicate subsets for axis %s' % dimension, )


    _LOG.info(x_name, y_name)

    for subset in subsets:
        dimension = subset.dimension.lower()
        if dimension == x_name:
            if isinstance(subset, Trim):
                extent_x = (
                    subset.low if subset.low is not None else extent_x[0],
                    subset.high if subset.high is not None else extent_x[1],
                )
            elif isinstance(subset, Slice):
                extent_x = subset.point

        elif dimension == y_name:
            if isinstance(subset, Trim):
                extent_y = (
                    subset.low if subset.low is not None else extent_y[0],
                    subset.high if subset.high is not None else extent_y[1],
                )
            elif isinstance(subset, Slice):
                extent_y = subset.point

        elif dimension == 'time':
            if isinstance(subset, Trim):
                low = parse(subset.low).date() if subset.low is not None else None
                high = parse(subset.high).date() if subset.high is not None else None
                if low is not None:
                    times = [
                        time for time in times
                        if time >= low
                    ]
                if high is not None:
                    times = [
                        time for time in times
                        if time <= high
                    ]
            elif isinstance(subset, Slice):
                point = parse(subset.point).date()
                times = [point]

        else:
            raise WCS2Exception('Invalid subsetting axis %s' % subset.dimension, )

    #
    # Scaling
    #

    scales = request.scales
    if len(scales) != len(set(subset.axis.lower() for subset in scales)):
        axis = 'TODO'
        raise WCS2Exception('Duplicate scales for axis %s' % axis, )

    x_resolution = product.resolution_x
    y_resolution = product.resolution_y
    x_size = round((extent_x[1] - extent_x[0]) / x_resolution)
    y_size = round((extent_y[1] - extent_y[0]) / x_resolution)

    if native_crs != subsetting_crs:
        transform_result = calculate_default_transform(
            geometry.CRS(native_crs),
            geometry.CRS(subsetting_crs),
            x_size, y_size,
            left=extent_x[0],
            right=extent_x[1],
            bottom=extent_y[0],
            top=extent_y[1],
        )
        x_size, y_size = transform_result[1]

    for scale in scales:
        axis = scale.axis.lower()

        if axis in (x_name, 'x', 'i'):
            if isinstance(scale, ScaleAxis):
                if x_size is None:
                    raise Exception('Cannot scale axis %s' % scale.axis)

                x_size *= scale.factor

            elif isinstance(scale, ScaleSize):
                x_size = scale.size

            elif isinstance(scale, ScaleExtent):
                x_size = scale.high - scale.low

        elif axis in (y_name, 'y', 'j'):
            if isinstance(scale, ScaleAxis):
                if y_size is None:
                    raise Exception('Cannot scale axis %s' % scale.axis)

                y_size *= scale.factor

            elif isinstance(scale, ScaleSize):
                y_size = scale.size

            elif isinstance(scale, ScaleExtent):
                y_size = scale.high - scale.low

        elif axis in ('time', 'k'):
            raise Exception('Cannot scale axis %s' % scale.axis)

        else:
            raise WCS2Exception('Invalid scaling axis %s' % scale.axis)

    _LOG.info(request.subsets)

    #
    # Rangesubset
    #

    band_labels = product.band_idx.band_labels()
    if request.range_subset:
        bands = []
        for range_subset in request.range_subset:
            if isinstance(range_subset, str):
                if range_subset not in band_labels:
                    raise Exception('no such field')
                bands.append(range_subset)
            else:
                if range_subset.start not in band_labels:
                    raise Exception('no such field')
                if range_subset.end not in band_labels:
                    raise Exception('no such field')

                start = band_labels.index(range_subset.start)
                end = band_labels.index(range_subset.end)
                bands.extend(band_labels[start:(end + 1) if end > start else (end - 1)])
    else:
        bands = product.wcs_default_bands  # TODO: standard says differently

    #
    # Format handling
    #

    if not request.format:
        fmt = cfg.wcs_formats[cfg.native_wcs_format]
    else:
        for fmt in cfg.wcs_formats.values():
            if fmt['mime'] == request.format:
                break
        else:
            raise WCS2Exception("Unsupported format: %s" % request.format,
                                WCS2Exception.INVALID_PARAMETER_VALUE,
                                locator="FORMAT parameter")

    x_resolution = (extent_x[1] - extent_x[0]) / x_size
    y_resolution = (extent_y[1] - extent_y[0]) / y_size

    trans_aff = Affine.translation(extent_x[0], extent_y[1])
    scale_aff = Affine.scale(x_resolution, -y_resolution)
    affine = trans_aff * scale_aff
    geobox = geometry.GeoBox(x_size, y_size, affine, geometry.CRS(subsetting_crs))

    datasets = []
    for time in times:
        # IF t was passed to the datasets method instead of the stacker
        # constructor, we could use the one stacker.
        stacker = DataStacker(product,
                              geobox,
                              time,
                              bands=bands)
        t_datasets = stacker.datasets(dc.index)

        if not t_datasets:
            # No matching data for this date
            continue
        datasets.extend(t_datasets)

    if product.max_datasets_wcs > 0 and len(datasets) > product.max_datasets_wcs:
        raise WCS2Exception("This request processes too much data to be served in a reasonable amount of time."
                            "Please reduce the bounds of your request and try again."
                            "(max: %d, this request requires: %d)" % (product.max_datasets_wcs, len(datasets)))

    _LOG.info('After iterating')

    if fmt["multi-time"] and len(times) > 1:
        # Group by solar day
        group_by = datacube.api.query.query_group_by(time=times, group_by='solar_day')
        datasets = dc.group_datasets(datasets, group_by)

    _LOG.info(datasets)

    stacker = DataStacker(product,
                          geobox,
                          times[0],
                          bands=bands)


    output = stacker.data(datasets, skip_corrections=True)

    _LOG.info(output)

    release_cube(dc)

    #
    # TODO: configurable
    #
    if fmt['mime'] == 'image/geotiff':
        output = get_tiff(request, output, product, x_size, y_size, affine, output_crs)

    elif fmt['mime'] == 'application/x-netcdf':
        output = get_netcdf(request, output, output_crs)
    else:
        pass

    filename = '%s.%s' % (request.coverage_id, fmt['extension'])
    return output, fmt['mime'], filename


@opencensus_trace_call(tracer=tracer)
def get_tiff(request, data, product, width, height, affine, crs):
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

    # TODO: convert other parameters as-well
    gtiff = request.geotiff_encoding_parameters

    data = data.astype(dtype)
    nodata = 0
    for band in data.data_vars:
        nodata = product.band_idx.nodata_val(band)
    with MemoryFile() as memfile:
        #pylint: disable=protected-access, bad-continuation

        kwargs = {}
        if gtiff.tile_width is not None:
            kwargs['blockxsize'] = gtiff.tile_width
        if gtiff.tile_height is not None:
            kwargs['blockysize'] = gtiff.tile_height

        if gtiff.predictor:
            predictor = gtiff.predictor.lower()
            if predictor == 'horizontal':
                kwargs['predictor'] = 2
            elif predictor == 'floatingpoint':
                kwargs['predictor'] = 3

        with memfile.open(
            driver="GTiff",
            width=width,
            height=height,
            count=len(data.data_vars),
            transform=affine,
            crs=crs,
            nodata=nodata,
            tiled=gtiff.tiling if gtiff.tiling is not None else True,
            compress=gtiff.compression.lower() if gtiff.compression else "lzw",
            predictor=2,
            interleave=gtiff.interleave or "band",
            dtype=dtype, **kwargs) as dst:
            for idx, band in enumerate(data.data_vars, start=1):
                dst.write(data[band].values, idx)
                dst.set_band_description(idx, product.band_idx.band_label(band))
                dst.update_tags(idx, STATISTICS_MINIMUM=data[band].values.min())
                dst.update_tags(idx, STATISTICS_MAXIMUM=data[band].values.max())
                dst.update_tags(idx, STATISTICS_MEAN=data[band].values.mean())
                dst.update_tags(idx, STATISTICS_STDDEV=data[band].values.std())
        return memfile.read()


@opencensus_trace_call(tracer=tracer)
def get_netcdf(request, data, crs):
    # Cleanup dataset attributes for NetCDF export
    data.attrs["crs"] = crs # geometry.CRS(response_crs)
    for v in data.data_vars.values():
        v.attrs["crs"] = crs
        if "spectral_definition" in v.attrs:
            del v.attrs["spectral_definition"]
    if "time" in data and "units" in data["time"].attrs:
        del data["time"].attrs["units"]

    # And export to NetCDF
    return data.to_netcdf()

