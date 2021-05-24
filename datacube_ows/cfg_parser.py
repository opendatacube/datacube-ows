#!/usr/bin/env python3
# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import json
import os
import sys

import click
from datacube import Datacube
from deepdiff import DeepDiff

from babel.messages.pofile import write_po

from datacube_ows import __version__
from datacube_ows.ows_configuration import (ConfigException, OWSConfig,
                                            OWSFolder, read_config)


@click.group()
@click.option(
    "--version", is_flag=True, default=False, help="Show OWS version number and exit"
)
def main(version):
    # --version
    if version:
        click.echo("Open Data Cube Open Web Services (datacube-ows) version", __version__)
        return 0


@main.command()
@click.argument("paths", nargs=-1)
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
    help="Provide an output inventory file name with extension .json",
)
def check(parse_only, folders, styles, input_file, output_file, paths):
    """Check configuration files

    Takes a list of configuration specifications which are each loaded and validated in turn,
    with each specification being interpreted as per the $DATACUBE_OWS_CFG environment variable.

    If no specification is provided, the $DATACUBE_OWS_CFG environment variable is used.
    """
    if parse_only and (folders or styles):
        click.echo(
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
        click.echo("Config exception for path", str(e))
        return False
    click.echo("Configuration parsed OK")
    click.echo("Configured message file location:", cfg.msg_file_name)
    click.echo("Configured translations directory location:", cfg.translations_dir)
    if folders:
        click.echo()
        click.echo("Folder/Layer Hierarchy")
        click.echo("======================")
        print_layers(cfg.layers, styles, depth=0)
        click.echo()
    elif styles:
        click.echo()
        click.echo("Layers and Styles")
        click.echo("=================")
        for lyr in cfg.product_index.values():
            click.echo(lyr.name, f"[{','.join(lyr.product_names)}]")
            print_styles(lyr)
        click.echo()
    if input_file or output_file:
        layers_report(cfg.product_index, input_file, output_file)
    return True


@main.command()
@click.option(
    "-c",
    "--cfg-only",
    is_flag=True,
    default=False,
    help="Read metadata from config only - ignore configured metadata message file.",
)
@click.option(
    "-m",
    "--msg-file",
    default="messages.po",
    help="Write to a message file with the translatable metadata from the configuration. (Defaults to 'messages.po')"
)
@click.argument("path", nargs=-1)
def extract(path, cfg_only, msg_file):
    """Extract metadata from existing configuration into a message file template.

    Takes a configuration specification which is loaded as per the $DATACUBE_OWS_CFG environment variable.

    If no specification is provided, the $DATACUBE_OWS_CFG environment variable is used.
    """
    try:
        raw_cfg = read_config(path)
        cfg = OWSConfig(refresh=True, cfg=raw_cfg, ignore_msgfile=cfg_only)
        with Datacube() as dc:
            cfg.make_ready(dc)
    except ConfigException as e:
        click.echo("Config exception for path", str(e))
        return False
    click.echo("Configuration parsed OK")
    click.echo("Configured message file location:", cfg.msg_file_name)
    click.echo("Configured translations directory location:", cfg.translations_dir)
    write_msg_file(msg_file, cfg)
    click.echo(f"Message file {msg_file} written")


@click.option(
    "-t",
    "--translations",
    default=False,
    help="Update the configured translations directory with fresh translation-templates for the listed languages, based on the configured message file. "
        + "Use a comma separated list of language codes or 'all'."
)
def will_be_translations(translations):
    if translations:
        if not cfg.translations_dir:
            click.echo("No translations directory location configured")
            return False
        if translations == "all":
            translations = cfg.locales
        else:
            locs = []
            for locale in translations.split(","):
                if locale in cfg.locales:
                    locs.append(locale)
                else:
                    click.echo("Language " + locale + " not supported.")
            if not locs:
                click.echo("No supported languages listed in locales. Supported languages are:", ",".join(cfg.locales))
                return False
            translations = locs

        translations_dir = cfg.translations_dir
        for locale in translations:
            click.echo("Creating template for language", locale)
            os.system(f"pybabel init -i {cfg.msg_file_name} -d {translations_dir} -D {cfg.message_domain} -l {locale}")
        click.echo("Language templates created.")
    return True


def write_msg_file(msg_file, cfg):
    with open(msg_file, "wb") as fp:
        write_po(fp, cfg.export_metadata(), omit_header=True)


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
            click.echo(ddiff)
            sys.exit(1)
    if output_file:
        with open(output_file, 'w') as reportfile:
            json.dump(report, reportfile, indent=4)
        return True


def print_layers(layers, styles, depth):
    for lyr in layers:
        if isinstance(lyr, OWSFolder):
            indent(depth)
            click.echo("*", lyr.title)
            click.echo(lyr.child_layers, styles, depth + 1)
        else:
            indent(depth)
            click.echo(lyr.name, f"[{','.join(lyr.product_names)}]")
            if styles:
                click.echo(lyr, depth)


def print_styles(lyr, depth=0):
    for styl in lyr.styles:
        indent(0, for_styles=True)
        print(".", styl.name)


def indent(depth, for_styles=False):
    for i in range(depth):
        print("  ", end="")
    if for_styles:
        print("      ", end="")
