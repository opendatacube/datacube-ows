# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import importlib
import re

import click
import datacube.cfg
import sqlalchemy
from datacube import Datacube

from datacube_ows.index.api import InsufficientDbPrivileges
from datacube_ows.utils import get_driver_name, get_sqlconn


def run_sql(dc: Datacube, path: str, **params: str) -> bool:
    driver_names = {
        "pg_index": "postgres",
        "pgis_index": "postgis",
    }
    driver_name = driver_names[dc.index.name]
    print(f"path in is {path}")
    full_path = importlib.resources.files("datacube_ows").joinpath(
        f"sql/{driver_name}/{path}"
    )
    if not full_path.is_dir():
        print(
            f"Cannot find SQL resource directory {full_path} - check your datacube-ows installation"
        )
        return False

    files = sorted(full_path.iterdir())  # type: ignore[type-var]

    # N.B. We aren't actually using this "required parameters" feature at
    #      the moment.
    filename_req_pattern = re.compile(
        r"\d+[_a-zA-Z0-9]+_requires_(?P<reqs>[_a-zA-Z0-9]+)\.sql"
    )
    filename_pattern = re.compile(r"\d+[_a-zA-Z0-9]+\.sql")
    with get_sqlconn(dc) as conn:
        all_ok: bool = True
        for fi in files:
            fname = fi.name
            isolated = fname.endswith("_isolated.sql")
            match = filename_pattern.fullmatch(fname)
            if not match:
                click.echo(f"Illegal SQL filename: {fname} (skipping)")
                all_ok = False
                continue
            req_match = filename_req_pattern.fullmatch(fname)
            reqs = req_match.group("reqs").split("_") if req_match else []
            if reqs:
                try:
                    kwargs = {v: params[v] for v in reqs if v != "isolated"}
                except KeyError as e:
                    click.echo(
                        f"Required parameter {e} for file {fname} not supplied - skipping"
                    )
                    all_ok = False
                    continue
            else:
                kwargs = {}
            comment, sql = read_file(driver_name, path, fname, **kwargs)
            if reqs:
                sql = sql.format(**kwargs)
            if isolated:
                conn.commit()
                with get_sqlconn(dc).execution_options(
                    isolation_level="AUTOCOMMIT"
                ) as iso_conn:
                    run_sql_statement(sql, comment, fname, iso_conn, dc.index)
            else:
                run_sql_statement(sql, comment, fname, conn, dc.index)

        return all_ok


def read_file(
    driver_name: str, path: str, fname: str, **kwargs: str
) -> tuple[str, str]:
    ref = importlib.resources.files("datacube_ows").joinpath(
        f"sql/{driver_name}/{path}/{fname}"
    )
    comment = ""
    sql = ""
    with ref.open("rb") as fp:
        first = True
        for line in fp:
            sline = str(line, "utf-8")
            if first and sline.startswith("--"):
                comment = sline[2:].format(**kwargs) if kwargs else sline[2:]
            else:
                sql = sql + "\n" + sline
            first = False
    return comment, sql


def run_sql_statement(
    sql: str,
    comment: str,
    fname: str,
    conn: sqlalchemy.Connection,
    idx: datacube.index.Index,
) -> None:
    click.echo(f" - Running SQL statement: {comment}")
    if get_driver_name(idx) == "psycopg":
        from psycopg.errors import DuplicateObject, InsufficientPrivilege
    else:
        from psycopg2.errors import DuplicateObject, InsufficientPrivilege

    try:
        result = conn.execute(sqlalchemy.text(sql))
        click.echo(f"    ...  succeeded(?) with rowcount {result.rowcount}")
    except sqlalchemy.exc.ProgrammingError as e:
        if isinstance(e.orig, InsufficientPrivilege):
            raise InsufficientDbPrivileges(
                f"Insufficient Privileges (user {idx.environment.db_username}). Try running again as a database superuser"
            ) from None
        if isinstance(e.orig, DuplicateObject):
            if fname.endswith("_ignore_duplicates.sql"):
                click.echo("Ignoring 'already exists' error")
            else:
                click.echo(f"Unexpected database error: {e}")
                raise e from None
        else:
            click.echo(f"Unexpected database error: {e}")
            raise e from e
