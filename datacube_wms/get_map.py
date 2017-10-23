from datetime import timedelta, datetime

import datacube
import numpy
import xarray
from affine import Affine
from datacube.storage.masking import make_mask, mask_valid_data as mask_invalid_data
from datacube.utils import geometry

from datacube_wms.cube_pool import get_cube, release_cube
from datacube_wms.wms_cfg import service_cfg
from datacube_wms.wms_layers import get_layers
from datacube_wms.wms_utils import WMSException, _get_geobox, resp_headers

# travis can only get earlier version of rasterio which doesn't have MemoryFile, so
# - tell pylint to ingnore inport error
# - catch ImportError so pytest doctest don't fall over
try:
    from rasterio.io import MemoryFile  # pylint: disable=import-error
except ImportError:
    MemoryFile = None



class TileGenerator(object):
    def __init__(self, **kwargs):
        pass

    def datasets(self, index):
        pass

    def data(self, datasets):
        pass


class RGBTileGenerator(TileGenerator):
    def __init__(self, product, style, geobox, time, **kwargs):
        super(RGBTileGenerator, self).__init__(**kwargs)
        self._product = product
        self._style = style
        self._geobox = geobox
        self._time = [ time, time + timedelta(days=1) ]

    def datasets(self, index):
        return _get_datasets(index, self._geobox, self._product.name, self._time)

    def data(self, datasets):
        holder = numpy.empty(shape=tuple(), dtype=object)
        holder[()] = datasets
        sources = xarray.DataArray(holder)

        prod = datasets[0].type
        measurements = [self._set_resampling(prod.measurements[name]) for name in self._style.needed_bands]
        with datacube.set_options(reproject_threads=1, fast_load=True):
            return datacube.Datacube.load_data(sources, self._geobox, measurements)

    def _set_resampling(self, measurement):
        mc = measurement.copy()
        # mc['resampling_method'] = 'cubic'
        return mc


class LatestCloudFree(TileGenerator):
    # TODO: The contract for Tile Generators has changed since this was last used.
    def __init__(self, product, bands, mask, mask_band, mask_flags, geobox, time, **kwargs):
        super(LatestCloudFree, self).__init__(**kwargs)
        self._product = product
        self._bands = bands
        self._mask = mask
        self._mask_band = mask_band
        self._mask_flags = mask_flags
        self._geobox = geobox
        self._time = time

    def _get_datasets(self, index, product, geobox, time):
        query = datacube.api.query.Query(product=product, geopolygon=geobox.extent, time=time)
        datasets = index.datasets.search_eager(**query.search_terms)
        return [dataset for dataset in datasets if dataset.extent.to_crs(geobox.crs).intersects(geobox.extent)]

    def datasets(self, index):
        return {
            'product': self._get_datasets(index, self._product, self._geobox, self._time),
            'mask': self._get_datasets(index, self._mask, self._geobox, self._time)
        }

    def data(self, datasets):
        prod_sources = datacube.Datacube.group_datasets(datasets['product'], datacube.api.query.query_group_by())
        mask_sources = datacube.Datacube.group_datasets(datasets['mask'], datacube.api.query.query_group_by())
        # pylint: disable=unbalanced-tuple-unpacking
        prod_sources, mask_sources = xarray.align(prod_sources, mask_sources)

        fused_data = None
        fused_mask = None
        for i in reversed(range(0, prod_sources.time.size)):
            prod = datasets['mask'][0].type
            measurements = [self._set_resampling(prod.measurements[name]) for name in (self._mask_band, )]
            with datacube.set_options(reproject_threads=1, fast_load=True):
                pq_data = datacube.Datacube.load_data(mask_sources[i], self._geobox, measurements)
            mask = make_mask(pq_data[self._mask_band], **self._mask_flags)

            # skip real cloudy stuff
            if numpy.count_nonzero(mask) < mask.size*0.05:
                continue

            prod = datasets['product'][0].type
            measurements = [self._set_resampling(prod.measurements[name]) for name in self._bands]

            with datacube.set_options(reproject_threads=1, fast_load=True):
                pix_data = datacube.Datacube.load_data(prod_sources[i], self._geobox, measurements)
            pix_data = mask_invalid_data(pix_data)

            if fused_data is None:
                fused_data = pix_data
                fused_mask = mask
                continue

            copy_mask = (~fused_mask) & mask  # pylint: disable=invalid-unary-operand-type
            for band in self._bands:
                numpy.copyto(fused_data[band].values, pix_data[band].values, where=copy_mask)
            fused_mask = fused_mask | mask

            # don't try to get 100% cloud free
            if numpy.count_nonzero(fused_mask) > fused_mask.size*0.95:
                break

        return fused_data

    def _set_resampling(self, measurement):
        mc = measurement.copy()
        # mc['resampling_method'] = 'cubic'
        return mc


