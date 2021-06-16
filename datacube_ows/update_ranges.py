#!/usr/bin/env python3
# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2021 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import os
import re

import click
import pkg_resources
import psycopg2
import sqlalchemy
from datacube import Datacube
from psycopg2.sql import SQL

from datacube_ows import __version__
from datacube_ows.ows_configuration import get_config
from datacube_ows.product_ranges import add_ranges, get_sqlconn
from datacube_ows.startup_utils import initialise_debugging


@click.command()
@click.option("--views", is_flag=True, default=False, help="Refresh the ODC spatio-temporal materialised views.")
@click.option("--blocking/--no-blocking", is_flag=True, default=False, help="Obsolete")
@click.option("--schema", is_flag=True, default=False, help="Create or update the OWS database schema, including the spatio-temporal materialised views.")
@click.option("--role", default=None, help="Role to grant database permissions to")
@click.option("--summary", is_flag=True, default=False, help="Treat any named ODC products with no corresponding configured OWS Layer as summary products")
@click.option("--merge-only/--no-merge-only", default=False, help="When used with a multiproduct layer, the ranges for underlying datacube products are not updated.")
@click.option("--product", default=None, help="Deprecated option provided for backwards compatibility")
@click.option("--multiproduct", default=None, help="Deprecated option provided for backwards compatibility.")
@click.option("--calculate-extent/--no-calculate-extent", default=None, help="Has no effect any more.  Provided for backwards compatibility only")
@click.option("--version", is_flag=True, default=False, help="Print version string and exit")
@click.argument("layers", nargs=-1)
def main(layers, blocking,
         merge_only, summary,
         schema, views, role, version,
         product, multiproduct, calculate_extent):
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
        return 0
    # Handle old-style calls
    if not layers:
        layers = []
    if product:
        print("********************************************************************************")
        print("Warning: The product flag is deprecated and will be removed in a future release.")
        print("          The correct way to make this call is now:")
        print("          ")
        print("          python3 update_ranges.py %s" % product)
        print("********************************************************************************")
        layers.append(product)
    if multiproduct:
        print("********************************************************************************")
        print("Warning: The product flag is deprecated and will be removed in a future release.")
        print("          The correct way to make this call is now:")
        print("          ")
        if merge_only:
            print("          python3 update_ranges.py --merge-only %s" % multiproduct)
        else:
            print("          python3 update_ranges.py %s" % multiproduct)
        print("********************************************************************************")
        layers.append(multiproduct)
    if calculate_extent is not None:
        print("********************************************************************************")
        print("Warning: The calculate-extent and no-calculate-extent flags no longer have ")
        print("         any effect.  They are kept only for backwards compatibility and will")
        print("         be removed in a future release.")
        print("********************************************************************************")
    if schema and layers:
        print("Sorry, cannot update the schema and ranges in the same invocation.")
        return 1
    elif views and layers:
        print("Sorry, cannot update the materialised views and ranges in the same invocation.")
        return 1
    elif schema and not role:
        print("Sorry, cannot update schema without specifying a role, use: '--schema --role myrole'")
        return 1
    elif role and not schema:
        print("Sorry, role only makes sense for updating the schema")
        return 1

    initialise_debugging()

    dc = Datacube(app="ows_update_ranges")
    cfg = get_config(called_from_update_ranges=True)
    if schema:
        print("Checking schema....")
        print("Creating or replacing WMS database schema...")
        create_schema(dc, role)
        print("Creating or replacing materialised views...")
        create_views(dc)
        print("Done")
        return 0
    elif views:
        if blocking:
            print("WARNING: The 'blocking' flag is "
                  "no longer supported and will be ignored.")
        print("Refreshing materialised views...")
        refresh_views(dc)
        print("Done")
        return 0

    print("Deriving extents from materialised views")
    if not layers:
        layers = list(cfg.product_index.keys())
    try:
        add_ranges(dc, layers, summary, merge_only)
    except (psycopg2.errors.UndefinedColumn,
            sqlalchemy.exc.ProgrammingError):
        print("ERROR: OWS schema or extent materialised views appear to be missing",
              "\n",
              "       Try running with the --schema options first."
              )
        return 1
    return 0


def create_views(dc):
    try:
        from datacube.config import LocalConfig
        odc_cfg = LocalConfig.find()
        dbname = odc_cfg.get("db_database")
    except ImportError:
        dbname = os.environ.get("DB_DATABASE")
    run_sql(dc, "extent_views/create", database=dbname)


def refresh_views(dc):
    run_sql(dc, "extent_views/refresh")


def create_schema(dc, role):
    run_sql(dc, "wms_schema/create", role=role)


def run_sql(dc, path, **params):
    if not pkg_resources.resource_exists(__name__, f"sql/{path}"):
        print("Cannot find SQL resources - check your datacube-ows installation")
        return
    if not pkg_resources.resource_isdir(__name__, f"sql/{path}"):
        print("Cannot find SQL resource directory - check your datacube-ows installation")
        return

    files = sorted(pkg_resources.resource_listdir(__name__, f"sql/{path}"))

    filename_req_pattern = re.compile(r"\d+[_a-zA-Z0-9]+_requires_(?P<reqs>[_a-zA-Z0-9]+)\.sql")
    filename_pattern = re.compile(r"\d+[_a-zA-Z0-9]+\.sql")
    conn = get_sqlconn(dc)

    for f in files:
        match = filename_pattern.fullmatch(f)
        if not match:
            print(f"Illegal SQL filename: {f} (skipping)")
            continue
        req_match = filename_req_pattern.fullmatch(f)
        if req_match:
            reqs = req_match.group("reqs").split("_")
        else:
            reqs = []
        sql_stream = pkg_resources.resource_stream(__name__, f"sql/{path}/{f}")
        sql = ""
        first = True
        for line in sql_stream:
            line = str(line, "utf-8")
            if first and line.startswith("--"):
                print(line[2:])
            else:
                sql = sql + "\n" + line
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
        if f.endswith("_raw.sql"):
            q = SQL(sql)
            with conn.connection.cursor() as psycopg2connection:
                psycopg2connection.execute(q)
        else:
            conn.execute(sql)
    conn.close()


