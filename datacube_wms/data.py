from datetime import timedelta, datetime
import json
from skimage.draw import polygon as skimg_polygon

import datacube

import numpy
import xarray
from affine import Affine

from datacube.storage.masking import make_mask, mask_invalid_data
from datacube.utils import geometry

from datacube_wms.cube_pool import get_cube, release_cube, pool_size
from datacube_wms.wms_cfg import service_cfg
from datacube_wms.wms_utils import get_arg, WMSException, _get_geobox, resp_headers, get_product_from_arg, get_time, \
    img_coords_to_geopoint, bounding_box_to_geom, zoom_factor

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

        start_time = datetime(time.year, time.month, time.day) - timedelta(hours=product.time_zone)
        self._time = [start_time, time + timedelta(days=1)]
        self._style = style

    def needed_bands(self):
        if self._style:
            return self._style.needed_bands
        else:
            return self._product.product.measurements.keys()

    def datasets(self, index, mask=False, all_time=False, point=None):
        if all_time:
            times = self._product.ranges["times"]
            time = [times[0], times[-1] + timedelta(days=1)]
        else:
            time = self._time
        if mask and self._product.pq_name:
            prod_name = self._product.pq_name
        elif mask:
            return []
        else:
            prod_name = self._product.product_name
        query = datacube.api.query.Query(product=prod_name, geopolygon=self._geobox.extent, time=time)
        datasets = index.datasets.search_eager(**query.search_terms)
        datasets.sort(key=lambda d: d.center_time)
        to_load = []
        if point:
            dataset_iter = iter(datasets)
            for dataset in dataset_iter:
                if mask:
                    bbox = dataset.bounds
                    compare_geometry = bounding_box_to_geom(bbox, dataset.crs, self._geobox.crs)
                else:
                    compare_geometry = dataset.extent.to_crs(self._geobox.crs)
                if compare_geometry.contains(point):
                    to_load.append(dataset)
            return to_load
        dataset_iter = iter(datasets)
        date_index = {}
        for dataset in dataset_iter:
            if mask and self._product.pq_manual_merge:
                to_load.append(dataset)
            else:
                if dataset.extent.to_crs(self._geobox.crs).intersects(self._geobox.extent):
                    if dataset.center_time in date_index:
                        date_index[dataset.center_time].append(dataset)
                    else:
                        date_index[dataset.center_time] = [dataset]

        if mask and self._product.pq_manual_merge:
            return to_load
        elif not date_index:
            return None

        date_extents = {}
        for dt, dt_dss in date_index.items():
            geom = None
            for ds in dt_dss:
                if geom is None:
                    geom = ds.extent.to_crs(self._geobox.crs)
                else:
                    geom = geom.union(ds.extent.to_crs(self._geobox.crs))
            if geom.contains(self._geobox.extent):
                return dt_dss
            date_extents[dt] = geom

        dates = date_extents.keys()

        biggest_geom_first = sorted(dates, key=lambda x: [date_extents[x].area, x], reverse=True)

        accum_geom = None
        last_area = 0.0
        for d in biggest_geom_first:
            geom = date_extents[d]
            if accum_geom is None:
                accum_geom = geom
                to_load.extend(date_index[d])
            elif not accum_geom.contains(geom):
                accum_geom = accum_geom.union(geom)
                to_load.extend(date_index[d])
        return to_load


    def data(self, datasets, mask=False, manual_merge=False):
        if mask:
            prod = self._product.pq_product
            measurements = [self._set_resampling(prod.measurements[self._product.pq_band])]
        else:
            prod = self._product.product
            measurements = [self._set_resampling(prod.measurements[name]) for name in self.needed_bands()]
        with datacube.set_options(reproject_threads=1, fast_load=True):
            if manual_merge:
                datas = [ ]
                for i in range(0, len(datasets)):
                    j = i + 1
                    holder = numpy.empty(shape=tuple(), dtype=object)
                    holder[()] = datasets[i:j]
                    sources = xarray.DataArray(holder)
                    datas.append(datacube.Datacube.load_data(sources, self._geobox, measurements))
                merged = None
                if mask:
                    band = self._product.pq_band
                else:
                    for band in self.needed_bands():
                        break
                for d in datas:
                    extent_mask = self._product.extent_mask_func(d, band)
                    dm = d.where(extent_mask)
                    if merged is None:
                        merged = dm
                    else:
                        merged = merged.combine_first(dm)
                if mask:
                    merged = merged.astype('uint8', copy=True)
                    merged[band].attrs = d[band].attrs
                return merged
            else:
                if isinstance(datasets, xarray.DataArray):
                    sources = datasets
                else:
                    holder = numpy.empty(shape=tuple(), dtype=object)
                    holder[()] = datasets
                    sources = xarray.DataArray(holder)
                return datacube.Datacube.load_data(sources, self._geobox, measurements)

    def _set_resampling(self, measurement):
        mc = measurement.copy()
        # mc['resampling_method'] = 'cubic'
        return mc


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
                    permitted_values=service_cfg["published_CRSs"].keys())
    crs = geometry.CRS(crsid)

    # Layers and Styles parameters
    product = get_product_from_arg(args)
    styles = args.get("styles", "").split(",")
    if len(styles) != 1:
        raise WMSException("Multi-layer GetMap requests not supported")
    style_r = styles[0]
    if not style_r:
        style_r = product.default_style
    style = product.style_index.get(style_r)
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

    # Zoom Factor
    zf = zoom_factor(args, crs)

    # Time parameter
    time = get_time(args, product)

    # Tiling.
    tiler = RGBTileGenerator(product, geobox, time, style=style)
    dc = get_cube()
    try:
        datasets = tiler.datasets(dc.index)
        if not datasets:
            body = _write_empty(geobox)
        elif zf < product.min_zoom:
            # Zoomed out to far to properly render data.
            # Construct a polygon which is the union of the extents of the matching datasets.
            extent = None
            extent_crs = None
            for ds in datasets:
                if extent:
                    new_extent = ds.extent
                    if new_extent.crs != extent_crs:
                        new_extent = new_extent.to_crs(extent_crs)
                    extent = extent.union(new_extent)
                else:
                    extent = ds.extent
                    extent_crs = extent.crs
            extent = extent.to_crs(geobox.crs)

            body = _write_polygon(geobox, extent, product.zoom_fill)
        else:
            if style.masks:
                pq_datasets = tiler.datasets(dc.index, mask=True)
                pq_data = tiler.data(pq_datasets,
                                     mask=True,
                                     manual_merge=product.pq_manual_merge)
            else:
                pq_datasets = None
                pq_data = None
            masks = []
            data = tiler.data(datasets)
            for band in style.needed_bands:
                # extent_mask = (data[band] != data[band].attrs['nodata'])
                extent_mask = product.extent_mask_func(data, band)

            if data:
                body = _write_png(data, pq_data, style, extent_mask)
            else:
                body = _write_empty(geobox)
        release_cube(dc)
    except Exception as e:
        release_cube(dc)
        raise e
    return body, 200, resp_headers({"Content-Type": "image/png"})


