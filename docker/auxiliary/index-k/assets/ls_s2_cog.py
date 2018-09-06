
# coding: utf-8
from xml.etree import ElementTree
from pathlib import Path
import os
from osgeo import osr
import dateutil
from dateutil import parser
from datetime import timedelta
import uuid
import yaml
import logging
import click
import re
import boto3
import datacube
from datacube.index.hl import Doc2Dataset
from datacube.utils import changes
from ruamel.yaml import YAML

from multiprocessing import Process, current_process, Queue, Manager, cpu_count
from time import sleep, time

GUARDIAN = "GUARDIAN_QUEUE_EMPTY"
AWS_PDS_TXT_SUFFIX = "MTL.txt"


MTL_PAIRS_RE = re.compile(r'(\w+)\s=\s(.*)')

bands_ls8 = [('1', 'coastal_aerosol'),
             ('2', 'blue'),
             ('3', 'green'),
             ('4', 'red'),
             ('5', 'nir'),
             ('6', 'swir1'),
             ('7', 'swir2'),
             ('8', 'panchromatic'),
             ('9', 'cirrus'),
             ('10', 'lwir1'),
             ('11', 'lwir2'),
             ('QUALITY', 'quality')]

bands_ls7 = [('1', 'blue'),
             ('2', 'green'),
             ('3', 'red'),
             ('4', 'nir'),
             ('5', 'swir1'),
             ('7', 'swir2'),
             ('QUALITY', 'quality')]


def _parse_value(s):
    s = s.strip('"')
    for parser in [int, float]:
        try:
            return parser(s)
        except ValueError:
            pass
    return s


def _parse_group(lines):
    tree = {}
    for line in lines:
        match = MTL_PAIRS_RE.findall(line)
        if match:
            key, value = match[0]
            if key == 'GROUP':
                tree[value] = _parse_group(lines)
            elif key == 'END_GROUP':
                break
            else:
                tree[key] = _parse_value(value)
    return tree


def get_geo_ref_points(info):
    return {
        'ul': {'x': info['CORNER_UL_PROJECTION_X_PRODUCT'], 'y': info['CORNER_UL_PROJECTION_Y_PRODUCT']},
        'ur': {'x': info['CORNER_UR_PROJECTION_X_PRODUCT'], 'y': info['CORNER_UR_PROJECTION_Y_PRODUCT']},
        'll': {'x': info['CORNER_LL_PROJECTION_X_PRODUCT'], 'y': info['CORNER_LL_PROJECTION_Y_PRODUCT']},
        'lr': {'x': info['CORNER_LR_PROJECTION_X_PRODUCT'], 'y': info['CORNER_LR_PROJECTION_Y_PRODUCT']},
    }


def get_coords(geo_ref_points, spatial_ref):
    t = osr.CoordinateTransformation(spatial_ref, spatial_ref.CloneGeogCS())

    def transform(p):
        lon, lat, z = t.TransformPoint(p['x'], p['y'])
        return {'lon': lon, 'lat': lat}

    return {key: transform(p) for key, p in geo_ref_points.items()}


def satellite_ref(sat):
    """
    To load the band_names for referencing either LANDSAT8 or LANDSAT7 bands
    """
    if sat == 'LANDSAT_8':
        sat_img = bands_ls8
    elif sat == 'LANDSAT_7' or sat == 'LANDSAT_5':
        sat_img = bands_ls7
    else:
        raise ValueError('Satellite data Not Supported')
    return sat_img


def format_obj_key(obj_key):
    obj_key = '/'.join(obj_key.split("/")[:-1])
    return obj_key


def get_s3_url(bucket_name, obj_key):
    return 'http://{bucket_name}.s3.amazonaws.com/{obj_key}'.format(
        bucket_name=bucket_name, obj_key=obj_key)


def absolutify_paths(doc, bucket_name, obj_key):
    objt_key = format_obj_key(obj_key)
    for band in doc['image']['bands'].values():
        band['path'] = get_s3_url(bucket_name, objt_key + '/'+band['path'])
    return doc


def make_metadata_doc(mtl_data, bucket_name, object_key):
    mtl_product_info = mtl_data['PRODUCT_METADATA']
    mtl_metadata_info = mtl_data['METADATA_FILE_INFO']
    satellite = mtl_product_info['SPACECRAFT_ID']
    instrument = mtl_product_info['SENSOR_ID']
    acquisition_date = mtl_product_info['DATE_ACQUIRED']
    scene_center_time = mtl_product_info['SCENE_CENTER_TIME']
    level = mtl_product_info['DATA_TYPE']
    product_type = 'L1TP'
    sensing_time = acquisition_date + ' ' + scene_center_time
    cs_code = 32600 + mtl_data['PROJECTION_PARAMETERS']['UTM_ZONE']
    label = mtl_metadata_info['LANDSAT_SCENE_ID']
    spatial_ref = osr.SpatialReference()
    spatial_ref.ImportFromEPSG(cs_code)
    geo_ref_points = get_geo_ref_points(mtl_product_info)
    coordinates = get_coords(geo_ref_points, spatial_ref)
    bands = satellite_ref(satellite)
    doc = {
        'id': str(uuid.uuid5(uuid.NAMESPACE_URL, get_s3_url(bucket_name, object_key))),
        'processing_level': level,
        'product_type': product_type,
        'creation_dt': str(acquisition_date),
        'label': label,
        'platform': {'code': satellite},
        'instrument': {'name': instrument},
        'extent': {
            'from_dt': sensing_time,
            'to_dt': sensing_time,
            'center_dt': sensing_time,
            'coord': coordinates,
                  },
        'format': {'name': 'GeoTiff'},
        'grid_spatial': {
            'projection': {
                'geo_ref_points': geo_ref_points,
                'spatial_reference': 'EPSG:%s' % cs_code,
                            }
                        },
        'image': {
            'bands': {
                band[1]: {
                    'path': mtl_product_info['FILE_NAME_BAND_' + band[0]],
                    'layer': 1,
                } for band in bands
            }
        },
        'lineage': {'source_datasets': {}},
    }
    doc = absolutify_paths(doc, bucket_name, object_key)
    return doc


