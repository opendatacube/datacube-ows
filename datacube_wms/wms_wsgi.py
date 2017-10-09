from __future__ import absolute_import, division, print_function

try:
    from urlparse import parse_qs
except ImportError:
    from urllib.parse import parse_qs

# travis can only get earlier version of rasterio which doesn't have MemoryFile, so
# - tell pylint to ingnore inport error
# - catch ImportError so pytest doctest don't fall over
try:
    from rasterio.io import MemoryFile  # pylint: disable=import-error
except ImportError:
    MemoryFile = None

import numpy
import pandas
import xarray
from affine import Affine
from datetime import datetime, timedelta

import datacube
import datacube.api.query
from datacube.storage.masking import mask_valid_data as mask_invalid_data, make_mask
from datacube.utils import geometry


INDEX_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <title>Map</title>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <link rel="shortcut icon" type="image/x-icon" href="docs/images/favicon.ico" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.0.2/dist/leaflet.css" />
    <link rel="stylesheet" type="text/css" href="https://cdnjs.cloudflare.com/ajax/libs/vis/4.18.1/vis-timeline-graph2d.min.css" />
    <script src="https://unpkg.com/leaflet@1.0.2/dist/leaflet.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/vis/4.18.1/vis.min.js"></script>
</head>
<body>

<div id="mapid" style="width: 1200px; height: 800px;"></div>
<div id="timeline" style="width: 1200px; height: 200px;"></div>
<script>
    function formatDate(date) {{
      return date.getFullYear() + "-" + (date.getMonth()+1) + "-" + date.getDate();
    }};
    function formatDateRange(start, end) {{
        return formatDate(start) + "/" + formatDate(end);
    }};

    var start = new Date(2006, 1, 1);
    var end = new Date(2006, 3, 1);

    var mymap = L.map('mapid').setView([-35.0, 148.75], 12);
    mbUrl = 'http://{{s}}.tile.osm.org/{{z}}/{{x}}/{{y}}.png'; 
    osm = L.tileLayer(mbUrl, {{id: 'mapbox.light', attribution: ""}});
    cube = L.tileLayer.wms(
        "{wms_url}",
        {{
            minZoom: 6,
            maxZoom: 19,
            layers: "ls5_sr_rgb",
            format: 'image/png',
            transparent: true,
            attribution: "Teh Cube",
            time: formatDateRange(start, end)
        }}
    );
    cube_cir = L.tileLayer.wms(
        "{wms_url}",
        {{
            minZoom: 6,
            maxZoom: 19,
            layers: "ls8_sr_cir",
            format: 'image/png',
            transparent: true,
            attribution: "Teh Cube",
            time: formatDateRange(start, end)
        }}
    );
    cube_false = L.tileLayer.wms(
        "{wms_url}",
        {{
            minZoom: 6,
            maxZoom: 19,
            layers: "ls8_sr_false",
            format: 'image/png',
            transparent: true,
            attribution: "Teh Cube",
            time: formatDateRange(start, end)
        }}
    );
    cube.addTo(mymap);
    L.control.layers({{'OSM': osm, 'RGB': cube}}, {{}}).addTo(mymap);

    items = new vis.DataSet([{{id: 1, content: 'time', start: start, end: end}}]);
    function onUpdate(event, properties, senderId) {{
        start = properties.data[0].start;
        end = properties.data[0].end;
        cube.setParams({{time: formatDateRange(start, end)}});
    }};
    items.on('update', onUpdate);

    options = {{
        editable: {{
            updateTime: true
        }},
        start: new Date(2006, 1, 1),
        end: new Date()
    }};
    var timeline = new vis.Timeline(document.getElementById('timeline'), items, options);
</script>
</body>
</html>
"""


GET_CAPS_TEMPLATE = """<?xml version='1.0' encoding="UTF-8" standalone="no" ?>
<!DOCTYPE WMT_MS_Capabilities SYSTEM "http://schemas.opengis.net/wms/1.1.1/WMS_MS_Capabilities.dtd"
 [
 <!ELEMENT VendorSpecificCapabilities EMPTY>
 ]>
