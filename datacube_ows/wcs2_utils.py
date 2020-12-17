from __future__ import absolute_import, division, print_function

import logging
from dateutil.parser import parse

import collections
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
from datacube_ows.data import DataStacker, datasets_in_xarray
from datacube_ows.ogc_exceptions import WCS2Exception
from datacube_ows.mv_index import MVSelectOpts
from datacube_ows.ows_configuration import get_config
from datacube_ows.wcs_scaler import WCSScaler, WCSScalerUnknownDimension

_LOG = logging.getLogger(__name__)


def uniform_crs(cfg, crs):
    " Helper function to transform a URL style EPSG definition to an 'EPSG:nnn' one "
    if crs.startswith('http://www.opengis.net/def/crs/EPSG/'):
        code = crs.rpartition('/')[-1]
        crs = 'EPSG:%s' % code
    elif crs.startswith('urn:ogc:def:crs:EPSG:'):
        code = crs.rpartition(':')[-1]
        crs = 'EPSG:%s' % code
    elif crs.startswith('EPSG'):
        pass
    elif crs in cfg.published_CRSs:
        pass
    else:
        raise WCS2Exception("Not a CRS: %s" % crs,
                            WCS2Exception.NOT_A_CRS,
                            locator=crs,
                            valid_keys=list(cfg.published_CRSs))
    return crs