def format_obj_key(obj_key):
    obj_key ='/'.join(obj_key.split("/")[:-1])
    return obj_key


def get_s3_url(bucket_name, obj_key):
    return 's3://{bucket_name}/{obj_key}'.format(
        bucket_name=bucket_name, obj_key=obj_key)

def archive_dataset(doc, uri, index, sources_policy):
    def get_ids(dataset):
        ds = index.datasets.get(dataset.id, include_sources=True)
        for source in ds.sources.values():
            yield source.id
        yield dataset.id


    resolver = Doc2Dataset(index)
    dataset, err  = resolver(doc, uri)
    index.datasets.archive(get_ids(dataset))
    logging.info("Archiving %s and all sources of %s", dataset.id, dataset.id)


def add_dataset(doc, uri, index, sources_policy):
    logging.info("Indexing %s", uri)
    resolver = Doc2Dataset(index)
    dataset, err  = resolver(doc, uri)
    if err is not None:
        logging.error("%s", err)
    try:
        index.datasets.add(dataset, sources_policy=sources_policy) # Source policy to be checked in sentinel 2 datase types
    except changes.DocumentMismatchError as e:
        index.datasets.update(dataset, {tuple(): changes.allow_any})
    except Exception as e:
        logging.error("Unhandled exception %s", e)

    return uri


def worker(config, bucket_name, prefix, suffix, func, unsafe, sources_policy, queue):
    dc=datacube.Datacube(config=config)
    index = dc.index
    s3 = boto3.resource("s3")
    safety = 'safe' if not unsafe else 'unsafe'

    while True:
        key = queue.get(timeout=60)
        if key == GUARDIAN:
            break
        logging.info("Processing %s %s", key, current_process())
        obj = s3.Object(bucket_name, key).get(ResponseCacheControl='no-cache')
        raw = obj['Body'].read()
        if suffix == AWS_PDS_TXT_SUFFIX:
            # Attempt to process text document
            raw_string = raw.decode('utf8')
            txt_doc = _parse_group(iter(raw_string.split("\n")))['L1_METADATA_FILE']
            data = make_metadata_doc(txt_doc, bucket_name, key)
        else:
            yaml = YAML(typ=safety, pure=False)
            yaml.default_flow_style = False
            data = yaml.load(raw)
        uri= get_s3_url(bucket_name, key)
        logging.info("calling %s", func)
        func(data, uri, index, sources_policy)
        queue.task_done()


def iterate_datasets(bucket_name, config, prefix, suffix, func, unsafe, sources_policy):
    manager = Manager()
    queue = manager.Queue()

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    logging.info("Bucket : %s prefix: %s ", bucket_name, str(prefix))
    safety = 'safe' if not unsafe else 'unsafe'
    worker_count = cpu_count() * 2

    processess = []
    for i in range(worker_count):
        proc = Process(target=worker, args=(config, bucket_name, prefix, suffix, func, unsafe, sources_policy, queue,))
        processess.append(proc)
        proc.start()

    for obj in bucket.objects.filter(Prefix = str(prefix)):
        if (obj.key.endswith(suffix)):
            queue.put(obj.key)

    queue.join()

    for i in range(worker_count):
        queue.put(GUARDIAN)

    for proc in processess:
        proc.join()



@click.command(help= "Enter Bucket name. Optional to enter configuration file to access a different database")
@click.argument('bucket_name')
@click.option('--config','-c',help=" Pass the configuration file to access the database",
        type=click.Path(exists=True))
@click.option('--prefix', '-p', help="Pass the prefix of the object to the bucket")
@click.option('--suffix', '-s', default=".yaml", help="Defines the suffix of the metadata_docs that will be used to load datasets. For AWS PDS bucket use MTL.txt")
@click.option('--archive', is_flag=True, help="If true, datasets found in the specified bucket and prefix will be archived")
@click.option('--unsafe', is_flag=True, help="If true, YAML will be parsed unsafely. Only use on trusted datasets. Only valid if suffix is yaml")
@click.option('--sources_policy', default="verify", help="verify, ensure, skip")
def main(bucket_name, config, prefix, suffix, archive, unsafe, sources_policy):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
    action = archive_dataset if archive else add_dataset
    iterate_datasets(bucket_name, config, prefix, suffix, action, unsafe, sources_policy)
   

if __name__ == "__main__":
    main()


