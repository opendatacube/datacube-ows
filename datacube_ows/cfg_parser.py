#!/usr/bin/env python3

import json
import sys

import click
from datacube import Datacube
from deepdiff import DeepDiff

from datacube_ows import __version__
from datacube_ows.ows_configuration import (ConfigException, OWSConfig,
                                            OWSFolder, read_config)


@click.command()
@click.argument("paths", nargs=-1)
@click.option(
    "--version", is_flag=True, default=False, help="Show OWS version number and exit"
)
@click.option(
    "-p",
    "--parse-only",
    is_flag=True,
    default=False,
    help="Only parse the syntax of the config file - do not validate against database",
)
@click.option(
    "-f",
    "--folders",
    is_flag=True,
    default=False,
    help="Print the folder/layer heirarchy(ies) to stdout.",
)
@click.option(
    "-s",
    "--styles",
    is_flag=True,
    default=False,
    help="Print the styles for each layer to stdout (format depends on --folders flag).",
)
@click.option(
    "-i",
    "--input-file",
    default=False,
    help="Provide a file path for the input inventory json file to be compared with config file",
)
@click.option(
    "-o",
    "--output-file",
    default=False,
    help="Provide an output file name with extension .json",
)
def main(version, parse_only, folders, styles, input_file, output_file, paths):
    """Test configuration files

    Valid invocations:

    Uses the DATACUBE_OWS_CFG environment variable to find the OWS config file.
    """
    # --version
    if version:
        print("Open Data Cube Open Web Services (datacube-ows) version", __version__)
        return 0

    if parse_only and (folders or styles):
        print(
            "The --folders (-f) and --styles (-s) flags cannot be used in conjunction with the --parser-only (-p) flag."
        )
        sys.exit(1)

    all_ok = True
    if not paths:
        if parse_path(None, parse_only, folders, styles, input_file, output_file):
            return 0
        else:
            sys.exit(1)
    for path in paths:
        if not parse_path(path, parse_only, folders, styles, input_file, output_file):
            all_ok = False

    if not all_ok:
        sys.exit(1)
    return 0


def parse_path(path, parse_only, folders, styles, input_file, output_file):
    try:
        raw_cfg = read_config(path)
        cfg = OWSConfig(refresh=True, cfg=raw_cfg)
        if not parse_only:
            with Datacube() as dc:
                cfg.make_ready(dc)
    except ConfigException as e:
        print("Config exception for path", str(e))
        return False
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
    if input_file or output_file:
        layers_report(cfg.product_index, input_file, output_file)
    return True


def layers_report(config_values, input_file, output_file):
    report = {"total_layers_count": len(config_values.values()), "layers": []}
    for lyr in config_values.values():
        layer = {
            "product": list(lyr.product_names),
            "styles_count": len(lyr.styles),
            "styles_list": [styl.name for styl in lyr.styles],
        }
        report["layers"].append(layer)
    if input_file:
        with open(input_file) as f:
            input_file_data = json.load(f)
        ddiff = DeepDiff(input_file_data, report, ignore_order=True)
        if len(ddiff) == 0:
            return True
        else:
            print(ddiff)
            sys.exit(1)
    if output_file:
        with open(output_file, "w") as reportfile:
            json.dump(report, reportfile, indent=4)
        return True


def print_layers(layers, styles, depth):
    for lyr in layers:
        if isinstance(lyr, OWSFolder):
            indent(depth)
            print("*", lyr.title)
            print_layers(lyr.child_layers, styles, depth + 1)
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
