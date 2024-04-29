#!/usr/bin/env python3
# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0


import importlib.resources
import re
import sys

import datacube
import click
import psycopg2
import sqlalchemy
from datacube import Datacube
from sqlalchemy import text

from datacube_ows import __version__
from datacube_ows.ows_configuration import get_config
from datacube_ows.product_ranges import add_ranges, get_sqlconn
from datacube_ows.startup_utils import initialise_debugging


@click.command()
@click.option("--views", is_flag=True, default=False, help="Refresh the ODC spatio-temporal materialised views.")
@click.option("--schema", is_flag=True, default=False, help="Create or update the OWS database schema, including the spatio-temporal materialised views.")
@click.option("--role", default=None, help="Role to grant database permissions to")
@click.option("--merge-only/--no-merge-only", default=False, help="When used with a multiproduct layer, the ranges for underlying datacube products are not updated.")
@click.option("--version", is_flag=True, default=False, help="Print version string and exit")
@click.argument("layers", nargs=-1)
def main(layers: list[str],
         merge_only: bool,
         schema: bool, views: bool, role: str | None, version: bool) -> int:
    """Manage datacube-ows range tables.

    Valid invocations:

    * update_ranges.py --schema --role myrole
        Create (re-create) the OWS schema (including materialised views) and grants permission to role myrole

    * update_ranges.py --views
        Refresh the materialised views

    * One or more OWS or ODC layer names
        Update ranges for the specified LAYERS

    * No LAYERS (and neither the --views nor --schema options)
        (Update ranges for all configured OWS layers.

    Uses the DATACUBE_OWS_CFG environment variable to find the OWS config file.
    """
    # --version
    if version:
        print("Open Data Cube Open Web Services (datacube-ows) version",
              __version__
               )
        sys.exit(0)
    # Handle old-style calls
    if not layers:
        layers = []
    if schema and layers:
        print("Sorry, cannot update the schema and ranges in the same invocation.")
        sys.exit(1)
    elif views and layers:
        print("Sorry, cannot update the materialised views and ranges in the same invocation.")
        sys.exit(1)
    elif schema and not role:
        print("Sorry, cannot update schema without specifying a role, use: '--schema --role myrole'")
        sys.exit(1)
    elif role and not schema:
        print("Sorry, role only makes sense for updating the schema")
        sys.exit(1)

    initialise_debugging()

    dc = Datacube(app="ows_update_ranges")
    cfg = get_config(called_from_update_ranges=True)
    if schema:
        assert role is not None  # for type checker
        print("Checking schema....")
        print("Creating or replacing WMS database schema...")
        create_schema(dc, role)
        print("Creating or replacing materialised views...")
        create_views(dc)
        print("Done")
        return 0
    elif views:
        print("Refreshing materialised views...")
        refresh_views(dc)
        print("Done")
        return 0

    print("Deriving extents from materialised views")
    if not layers:
        layers = list(cfg.product_index.keys())
    try:
        errors = add_ranges(dc, layers, merge_only)
    except (psycopg2.errors.UndefinedColumn,
            sqlalchemy.exc.ProgrammingError) as e:
        print("ERROR: OWS schema or extent materialised views appear to be missing",
              "\n",
              "       Try running with the --schema options first."
              )
        sys.exit(1)
    if errors:
        sys.exit(1)

    return 0


def create_views(dc: datacube.Datacube):
    from datacube.cfg import ODCConfig
    odc_cfg = ODCConfig().get_environment()
    dbname = odc_cfg.db_database
    run_sql(dc, "extent_views/create", database=dbname)


def refresh_views(dc: datacube.Datacube):
    run_sql(dc, "extent_views/refresh")


def create_schema(dc: datacube.Datacube, role: str):
    run_sql(dc, "wms_schema/create", role=role)


def run_sql(dc: datacube.Datacube, path: str, **params: str):
    if not importlib.resources.files("datacube_ows").joinpath(f"sql/{path}").is_dir():
        print("Cannot find SQL resource directory - check your datacube-ows installation")
        return

    files = sorted(
        importlib.resources.files("datacube_ows").joinpath(f"sql/{path}").iterdir()  # type: ignore[type-var]
    )

    filename_req_pattern = re.compile(r"\d+[_a-zA-Z0-9]+_requires_(?P<reqs>[_a-zA-Z0-9]+)\.sql")
    filename_pattern = re.compile(r"\d+[_a-zA-Z0-9]+\.sql")
    conn = get_sqlconn(dc)

    for fi in files:
        f = fi.name
        match = filename_pattern.fullmatch(f)
        if not match:
            print(f"Illegal SQL filename: {f} (skipping)")
            continue
        req_match = filename_req_pattern.fullmatch(f)
        if req_match:
            reqs = req_match.group("reqs").split("_")
        else:
            reqs = []
        ref = importlib.resources.files("datacube_ows").joinpath(f"sql/{path}/{f}")
        with ref.open("rb") as fp:
            sql = ""
            first = True
            for line in fp:
                sline = str(line, "utf-8")
                if first and sline.startswith("--"):
                    print(sline[2:])
                else:
                    sql = sql + "\n" + sline
                    if first:
                        print(f"Running {f}")
                first = False
        if reqs:
            try:
                kwargs = {v: params[v] for v in reqs}
            except KeyError as e:
                print(f"Required parameter {e} for file {f} not supplied - skipping")
                continue
            sql = sql.format(**kwargs)
        # Special handling of "_raw.sql" scripts no longer required in SQLAlchemy 2?
        conn.execute(text(sql))
    conn.close()
