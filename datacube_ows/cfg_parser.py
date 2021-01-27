#!/usr/bin/env python3

import click

from datacube_ows import __version__
from datacube_ows.ows_configuration import read_config, OWSConfig, ConfigException, OWSFolder
from datacube import Datacube

@click.command()
@click.argument("paths", nargs=-1)
@click.option("--version", is_flag=True, default=False, help="Show OWS version number and exit")
@click.option("-p", "--parse-only", is_flag=True, default=False, help="Only parse the syntax of the config file - do not validate against database")
@click.option("-f", "--folders", is_flag=True, default=False, help="Print the folder/layer heirarchy(ies) to stdout.")
@click.option("-s", "--styles", is_flag=True, default=False, help="Print the styles for each layer to stdout (format depends on --folders flag).")
def main(version, parse_only, folders, styles, paths):
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

    if parse_only and (folders or styles):
        print("The --folders (-f) and --styles (-s) flags cannot be used in conjunction with the --parser-only (-p) flag.")
        return 1

    if not paths:
        if parse_path(None, parse_only, folders, styles):
            return 0
        else:
            return 1
    all_ok = True
    for path in paths:
        if not parse_path(path, parse_only, folders, styles):
            all_ok = False


    if all_ok:
        return 1
    return 0

def parse_path(path, parse_only, folders, styles):
    try:
        raw_cfg = read_config(path)
        cfg = OWSConfig(refresh=True, cfg=raw_cfg)
        if not parse_only:
            with Datacube() as dc:
                cfg.make_ready(dc)
    except ConfigException as e:
        print("Config exception for path", str(e))
    print("Configuration parsed OK")
    if folders:
        print()
        print("Folder/Layer Hierarchy")
        print("======================")
        print_layers(cfg.layers, styles, depth=0)
        print()
    elif styles:
        print()
        print("Layers and Styles")
        print("=================")
        for lyr in cfg.product_index.values():
            print(lyr.name, f"[{','.join(lyr.product_names)}]")
            print_styles(lyr)
        print()

def print_layers(layers, styles, depth):
    for lyr in layers:
        if isinstance(lyr, OWSFolder):
            indent(depth)
            print("*", lyr.title)
            print_layers(lyr.child_layers, styles, depth+1)
        else:
            indent(depth)
            print(lyr.name, f"[{','.join(lyr.product_names)}]")
            if styles:
                print_styles(lyr, depth)


def print_styles(lyr, depth=0):
    for styl in lyr.styles:
        indent(0, for_styles=True)
        print(".", styl.name)


def indent(depth, for_styles=False):
    for i in range(depth):
        print("  ", end="")
    if for_styles:
        print("      ", end="")
