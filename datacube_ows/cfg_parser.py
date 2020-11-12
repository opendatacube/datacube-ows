#!/usr/bin/env python3

import click

from datacube_ows import __version__
from datacube_ows.ows_configuration import read_config, OWSConfig, ConfigException
from datacube import Datacube

@click.command()
@click.argument("paths", nargs=-1)
@click.option("--version", is_flag=True, default=False, help="Show OWS version number and exit")
@click.option("-p", "--parse-only", is_flag=True, default=False, help="Only parse the syntax of the config file - do not validate against database")
def main(version, parse_only, paths):
    #layers, blocking,
    #     merge_only, summary,
    #     schema, views, role, version,
    #     product, multiproduct, calculate_extent):
    """Test configuration files

    Valid invocations:

    Uses the DATACUBE_OWS_CFG environment variable to find the OWS config file.
    """
    # --version
    if version:
        print("Open Data Cube Open Web Services (datacube-ows) version",
              __version__
               )
        return 0

    if not paths:
        if parse_path(None, parse_only):
            return 0
        else:
            return 1
    all_ok = True
    for path in paths:
        if not parse_path(path, parse_only):
            all_ok = False


    if all_ok:
        return 1
    return 0

def parse_path(path, parse_only):
    try:
        raw_cfg = read_config(path)
        cfg = OWSConfig(refresh=True, cfg=raw_cfg)
        if not parse_only:
            with Datacube() as dc:
                cfg.make_ready(dc)
    except ConfigException as e:
        print("Config exception for path", str(e))
