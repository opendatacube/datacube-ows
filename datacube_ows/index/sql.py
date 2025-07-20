# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import importlib
import re

import click
import datacube.cfg
import psycopg2
import sqlalchemy
from datacube import Datacube

from datacube_ows.index import AbortRun


def get_sqlconn(dc: Datacube) -> sqlalchemy.Connection:
    """
    Extracts a SQLAlchemy database connection from a Datacube object.

    :param dc: An initialised Datacube object
    :return: A SQLAlchemy database connection object.
    """
    # pylint: disable=protected-access
    return dc.index._db._engine.connect()  # type: ignore[attr-defined]


def run_sql(dc: Datacube, driver_name: str, path: str, **params: str) -> bool:
    if not importlib.resources.files("datacube_ows").joinpath(f"sql/{driver_name}/{path}").is_dir():
        print("Cannot find SQL resource directory - check your datacube-ows installation")
        return False

    files = sorted(
        importlib.resources.files("datacube_ows").joinpath(f"sql/{driver_name}/{path}").iterdir()  # type: ignore[type-var]
    )

    filename_req_pattern = re.compile(r"\d+[_a-zA-Z0-9]+_requires_(?P<reqs>[_a-zA-Z0-9]+)\.sql")
    filename_pattern = re.compile(r"\d+[_a-zA-Z0-9]+\.sql")
    conn = get_sqlconn(dc)
    try:
        all_ok: bool = True
        for fi in files:
            fname = fi.name
            match = filename_pattern.fullmatch(fname)
            if not match:
                click.echo(f"Illegal SQL filename: {fname} (skipping)")
                all_ok = False
                continue
            req_match = filename_req_pattern.fullmatch(fname)
            reqs = req_match.group("reqs").split("_") if req_match else []
            if reqs:
                try:
                    kwargs = {v: params[v] for v in reqs}
                except KeyError as e:
                    click.echo(f"Required parameter {e} for file {fname} not supplied - skipping")
                    all_ok = False
                    continue
            else:
                kwargs = {}
            sql = read_file(driver_name, path, fname, **kwargs)
            if reqs:
                sql = sql.format(**kwargs)
            run_sql_statement(sql, fname, conn, dc.index.environment)

        return all_ok
    finally:
        conn.close()


def read_file(driver_name: str, path: str, fname: str, **kwargs: str) -> str:
    ref = importlib.resources.files("datacube_ows").joinpath(f"sql/{driver_name}/{path}/{fname}")
    sql = ""
    with ref.open("rb") as fp:
        first = True
        for line in fp:
            sline = str(line, "utf-8")
            if first and sline.startswith("--"):
                if kwargs:
                    click.echo(f" - Running {sline[2:].format(**kwargs)}")
                else:
                    click.echo(f" - Running {sline[2:]}")
            else:
                sql = sql + "\n" + sline
            first = False
    return sql


def run_sql_statement(sql: str, fname: str, conn: sqlalchemy.Connection, env: datacube.cfg.ODCEnvironment) -> None:
    try:
        result = conn.execute(sqlalchemy.text(sql))
        click.echo(f"    ...  succeeded(?) with rowcount {result.rowcount}")

    except sqlalchemy.exc.ProgrammingError as e:
        if isinstance(e.orig, psycopg2.errors.InsufficientPrivilege):
            click.echo(
                f"Insufficient Privileges (user {env.db_username}). Schema altering actions should be run by a role with admin privileges"
            )
            raise AbortRun() from None
        if isinstance(e.orig, psycopg2.errors.DuplicateObject):
            if fname.endswith('_ignore_duplicates.sql'):
                click.echo("Ignoring 'already exists' error")
            else:
                raise e from None
        else:
            raise e from e
