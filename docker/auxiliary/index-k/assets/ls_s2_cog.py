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
from botocore.handlers import disable_signing
import datacube
from datacube.scripts.dataset import create_dataset, parse_match_rules_options
from datacube.utils import changes
from ruamel.yaml import YAML

def format_obj_key(obj_key):
    obj_key ='/'.join(obj_key.split("/")[:-1])
    return obj_key


def get_s3_url(bucket_name, obj_key):
    return 's3://{bucket_name}/{obj_key}'.format(
        bucket_name=bucket_name, obj_key=obj_key)


def get_metadata_docs(bucket_name, prefix, suffix, unsafe):
    s3 = boto3.resource('s3')
    s3.meta.client.meta.events.register('choose-signer.s3.*', disable_signing)
    bucket = s3.Bucket(bucket_name)
    logging.info("Bucket : %s prefix: %s ", bucket_name, str(prefix))
    safety = 'safe' if not unsafe else 'unsafe'
    for obj in bucket.objects.filter(Prefix = str(prefix)):
        if obj.key.endswith(suffix):
            obj_key = obj.key
            logging.info("Processing %s", obj_key)
            raw_string = obj.get()['Body'].read().decode('utf8')
            yaml = YAML(typ=safety, pure = True)
            yaml.default_flow_style = False
            data = yaml.load(raw_string)
            yield obj_key,data
            
            
def make_rules(index):
    all_product_names = [prod.name for prod in index.products.get_all()]
    rules = parse_match_rules_options(index, None, all_product_names, True)
    return rules


def archive_dataset(doc, uri, rules, index, sources_policy):
    def get_ids(dataset):
        ds = index.datasets.get(dataset.id, include_sources=True)
        for source in ds.sources.values():
            yield source.id
        yield dataset.id


    dataset = create_dataset(doc, uri, rules)
    index.datasets.archive(get_ids(dataset))
    logging.info("Archiving %s and all sources of %s", dataset.id, dataset.id)


def add_dataset(doc, uri, rules, index, sources_policy):
    dataset = create_dataset(doc, uri, rules)

    try:
        index.datasets.add(dataset, sources_policy=sources_policy) # Source policy to be checked in sentinel 2 datase types 
    except changes.DocumentMismatchError as e:
        index.datasets.update(dataset, {tuple(): changes.allow_any})

    logging.info("Indexing %s", uri)
    return uri


def iterate_datasets(bucket_name, config, prefix, suffix, func, unsafe, sources_policy):
    dc=datacube.Datacube(config=config)
    index = dc.index
    rules = make_rules(index)
    
    for metadata_path,metadata_doc in get_metadata_docs(bucket_name, prefix, suffix, unsafe):
        uri= get_s3_url(bucket_name, metadata_path)
        func(metadata_doc, uri, rules, index, sources_policy)


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