def _write_png(data, pq_data, style, extent_mask):
    width = data[data.crs.dimensions[1]].size
    height = data[data.crs.dimensions[0]].size

    img_data = style.transform_data(data, pq_data, extent_mask)

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


def int_trim(val, minval, maxval):
    return max(min(val, maxval), minval)


def _write_polygon(geobox, polygon, zoom_fill):
    geobox_ext = geobox.extent
    if geobox_ext.within(polygon):
        data = numpy.full([geobox.width, geobox.height], fill_value=1, dtype="uint8")
    else:
        data = numpy.zeros([geobox.width, geobox.height], dtype="uint8")
        if not geobox_ext.disjoint(polygon):
            intersection = geobox_ext.intersection(polygon)
            if intersection.type == 'Polygon':
                coordinates_list = [ intersection.json["coordinates"] ]
            elif intersection.type == 'MultiPolygon':
                coordinates_list = intersection.json["coordinates"]
            else:
                raise Exception("Unexpected extent/geobox intersection geometry type: %s" % intersection.type)
            for polygon_coords in coordinates_list:
                pixel_coords = [ ~geobox.transform * coords for coords in polygon_coords[0] ]
                rs, cs = skimg_polygon([int_trim(c[1], 0, geobox.height - 1) for c in pixel_coords],
                                       [int_trim(c[0], 0, geobox.width - 1) for c in pixel_coords])
                data[rs, cs] = 1
    with MemoryFile() as memfile:
        with memfile.open(driver='PNG',
                          width=geobox.width,
                          height=geobox.height,
                          count=len(zoom_fill),
                          transform=Affine.identity(),
                          nodata=0,
                          dtype='uint8') as thing:
            for idx, fill in enumerate(zoom_fill, start=1):
                thing.write_band(idx, data * fill)
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
                    permitted_values=service_cfg["published_CRSs"].keys())
    crs = geometry.CRS(crsid)

    # BBox, height and width parameters
    geobox = _get_geobox(args, crs)

    # Time parameter
    time = get_time(args, product)

    # Point coords
    if version == "1.1.1":
        coords = ["x", "y"]
    else:
        coords = ["i", "j"]
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

    # Prepare to extract feature info
    tiler = RGBTileGenerator(product, geobox, time)
    feature_json = {}

    # --- Begin code section requiring datacube.
    dc = get_cube()
    try:
        geo_point = img_coords_to_geopoint(geobox, i, j)
        datasets = tiler.datasets(dc.index, all_time=True,
                                  point=geo_point)
        pq_datasets = tiler.datasets(dc.index, mask=True, all_time=False,
                                     point=geo_point)

        if service_cfg["published_CRSs"][crsid]["geographic"]:
            h_coord = "longitude"
            v_coord = "latitude"
        else:
            h_coord = service_cfg["published_CRSs"][crsid]["horizontal_coord"]
            v_coord = service_cfg["published_CRSs"][crsid]["vertical_coord"]
        isel_kwargs = {
            h_coord: [i],
            v_coord: [j]
        }
        if not datasets:
            pass
        else:
            available_dates = set()
            for d in datasets:
                idx_date = (d.center_time + timedelta(hours=product.time_zone)).date()
                available_dates.add(idx_date)
                if idx_date == time and "lon" not in feature_json:
                    data = tiler.data([d])

                    # Use i,j image coordinates to extract data pixel from dataset, and
                    # convert to lat/long geographic coordinates
                    if service_cfg["published_CRSs"][crsid]["geographic"]:
                        # Geographic coordinate systems (e.g. EPSG:4326/WGS-84) are already in lat/long
                        feature_json["lat"] = data.latitude[j].item()
                        feature_json["lon"] = data.longitude[i].item()
                        pixel_ds = data.isel(**isel_kwargs)
                    else:
                        # Non-geographic coordinate systems need to be projected onto a geographic
                        # coordinate system.  Why not use EPSG:4326?
                        # Extract coordinates in CRS
                        data_x = getattr(data, h_coord)
                        data_y = getattr(data, v_coord)

                        x = data_x[i].item()
                        y = data_y[j].item()
                        pt = geometry.point(x, y, crs)

                        # Project to EPSG:4326
                        crs_geo = geometry.CRS("EPSG:4326")
                        ptg = pt.to_crs(crs_geo)

                        # Capture lat/long coordinates
                        feature_json["lon"], feature_json["lat"] = ptg.coords[0]

                    # Extract data pixel
                    pixel_ds = data.isel(**isel_kwargs)

                    # Get accurate timestamp from dataset
                    feature_json["time"] = d.center_time.strftime("%Y-%m-%d %H:%M:%S UTC")

                    # Collect raw band values for pixel
                    feature_json["bands"] = {}
                    for band in tiler.needed_bands():
                        band_val = pixel_ds[band].item()
                        if band_val == -999:
                            feature_json["bands"][band] = "n/a"
                        else:
                            feature_json["bands"][band] = pixel_ds[band].item()

            my_flags = 0
            pqdi =-1
            for pqd in pq_datasets:
                pqdi += 1
                idx_date = (pqd.center_time + timedelta(hours=product.time_zone)).date()
                if idx_date == time:
                    pq_data = tiler.data([pqd], mask=True)
                    pq_pixel_ds = pq_data.isel(**isel_kwargs)
                    # PQ flags
                    m = product.pq_product.measurements[product.pq_band]
                    flags = pq_pixel_ds[product.pq_band].item()
                    if not flags & ~product.info_mask:
                        my_flags = my_flags | flags
                    else:
                        continue
                    feature_json["flags"] = {}
                    for mk, mv in m["flags_definition"].items():
                        if mk in product.ignore_flags_info:
                            continue
                        bits = mv["bits"]
                        values = mv["values"]
                        if not isinstance(bits, int):
                            continue
                        flag = 1 << bits
                        if my_flags & flag:
                            val = values['1']
                        else:
                            val = values['0']
                        feature_json["flags"][mk] = val

            lads = list(available_dates)
            lads.sort()
            feature_json["data_available_for_dates"] = [d.strftime("%Y-%m-%d") for d in lads]
        release_cube(dc)
    except Exception as e:
        release_cube(dc)
        raise e
    # --- End code section requiring datacube.

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