<WMT_MS_Capabilities version="1.1.1"
        xmlns:xlink="http://www.w3.org/1999/xlink">
<Service>
  <Name>OGC:WMS</Name>
  <Title>WMS server for Datacube</Title>
  <OnlineResource xlink:href="{location}"></OnlineResource>
</Service>
<Capability>
  <Request>
    <GetCapabilities>
      <Format>application/vnd.ogc.wms_xml</Format>
      <DCPType>
        <HTTP>
          <Get><OnlineResource xlink:href="{location}"></OnlineResource></Get>
        </HTTP>
      </DCPType>
    </GetCapabilities>
    <GetMap>
      <Format>image/png</Format>
      <DCPType>
        <HTTP>
          <Get><OnlineResource xlink:href="{location}"></OnlineResource></Get>
        </HTTP>
      </DCPType>
    </GetMap>
  </Request>
  <Exception>
    <Format>application/vnd.ogc.se_blank</Format>
  </Exception>
  <VendorSpecificCapabilities></VendorSpecificCapabilities>
  <UserDefinedSymbolization SupportSLD="1" UserLayer="0" UserStyle="1" RemoteWFS="0"/>
  <Layer>
    <Title>WMS server for Datacube</Title>
    <SRS>EPSG:3577</SRS>
    <SRS>EPSG:3857</SRS>
    <SRS>EPSG:4326</SRS>
    {layers}
  </Layer>
</Capability>
</WMT_MS_Capabilities>
"""

LAYER_TEMPLATE = """
<Layer>
  <Name>{name}</Name>
  <Title>{title}</Title>
  <Abstract>{abstract}</Abstract>
  {metadata}
</Layer>
"""

LAYER_SPEC = {
    'ls5_sr_rgb': {
        'product': 'ls5_nbar_albers',
        'mask': 'ls5_pq_albers',
        'mask_band': 'pixelquality',
        'mask_flags': dict(
            cloud_acca='no_cloud',
            cloud_fmask='no_cloud',
        ),
        #'mask_band': 'cfmask',
        #'mask_flags': {'cfmask': 'clear'},
        'bands': ('red', 'green', 'blue'),
        'extents': geometry.box(60, 0, 100, 40, crs=geometry.CRS('EPSG:4326')),
        'time': {
            'start': datetime(2006, 1, 1),
            'end': datetime(2006, 3, 1),
            'period': timedelta(days=0)
        }
    },
}


class TileGenerator(object):
    def __init__(self, **kwargs):
        pass

    def datasets(self, index):
        pass

    def data(self, datasets):
        pass


class RGBTileGenerator(TileGenerator):
    def __init__(self, config, geobox, time, **kwargs):
        super(RGBTileGenerator, self).__init__(**kwargs)
        self._product = config['product']
        self._bands = config['bands']
        self._geobox = geobox
        self._time = time

    def datasets(self, index):
        return _get_datasets(index, self._geobox, self._product, self._time)

    def data(self, datasets):
        holder = numpy.empty(shape=tuple(), dtype=object)
        holder[()] = datasets
        sources = xarray.DataArray(holder)

        prod = datasets[0].type
        measurements = [self._set_resampling(prod.measurements[name]) for name in self._bands]
        with datacube.set_options(reproject_threads=1, fast_load=True):
            return datacube.Datacube.load_data(sources, self._geobox, measurements)

    def _set_resampling(self, measurement):
        mc = measurement.copy()
        # mc['resampling_method'] = 'cubic'
        return mc


class LatestCloudFree(TileGenerator):
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

            copy_mask = (~fused_mask) & mask if fused_mask is not None else mask
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


def application(environ, start_response):
    with datacube.Datacube(app="WMS") as dc:
        args = _parse_query(environ['QUERY_STRING'])

        if args.get('request') == 'GetMap':
            return get_map(dc, args, start_response)

        if args.get('request') == 'GetCapabilities':
            return get_capabilities(dc, args, environ, start_response)

        data = INDEX_TEMPLATE.format(wms_url=_script_url(environ)).encode('utf-8')

        start_response("200 OK", [
            ("Content-Type", "text/html"),
            ("Content-Length", str(len(data)))
        ])
        return iter([data])


def _parse_query(qs):
    return {key.lower(): (val[0] if len(val) == 1 else val) for key, val in parse_qs(qs).items()}


def _script_url(environ):
    return 'http://'+environ['HTTP_HOST']+environ['SCRIPT_NAME']


def get_capabilities(dc, args, environ, start_response):
    layers = ""
    for name, layer in LAYER_SPEC.items():
        product = dc.index.products.get_by_name(layer['product'])
        if not product:
            continue
        layers += LAYER_TEMPLATE.format(name=name,
                                        title=name,
                                        abstract=product.definition['description'],
                                        metadata=get_layer_metadata(layer, product))

    data = GET_CAPS_TEMPLATE.format(location=_script_url(environ), layers=layers).encode('utf-8')
    start_response("200 OK", [
        ("Access-Control-Allow-Origin", "*"),
        ("Content-Type", "application/xml"),
        ("Content-Length", str(len(data)))
    ])
    return iter([data])


def get_layer_metadata(layer, product):
    metadata = """
