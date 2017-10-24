from datetime import timedelta
import json

import datacube
import numpy
import xarray
from affine import Affine
from datacube.storage.masking import make_mask, mask_valid_data as mask_invalid_data
from datacube.utils import geometry

from datacube_wms.cube_pool import get_cube, release_cube
from datacube_wms.wms_cfg import service_cfg
from datacube_wms.wms_utils import get_arg, WMSException, _get_geobox, resp_headers, get_product_from_arg, get_time, \
    img_coords_to_geopoint

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
    def __init__(self, product, geobox, time, style=None, **kwargs):
        super(RGBTileGenerator, self).__init__(**kwargs)
        self._product = product
        self._geobox = geobox
        self._time = [ time, time + timedelta(days=1) ]
        self._style = style

    def needed_bands(self):
        if self._style:
            return self._style.needed_bands
        else:
            return self._product.product.measurements.keys()

    def datasets(self, index, point=None):
        return _get_datasets(index, self._geobox, self._product.name, self._time, point=point)

    def data(self, datasets):
        holder = numpy.empty(shape=tuple(), dtype=object)
        holder[()] = datasets
        sources = xarray.DataArray(holder)

        prod = datasets[0].type
        measurements = [self._set_resampling(prod.measurements[name]) for name in self.needed_bands()]
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


def _get_datasets(index, geobox, product, time_, point=None):
    query = datacube.api.query.Query(product=product, geopolygon=geobox.extent, time=time_)
    datasets = index.datasets.search_eager(**query.search_terms)
    datasets.sort(key=lambda d: d.center_time)
    dataset_iter = iter(datasets)
    to_load = []
    if point:
        for dataset in dataset_iter:
            if dataset.extent.to_crs(geobox.crs).contains(point):
                return [ dataset ]
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
    # GetMap 1.1.1 must be supported for Terria
    version = get_arg(args, "version", "WMS version",
                      permitted_values=["1.1.1", "1.3.0"])

    # CRS parameter
    if version == "1.1.1":
        crs_arg = "srs"
    else:
        crs_arg = "crs"
    crsid = get_arg(args, crs_arg, "Coordinate Reference System",
                  errcode=WMSException.INVALID_CRS,
                  permitted_values=service_cfg["published_CRSs"])
    crs = geometry.CRS(crsid)

    # Layers and Styles parameters
    product = get_product_from_arg(args)
    styles = args.get("styles", "").split(",")
    if len(styles) != 1:
        raise WMSException("Multi-layer GetMap requests not supported")
    style_r = styles[0]
    if not style_r:
        style_r = product.platform.default_style
    style = product.platform.style_index.get(style_r)
    if not style:
        raise WMSException("Style %s is not defined" % style_r,
                           WMSException.STYLE_NOT_DEFINED,
                           locator="Style parameter")

    # Format parameter
    fmt = get_arg(args, "format", "image format",
                  errcode=WMSException.INVALID_FORMAT,
                  lower=True,
                  permitted_values=["image/png"])

    # BBox, height and width parameters
    geobox = _get_geobox(args, crs)

    # Time parameter
    time = get_time(args, product)

    # Tiling.
    tiler = RGBTileGenerator(product, geobox, time, style=style)
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

def feature_info(args):
    # Version parameter
    version = get_arg(args, "version", "WMS version",
                        permitted_values=["1.1.1", "1.3.0"])

    # Layer/product
    product = get_product_from_arg(args, "query_layers")

    fmt = get_arg(args, "info_format", "info format", lower=True, errcode=WMSException.INVALID_FORMAT,
                  permitted_values=["application/json"])

    # CRS parameter
    if version == "1.1.1":
        crs_arg = "srs"
    else:
        crs_arg = "crs"
    crsid = get_arg(args, crs_arg, "Coordinate Reference System",
                    errcode=WMSException.INVALID_FORMAT,
                    permitted_values=service_cfg["published_CRSs"])
    crs = geometry.CRS(crsid)

    # BBox, height and width parameters
    geobox = _get_geobox(args, crs)

    # Time parameter
    time = get_time(args, product)

    # Point coords
    if version == "1.1.1":
        coords = [ "x", "y" ]
    else:
        coords = [ "i", "j" ]
    i = args.get(coords[0])
    j = args.get(coords[1])
    if i is None:
        raise WMSException("HorizontalCoordinate not supplied", WMSException.INVALID_POINT,
                           "%s parameter" % coords[0])
    if j is None:
        raise WMSException("Vertical coordinate not supplied", WMSException.INVALID_POINT,
                           "%s parameter" % coords[0])
    i = int(i)
    j = int(j)
    feature_json = {}
    tiler = RGBTileGenerator(product, geobox, time)
    dc = get_cube()
    datasets = tiler.datasets(dc.index, point=img_coords_to_geopoint(geobox, i, j))
    if not datasets:
        pass
    else:
        data = tiler.data(datasets)
        # Use i,j image coordinates to extract data pixel from dataset, and
        # convert to lat/long geographic coordinates
        if crsid == "EPSG:4326":
            feature_json["lat"]=data.latitude[j].item()
            feature_json["lon"]=data.longitude[i].item()
            pixel_ds = data.isel(latitude=[j], longitude=[i])
        elif crsid == "EPSG:3857":
            x=data.x[i].item()
            y=data.y[j].item()
            pt=geometry.point(x, y, crs)
            crs_geo = geometry.CRS("EPSG:4326")
            ptg = pt.to_crs(crs_geo)
            feature_json["lon"], feature_json["lat"]=ptg.coords[0]
            pixel_ds = data.isel(x=[i], y=[j])
        # Get accurate timestamp from dataset
        feature_json["time"]=datasets[0].center_time.strftime("%Y-%m-%d %H:%M:%S")
        # Collect raw band values for pixel
        for band in tiler.needed_bands():
            feature_json[band] = pixel_ds[band].item()

    release_cube(dc)
    result = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": feature_json
            }
        ]
    }
    return json.dumps(result), 200, resp_headers({"Content-Type": "application/json"})