def get_coverage_data(request):
    #pylint: disable=too-many-locals, protected-access

    cfg = get_config()

    layer_name = request.coverage_id
    layer = cfg.product_index.get(layer_name)
    if not layer or not layer.wcs:
        raise WCS2Exception("Invalid coverage: %s" % layer_name,
                            WCS2Exception.NO_SUCH_COVERAGE,
                            locator="COVERAGE parameter",
                            valid_keys=list(cfg.product_index))

    with cube() as dc:
        if not dc:
            raise WCS2Exception("Database connectivity failure")
        #
        # CRS handling
        #

        native_crs = layer.native_CRS
        subsetting_crs = uniform_crs(cfg, request.subsetting_crs or native_crs)
        output_crs = uniform_crs(cfg, request.output_crs or subsetting_crs)

        if subsetting_crs not in cfg.published_CRSs:
            raise WCS2Exception("Invalid subsettingCrs: %s" % subsetting_crs,
                                WCS2Exception.SUBSETTING_CRS_NOT_SUPPORTED,
                                locator=subsetting_crs,
                                valid_keys=list(cfg.published_CRSs))

        output_crs = uniform_crs(cfg, request.output_crs or subsetting_crs or native_crs)

        if output_crs not in cfg.published_CRSs:
            raise WCS2Exception("Invalid outputCrs: %s" % output_crs,
                                WCS2Exception.OUTPUT_CRS_NOT_SUPPORTED,
                                locator=output_crs,
                                valid_keys=list(cfg.published_CRSs))

        #
        # Subsetting/Scaling
        #

        scaler = WCSScaler(layer, subsetting_crs)
        times = layer.ranges["times"]

        subsets = request.subsets

        if len(subsets) != len(set(subset.dimension.lower() for subset in subsets)):
            dimensions = [subset.dimension.lower() for subset in subsets]
            duplicate_dimensions = [
                item
                for item, count in collections.Counter(dimensions).items()
                if count > 1
            ]

            raise WCS2Exception("Duplicate dimension%s: %s" % (
                                    's' if len(duplicate_dimensions) > 1 else '',
                                    ', '.join(duplicate_dimensions)
                                ),
                                WCS2Exception.INVALID_SUBSETTING,
                                locator=','.join(duplicate_dimensions)
                                )

        for subset in subsets:
            dimension = subset.dimension.lower()
            if dimension == 'time':
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
                try:
                    if isinstance(subset, Trim):
                        scaler.trim(dimension, subset.low, subset.high)
                    elif isinstance(subset, Slice):
                        scaler.slice(dimension, subset.point)
                except WCSScalerUnknownDimension:
                    raise WCS2Exception('Invalid subsetting axis %s' % subset.dimension,
                                    WCS2Exception.INVALID_AXIS_LABEL,
                                    locator=subset.dimension)

        #
        # Transform spatial extent to native CRS.
        #
        scaler.to_crs(output_crs)

        #
        # Scaling
        #

        scales = request.scales
        if len(scales) != len(set(subset.axis.lower() for subset in scales)):
            axes = [subset.axis.lower() for subset in scales]
            duplicate_axes = [
                item
                for item, count in collections.Counter(axes).items()
                if count > 1
            ]
            raise WCS2Exception('Duplicate scales for ax%ss: %s' % (
                                    'i' if len(duplicate_axes) == 1 else 'e',
                                    ', '.join(duplicate_axes)
                                ),
                                WCS2Exception.INVALID_SCALE_FACTOR,
                                locator=','.join(duplicate_axes)
                                )

        for scale in scales:
            axis = scale.axis.lower()

            if axis in ('time', 'k'):
                raise WCS2Exception('Cannot scale axis %s' % scale.axis,
                                    WCS2Exception.INVALID_SCALE_FACTOR,
                                    locator=scale.axis
                                    )
            else:
                if isinstance(scale, ScaleAxis):
                    scaler.scale_axis(axis, scale.factor)
                elif isinstance(scale, ScaleSize):
                    scaler.scale_size(axis, scale.size)
                elif isinstance(scale, ScaleExtent):
                    scaler.scale_extent(axis, scale.low, scale.high)

        #
        # Rangesubset
        #

        band_labels = layer.band_idx.band_labels()
        if request.range_subset:
            bands = []
            for range_subset in request.range_subset:
                if isinstance(range_subset, str):
                    if range_subset not in band_labels:
                        raise WCS2Exception('No such field %s' % range_subset,
                                    WCS2Exception.NO_SUCH_FIELD,
                                    locator=range_subset,
                                    valid_keys=band_labels
                                    )
                    bands.append(range_subset)
                else:
                    if range_subset.start not in band_labels:
                        raise WCS2Exception('No such field %s' % range_subset.start,
                                            WCS2Exception.ILLEGAL_FIELD_SEQUENCE,
                                            locator=range_subset.start,
                                            valid_keys = band_labels)
                    if range_subset.end not in band_labels:
                        raise WCS2Exception('No such field %s' % range_subset.end,
                                            WCS2Exception.ILLEGAL_FIELD_SEQUENCE,
                                            locator=range_subset.end,
                                            valid_keys = band_labels)

                    start = band_labels.index(range_subset.start)
                    end = band_labels.index(range_subset.end)
                    bands.extend(band_labels[start:(end + 1) if end > start else (end - 1)])
        else:
            bands = layer.wcs_default_bands  # TODO: standard says differently

        #
        # Format handling
        #

        if not request.format:
            fmt = cfg.wcs_formats_by_name[layer.native_format]
        else:
            try:
                fmt = cfg.wcs_formats_by_mime[request.format]
            except KeyError:
                raise WCS2Exception("Unsupported format: %s" % request.format,
                                    WCS2Exception.INVALID_PARAMETER_VALUE,
                                    locator="FORMAT",
                                    valid_keys=list(cfg.wcs_formats_by_mime))

        if len(times) > 1 and not fmt.multi_time:
            raise WCS2Exception(
                "Format does not support multi-time datasets - "
                "either constrain the time dimension or choose a different format",
                WCS2Exception.INVALID_SUBSETTING,
                locator="FORMAT or SUBSET"
                                )
        affine = scaler.affine()
        geobox = geometry.GeoBox(scaler.size.x, scaler.size.y,
                                 affine, cfg.crs(output_crs))

        stacker = DataStacker(layer,
                              geobox,
                              times,
                              bands=bands)
        n_datasets = stacker.datasets(dc.index, mode=MVSelectOpts.COUNT)

        if layer.max_datasets_wcs > 0 and n_datasets > layer.max_datasets_wcs:
            raise WCS2Exception("This request processes too much data to be served in a reasonable amount of time."
                                "Please reduce the bounds of your request and try again."
                                "(max: %d, this request requires: %d)" % (layer.max_datasets_wcs, n_datasets))
        elif n_datasets == 0:
            raise WCS2Exception("The requested spatio-temporal subsets return no data.",
                                WCS2Exception.INVALID_SUBSETTING,
                                http_response=404)

        datasets = stacker.datasets(dc.index)
        if fmt.multi_time and len(times) > 1:
            # Group by solar day
            group_by = datacube.api.query.query_group_by(time=times, group_by='solar_day')
            datasets = dc.group_datasets(datasets, group_by)

        output = stacker.data(datasets, skip_corrections=True)

    #
    # TODO: configurable
    #
    if fmt.mime == 'image/geotiff':
        output = fmt.renderer(request.version)(request, output, output_crs,
                              layer, scaler.size.x, scaler.size.y, affine)

    else:
        output = fmt.renderer(request.version)(request, output, output_crs)

    headers = {
        "Content-Type": fmt.mime,
        'content-disposition': f'attachment; filename={request.coverage_id}.{fmt.extension}',
    }
    headers.update(layer.wcs_cache_rules.cache_headers(n_datasets))
    return output, headers


def get_tiff(request, data, crs, product, width, height, affine):
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

    data = data.squeeze(dim="time", drop=True)
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

