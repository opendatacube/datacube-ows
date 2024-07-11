#!/usr/bin/env python3
# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0


import sys

import click
import psycopg2
import sqlalchemy
from datacube import Datacube

from datacube_ows import __version__
from datacube_ows.ows_configuration import get_config
from datacube_ows.ows_configuration import OWSConfig
from datacube_ows.index import AbortRun, LayerSignature, ows_index
from datacube_ows.startup_utils import initialise_debugging


@click.command()
@click.option("--views", is_flag=True, default=False,
              help="Refresh the ODC spatio-temporal materialised views.")
@click.option("--schema", is_flag=True, default=False,
              help="Create or update the OWS database schema, including the spatio-temporal materialised views.")
@click.option("--read-role", multiple=True,
              help="(Only valid with --schema) Role(s) to grant read-only database permissions to")
@click.option("--write-role", multiple=True,
              help="(Only valid with --schema) Role(s) to grant both read and write/update database permissions to")
@click.option("--cleanup", is_flag=True, default=False,
              help="Cleanup up any datacube-ows 1.8.x tables/views")
@click.option("-E", "--env", default=None,
              help="(Only valid with --schema or --read-role or --write-role or --cleanup) environment to write to.")
@click.option("--version", is_flag=True, default=False,
              help="Print version string and exit")
@click.argument("layers", nargs=-1)
def main(layers: list[str],
         env: str | None,
         schema: bool,
         read_role: list[str],
         write_role: list[str],
         cleanup: bool, views: bool, version: bool) -> int:
    """Manage datacube-ows range tables.  Exposed on setup as datacube-ows-update

    Valid invocations:

    1. Schema/permissions/migration management

    * datacube-ows-update --schema
        Create (re-create) the OWS schema (including materialised views)

    * datacube-ows-update --read-role role1 --read-role role2 --write-role role3
        Grants read or read/write permissions to the OWS tables and views to the indicated role(s).

        The --read-role and --write-role options can also be passed in combination with the --schema option
        described above.

        Read permissions are required for the database role that the datacube-ows service uses.

        Write permissions are required for the database role used to run the Data Management actions below.

        (These schema management actions require higher level permissions.)

    * datacube-ows-update --cleanup
        Clean up (drop) any datcube-ows 1.8.x database entities.

        The --cleanup option can also be passed in combination with the --schema option described above.

    All of the above schema management actions can also be used with the --env or -E option:

    * datacube-ows-update --cleanup --env dev
        Use the "dev" environment from the ODC configuration for connecting to the database.
        (Defaults to env defined in OWS global config, or "default")

    Schema management functions attempt to create or modify database objects and assign permissions over those
    objects.  They typically need to run with a very high level of database permissions - e.g. depending
    on the requested action and the current state of the database schema, they may need to be able to create
    schemas, roles and/or extensions.

    2. Data management (updating OWS indexes)

    * datacube-ows-update --views
        Refresh the materialised views

    * datacube-ows-update layer1 layer2 ...
        Update ranges for the specified LAYERS  (Note that ODC product names are no longer supported)

    * datacube-ows-update
        Update ranges for all configured OWS layers.

    Uses the DATACUBE_OWS_CFG environment variable to find the OWS config file.
    """
    # --version
    if version:
        print("Open Data Cube Open Web Services (datacube-ows) version", __version__)
        sys.exit(0)
    # Handle old-style calls
    if not layers:
        layers = []
    if schema and layers:
        print("Sorry, cannot update the schema and ranges in the same invocation.")
        sys.exit(1)
    if schema and views:
        print("Sorry, No point in updating materialised views and updating the schema in the same invocation.")
        sys.exit(1)
    elif cleanup and layers:
        print("Sorry, cannot cleanup 1.8.x database entities and update ranges in the same invocation.")
        sys.exit(1)
    elif views and cleanup:
        print("Sorry, cannot update the materialised views and cleanup the database in the same invocation.")
        sys.exit(1)
    elif views and layers:
        print("Sorry, cannot update the materialised views and ranges in the same invocation.")
        sys.exit(1)
    elif read_role and (views or layers):
        print("Sorry, read-role can't be granted with view or range updates")
        sys.exit(1)
    elif write_role and (views or layers):
        print("Sorry, write-role can't be granted with view or range updates")
        sys.exit(1)

    initialise_debugging()

    cfg = get_config(called_from_update_ranges=True)
    app = cfg.odc_app + "-update"
    errors: bool = False
    if schema or read_role or write_role or cleanup or views:
        try:
            if cfg.default_env and env is None:
                dc = Datacube(env=cfg.default_env, app=app)
            else:
                dc = Datacube(env=env, app=app)
        except:
            click.echo(f"Unable to connect to the {env or cfg.default_env} database.")
            sys.exit(1)

        click.echo(f"Applying database schema updates to the {dc.index.environment.db_database} database:...")
        try:
            if schema:
                click.echo("Creating or replacing OWS database schema:...")
                ows_index(dc).create_schema(dc)
            for role in read_role:
                click.echo(f"Granting read-only access to role {role}...")
                ows_index(dc).grant_perms(dc, role, read_only=True)
            for role in write_role:
                click.echo(f"Granting read/write access to role {role}...")
                ows_index(dc).grant_perms(dc, role)
            if views:
                click.echo("Updating materialised views...")
                ows_index(dc).update_geotemporal_index(dc)
            if cleanup:
                click.echo("Cleaning up datacube-1.8.x range tables and views...")
                ows_index(dc).cleanup_schema(dc)
        except AbortRun:
            click.echo("Aborting schema update")
            errors = True
        click.echo("Done")
        if errors:
            sys.exit(1)
        return 0

    print("Deriving extents from materialised views")
    try:
        errors = add_ranges(cfg, layers)
        click.echo("Done.")
    except sqlalchemy.exc.ProgrammingError as e:
        if isinstance(e.orig, psycopg2.errors.UndefinedColumn):
            click.echo("ERROR: OWS schema or extent materialised views appear to be missing")
            click.echo("")
            click.echo("       Try running with the --schema options first.")
            sys.exit(1)
        elif isinstance(e.orig, psycopg2.errors.NotNullViolation):
            click.echo("ERROR: OWS materialised views are most likely missing a newly indexed product")
            click.echo("")
            click.echo("       Try running with the --viewes options first.")
            sys.exit(1)
        else:
            raise e
    if errors:
        sys.exit(1)

    return 0


def add_ranges(cfg: OWSConfig, layer_names: list[str]) -> bool:
    if not layer_names:
        layer_names = list(cfg.layer_index.keys())
    errors = False
    cache: dict[LayerSignature, list[str]] = {}
    for name in layer_names:
        if name not in cfg.layer_index:
            click.echo(f"Layer '{name}' does not exist in the OWS configuration - skipping")
            errors = True
            continue
        layer = cfg.layer_index[name]
        layer.ows_index().create_range_entry(layer, cache)

    print("Done.")
    return errors
