
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
from time import sleep

GUARDIAN = "GUARDIAN_QUEUE_EMPTY"

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
    resolver = Doc2Dataset(index)
    dataset, err  = resolver(doc, uri)
    try:
        index.datasets.add(dataset, sources_policy=sources_policy) # Source policy to be checked in sentinel 2 datase types
    except changes.DocumentMismatchError as e:
        index.datasets.update(dataset, {tuple(): changes.allow_any})
    except Exception as e:
        logging.error("Unhandled exception %s", e)

    logging.info("Indexing %s", uri)
    return uri

def worker(config, bucket_name, prefix, suffix, func, unsafe, sources_policy, queue):
    dc=datacube.Datacube(config=config)
    index = dc.index
    s3 = boto3.resource("s3")
    safety = 'safe' if not unsafe else 'unsafe'

    while True:
        try:
            key = queue.get_nowait()
            if key == GUARDIAN:
                break
            logging.info("Processing %s %s", key, current_process())
            obj = s3.Object(bucket_name, key).get(ResponseCacheControl='no-cache')
            raw_string = obj['Body'].read().decode('utf8')
            yaml = YAML(typ=safety, pure=True)
            yaml.default_flow_style = False
            data = yaml.load(raw_string)
            uri= get_s3_url(bucket_name, key)
            logging.info("calling %s", func)
            func(data, uri, index, sources_policy)
        except:
            sleep(0)
            pass


def iterate_datasets(bucket_name, config, prefix, suffix, func, unsafe, sources_policy):
    manager = Manager()
    queue = manager.Queue()

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(bucket_name)
    logging.info("Bucket : %s prefix: %s ", bucket_name, str(prefix))
    safety = 'safe' if not unsafe else 'unsafe'

    processess = []
    for i in range(cpu_count()):
        proc = Process(target=worker, args=(config, bucket_name, prefix, suffix, func, unsafe, sources_policy, queue,))
        processess.append(proc)
        proc.start()

    for obj in bucket.objects.filter(Prefix = str(prefix)):
        if (obj.key.endswith(suffix)):
            queue.put(obj.key)

    for i in range(cpu_count()):
        queue.put(GUARDIAN)

    for proc in processess:
        proc.join()



@click.command(help= "Enter Bucket name. Optional to enter configuration file to access a different database")
@click.argument('bucket_name')
@click.option('--config','-c',help=" Pass the configuration file to access the database",
        type=click.Path(exists=True))
@click.option('--prefix', '-p', help="Pass the prefix of the object to the bucket")
@click.option('--suffix', '-s', default=".yaml", help="Defines the suffix of the metadata_docs that will be used to load datasets")
@click.option('--archive', is_flag=True, help="If true, datasets found in the specified bucket and prefix will be archived")
@click.option('--unsafe', is_flag=True, help="If true, YAML will be parsed unsafely. Only use on trusted datasets.")
@click.option('--sources_policy', default="verify", help="verify, ensure, skip")
def main(bucket_name, config, prefix, suffix, archive, unsafe, sources_policy):
    logging.basicConfig(format='%(asctime)s %(levelname)s %(message)s', level=logging.INFO)
    action = archive_dataset if archive else add_dataset
    iterate_datasets(bucket_name, config, prefix, suffix, action, unsafe, sources_policy)
   

if __name__ == "__main__":
    main()