<LatLonBoundingBox minx="60" miny="0" maxx="100" maxy="40"></LatLonBoundingBox>
<BoundingBox CRS="EPSG:4326" minx="60" miny="0" maxx="100" maxy="40"/>
<Dimension name="time" units="ISO8601"/>
<Extent name="time" default="2015-01-01">2013-01-01/2017-01-01/P1M</Extent>
    """
    return metadata


def get_map(dc, args, start_response):
    geobox = _get_geobox(args)
    time = args.get('time', '2015-01-01/2015-02-01').split('/')
    if len(time) == 1:
        time = pandas.to_datetime(time[0])
        time = [time - timedelta(days=30), time]

    layer_config = LAYER_SPEC[args['layers']]
    #tiler = RGBTileGenerator(layer_config, geobox, time)
    tiler = LatestCloudFree(layer_config['product'],
                            layer_config['bands'],
                            layer_config['mask'],
                            layer_config['mask_band'],
                            layer_config['mask_flags'],
                            geobox, time)
    datasets = tiler.datasets(dc.index)
    data = tiler.data(datasets)

    if data:
        body = _write_png(data)
    else:
        body = _write_empty()
    start_response("200 OK", [
        ("Access-Control-Allow-Origin", "*"),
        ("Content-Type", "image/png"),
        ("Content-Length", str(len(body)))
    ])
    return iter([body])


def _get_geobox(args):
    width = int(args['width'])
    height = int(args['height'])
    minx, miny, maxx, maxy = map(float, args['bbox'].split(','))
    crs = geometry.CRS(args['srs'])

    affine = Affine.translation(minx, miny) * Affine.scale((maxx - minx) / width, (maxy - miny) / height)
    return geometry.GeoBox(width, height, affine, crs)


def _write_png(data):
    width = data[data.crs.dimensions[1]].size
    height = data[data.crs.dimensions[0]].size

    with MemoryFile() as memfile:
        with memfile.open(driver='PNG',
                          width=width,
                          height=height,
                          count=len(data.data_vars),
                          transform=Affine.identity(),
                          nodata=0,
                          dtype='uint8') as thing:
            for idx, band in enumerate(data.data_vars, start=1):
                scaled = numpy.clip(data[band].values[::-1] / 12.0, 0, 255).astype('uint8')
                thing.write_band(idx, scaled)
        return memfile.read()


def _write_empty():
    width, height = 1, 1
    with MemoryFile() as memfile:
        with memfile.open(driver='PNG',
                          width=width,
                          height=height,
                          count=1,
                          transform=Affine.identity(),
                          nodata=0,
                          dtype='uint8') as thing:
            thing.write_band(1, numpy.array([[0]], dtype='uint8'))
            # pass
        return memfile.read()


if __name__ == '__main__':
    from werkzeug.serving import run_simple  # pylint: disable=import-error, wrong-import-position
    run_simple('0.0.0.0', 8888, application, use_debugger=False, use_reloader=True)