def _get_datasets(index, geobox, product, time_):
    query = datacube.api.query.Query(product=product, geopolygon=geobox.extent, time=time_)
    datasets = index.datasets.search_eager(**query.search_terms)
    datasets.sort(key=lambda d: d.center_time)
    dataset_iter = iter(datasets)
    to_load = []
    for dataset in dataset_iter:
        if dataset.extent.to_crs(geobox.crs).intersects(geobox.extent):
            to_load.append(dataset)
            break
    else:
        return None

    geom = to_load[0].extent.to_crs(geobox.crs)
    for dataset in dataset_iter:
        if geom.contains(geobox.extent):
            break
        ds_extent = dataset.extent.to_crs(geobox.crs)
        if geom.contains(ds_extent):
            continue
        if ds_extent.intersects(geobox.extent):
            to_load.append(dataset)
            geom = geom.union(dataset.extent.to_crs(geobox.crs))
    return to_load


def get_map(args):
    # Version parameter
    version = args.get("version")
    if not version:
        raise WMSException("No WMS version supplied", locator="Version parameter")
    # GetMap 1.1.1 must be supported for Terria
    if version not in [ "1.1.1", "1.3.0" ]:
        raise WMSException("Unsupported WMS version: %s" % version,
                           locator="Version parameter")

    # CRS parameter
    if version == "1.1.1":
        crsid = args.get("srs")
    else:
        crsid = args.get("crs")
    if crsid not in service_cfg["published_CRSs"]:
        raise WMSException(
                    "Unsupported Coordinate Reference System: %s" % crsid,
                    WMSException.INVALID_CRS,
                    locator="CRS parameter")
    crs = geometry.CRS(crsid)

    # Layers and Styles parameters
    layers = args.get("layers", "").split(",")
    styles = args.get("styles", "").split(",")
    if len(layers) != 1 or len(styles) != 1:
        raise WMSException("Multi-layer GetMap requests not supported")
    layer = layers[0]
    style_r = styles[0]
    if not layer:
        raise WMSException("No layer specified in GetMap request")
    platforms = get_layers()
    product = platforms.product_index.get(layer)
    if not product:
        raise WMSException("Layer %s is not defined" % layer,
                           WMSException.LAYER_NOT_DEFINED,
                           locator="Layer parameter")
    if not style_r:
        style_r = product.platform.default_style
    style = product.platform.style_index.get(style_r)
    if not style:
        raise WMSException("Style %s is not defined" % style_r,
                           WMSException.STYLE_NOT_DEFINED,
                           locator="Style parameter")

    # Format parameter
    fmt = args.get("format", "").lower()
    if not fmt:
        raise WMSException("No image format specified",
                           WMSException.INVALID_FORMAT,
                           locator="Format parameter")
    elif fmt != "image/png":
        raise WMSException("Image format %s is not supported" % layer,
                           WMSException.INVALID_FORMAT,
                           locator="Format parameter")

    # BBox, height and width parameters
    geobox = _get_geobox(args, crs)

    # Time parameter
    times = args.get('time', '').split('/')
    if len(times) > 1:
        raise WMSException(
                    "Selecting multiple time dimension values not supported",
                    WMSException.INVALID_DIMENSION_VALUE,
                    locator="Time parameter")
    elif not times[0]:
        raise WMSException(
                    "Time dimension value not supplied",
                    WMSException.MISSING_DIMENSION_VALUE,
                    locator="Time parameter")
    try:
        time = datetime.strptime(times[0], "%Y-%m-%d").date()
    except ValueError:
        raise WMSException(
                    "Time dimension value '%s' not valid for this layer" % times[0],
                    WMSException.INVALID_DIMENSION_VALUE,
                    locator="Time parameter")

    # Validate time paramter for requested layer.
    if time not in product.ranges["time_set"]:
        raise WMSException(
                    "Time dimension value '%s' not valid for this layer" % times[0],
                    WMSException.INVALID_DIMENSION_VALUE,
                    locator="Time parameter")

    # Tiling.
    tiler = RGBTileGenerator(product, style, geobox, time)
    dc = get_cube()
    datasets = tiler.datasets(dc.index)
    if not datasets:
        body = _write_empty(geobox)
    else:
        data = tiler.data(datasets)
        if data:
            body = _write_png(data, style)
        else:
            body = _write_empty(geobox)
    release_cube(dc)
    return body, 200, resp_headers({"Content-Type": "image/png"})


def _write_png(data, style):
    width = data[data.crs.dimensions[1]].size
    height = data[data.crs.dimensions[0]].size

    img_data = style.transform_data(data)

    with MemoryFile() as memfile:
        with memfile.open(driver='PNG',
                          width=width,
                          height=height,
                          count=3,
                          transform=Affine.identity(),
                          nodata=0,
                          dtype='uint8') as thing:
            scaled = None
            for idx, band in enumerate(img_data.data_vars, start=1):
                thing.write_band(idx, img_data[band].values)

        return memfile.read()


def _write_empty(geobox):
    with MemoryFile() as memfile:
        with memfile.open(driver='PNG',
                          width=geobox.width,
                          height=geobox.height,
                          count=1,
                          transform=Affine.identity(),
                          nodata=0,
                          dtype='uint8') as thing:
            pass
        return memfile.read()