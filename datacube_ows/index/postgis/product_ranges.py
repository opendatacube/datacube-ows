# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

import logging
import math
from collections.abc import Callable
from datetime import date, datetime, timezone

import click
import datacube
import odc.geo
import sqlalchemy.exc
from odc.geo.crs import CRS
from sqlalchemy import text

from datacube_ows.index.api import CoordRange, LayerExtent, LayerSignature
from datacube_ows.ows_configuration import OWSNamedLayer
from datacube_ows.utils import get_driver_name, get_sqlconn

_LOG: logging.Logger = logging.getLogger(__name__)


def jsonise_bbox(bbox: odc.geo.geom.BoundingBox) -> dict[str, float]:
    return {
        "top": bbox.top,
        "bottom": bbox.bottom,
        "left": bbox.left,
        "right": bbox.right,
    }


def create_range_entry(
    layer: OWSNamedLayer, cache: dict[LayerSignature, list[str]]
) -> None:
    # Take layer signature
    meta = LayerSignature(
        time_res=layer.time_resolution.value,
        products=tuple(layer.product_names),
        env=layer.local_env._name,
        datasets=layer.dc.index.datasets.count(product=layer.product_names),
    )

    with get_sqlconn(layer.dc) as conn:
        txn = conn.begin()
        if meta in cache:
            template = cache[meta][0]
            # Layer {template} has same signature - reusing
            cache[meta].append(layer.name)
            try:
                conn.execute(
                    text("""
                INSERT INTO ows.layer_ranges
                    (layer, lat_min, lat_max, lon_min, lon_max, dates, bboxes, meta, last_updated)
                SELECT :layer_id, lat_min, lat_max, lon_min, lon_max, dates, bboxes, meta, last_updated
                FROM ows.layer_ranges lr2
                WHERE lr2.layer = :template_id"""),
                    {"layer_id": layer.name, "template_id": template},
                )
            except sqlalchemy.exc.IntegrityError:
                conn.execute(
                    text("""
                UPDATE ows.layer_ranges lr1
                SET lat_min = lr2.lat_min,
                    lat_max = lr2.lat_max,
                    lon_min = lr2.lon_min,
                    lon_max = lr2.lon_max,
                    dates = lr2.dates,
                    bboxes = lr2.bboxes,
                    meta = lr2.meta,
                    last_updated = lr2.last_updated
                FROM ows.layer_ranges lr2
                WHERE lr1.layer = :layer_id
                AND   lr2.layer = :template_id"""),
                    {"layer_id": layer.name, "template_id": template},
                )
        else:
            if get_driver_name(layer.dc.index) == "psycopg":
                from psycopg.types.json import Json
            else:
                from psycopg2.extras import Json
            # insert empty row if one does not already exist
            conn.execute(
                text("""
            INSERT INTO ows.layer_ranges
            (layer, lat_min, lat_max, lon_min, lon_max, dates, bboxes, meta, last_updated)
            VALUES
            (:p_layer, 0, 0, 0, 0, :empty, :empty, :meta, :now)
            ON CONFLICT (layer) DO NOTHING
            """),
                {
                    "p_layer": layer.name,
                    "empty": Json(""),
                    "meta": Json(meta.as_json()),
                    "now": datetime.now(tz=timezone.utc),
                },
            )

            prodids = [p.id for p in layer.products]

            # Set default timezone
            conn.execute(text("""set timezone to 'Etc/UTC'"""))

            # Loop over dates
            dates = set()  # Should get to here!
            if layer.time_resolution.is_solar():
                results = conn.execute(
                    text(
                        """
                  select lower(dt.search_val), upper(dt.search_val),
                         lower(lon.search_val), upper(lon.search_val)
                  from odc.dataset ds, odc.dataset_search_datetime dt, odc.dataset_search_num lon
                  where ds.product_ref = ANY(:prodids)
                  AND ds.id = dt.dataset_ref
                  AND ds.id = lon.dataset_ref
                  AND dt.search_key = :time
                  AND lon.search_key = :lon
                  """
                    ),
                    {"prodids": prodids, "time": "time", "lon": "lon"},
                )
                for result in results:
                    dt1, dt2, ll, lu = result
                    lon = (ll + lu) / 2
                    dt = dt1 + (dt2 - dt1) / 2
                    dt = dt.astimezone(timezone.utc)

                    solar_day = datacube.api.query._convert_to_solar_time(
                        dt, lon
                    ).date()
                    dates.add(solar_day)
            else:
                results = conn.execute(
                    text(
                        """
                  select
                        array_agg(dt.search_val)
                  from odc.dataset_search_datetime dt,
                       odc.dataset ds
                  WHERE ds.product_ref = ANY(:prodids)
                  AND   ds.id = dt.dataset_ref
                  AND   dt.search_key = 'time'
                  """
                    ),
                    {"prodids": prodids},
                )
                for result in results:
                    for dat_ran in result[0]:
                        dates.add(dat_ran.lower)

            if layer.time_resolution.is_subday():
                date_formatter = lambda d: d.isoformat()  # noqa: E731
            else:
                date_formatter = lambda d: d.strftime("%Y-%m-%d")  # noqa: E731

            dates = sorted(dates)
            conn.execute(
                text("""
               UPDATE ows.layer_ranges
               SET dates = :dates
               WHERE layer= :layer_id
            """),
                {
                    "dates": Json(list(map(date_formatter, dates))),
                    "layer_id": layer.name,
                },
            )
            # calculate bounding boxes
            # Get extent polygon from materialised views

            all_bboxes = build_bboxes(layer)
            if not all_bboxes:
                return

            conn.execute(
                text("""
            UPDATE ows.layer_ranges
            SET bboxes = :bbox,
                lat_min = :lat_min,
                lat_max = :lat_max,
                lon_min = :lon_min,
                lon_max = :lon_max
            WHERE layer = :layer_id
            """),
                {
                    "bbox": Json(all_bboxes),
                    "layer_id": layer.name,
                    "lat_min": all_bboxes["EPSG:4326"]["bottom"],
                    "lat_max": all_bboxes["EPSG:4326"]["top"],
                    "lon_min": all_bboxes["EPSG:4326"]["left"],
                    "lon_max": all_bboxes["EPSG:4326"]["right"],
                },
            )

            cache[meta] = [layer.name]
        txn.commit()


def build_bboxes(layer: OWSNamedLayer) -> dict[str, dict[str, float]]:
    # User native CRS for base extent, unless no spatial index for it, in which case
    # use 4326 which always has a spatial index.
    base_crs = CRS(layer.native_CRS)
    if base_crs not in layer.dc.index.spatial_indexes():
        base_crs = CRS("epsg:4326")
    base_extent = extent_for_layer(layer, base_crs)
    if base_extent is None:
        click.echo(f"Layer {layer.name} has no extent in CRS {base_crs}.  Skipping.")
        return {}
    result = {}
    for crsid, crs in layer.global_config().crses.items():
        if crs == base_crs:
            result[crsid] = sanitise_bbox(base_extent.boundingbox)
        elif crs in layer.dc.index.spatial_indexes():
            extent = extent_for_layer(layer, crs)
            if extent is None:
                click.echo(f"Layer {layer.name} has no extent in CRS {crs}.  Skipping.")
                return {}
            result[crsid] = sanitise_bbox(extent.boundingbox)
        else:
            extent = base_extent.to_crs(crs)
            result[crsid] = sanitise_bbox(extent.boundingbox)
    return result


def extent_for_layer(layer: OWSNamedLayer, crs: CRS) -> odc.geo.Geometry | None:
    ext = None
    for product in layer.products:
        prod_extent = layer.dc.index.products.spatial_extent(product, crs)
        ext = prod_extent if ext is None else ext | prod_extent
    return ext


def bbox_projections(
    starting_box: odc.geo.Geometry, crses: dict[str, odc.geo.CRS]
) -> dict[str, dict[str, float]]:
    result = {}
    for crsid, crs in crses.items():
        projbbox = starting_box.to_crs(crs).boundingbox
        result[crsid] = sanitise_bbox(projbbox)
    return result


def sanitise_bbox(bbox: odc.geo.geom.BoundingBox) -> dict[str, float]:
    def sanitise_coordinate(coord: float, fallback: float, upper: bool) -> float:
        if (
            not math.isfinite(coord)
            or (upper and coord > fallback)
            or (not upper and coord < fallback)
        ):
            return fallback
        return coord

    if bbox.crs == CRS("epsg:4326"):
        return {
            "top": sanitise_coordinate(bbox.top, float("90.0"), True),
            "bottom": sanitise_coordinate(bbox.bottom, float("-90.0"), False),
            "left": sanitise_coordinate(bbox.left, float("-180"), False),
            "right": sanitise_coordinate(bbox.right, float("9.999999999e99"), True),
        }
    return {
        "top": sanitise_coordinate(bbox.top, float("9.999999999e99"), True),
        "bottom": sanitise_coordinate(bbox.bottom, float("-9.999999999e99"), False),
        "left": sanitise_coordinate(bbox.left, float("-9.999999999e99"), False),
        "right": sanitise_coordinate(bbox.right, float("9.999999999e99"), True),
    }


def get_ranges(layer: OWSNamedLayer) -> LayerExtent | None:
    with get_sqlconn(layer.dc) as conn:
        results = conn.execute(
            text("""
            SELECT *
            FROM ows.layer_ranges
            WHERE layer=:pname"""),
            {"pname": layer.name},
        )

        for result in results:
            if layer.time_resolution.is_subday():
                dt_parser: Callable[[str], datetime | date] = (  # noqa: E731
                    lambda dts: datetime.fromisoformat(dts)
                )
            else:
                dt_parser = lambda dts: datetime.strptime(dts, "%Y-%m-%d").date()  # noqa: E731
            times = [dt_parser(d) for d in result.dates if d is not None]
            if not times:
                return None
            return LayerExtent(
                lat=CoordRange(min=float(result.lat_min), max=float(result.lat_max)),
                lon=CoordRange(min=float(result.lon_min), max=float(result.lon_max)),
                times=times,
                bboxes=result.bboxes,
            )
        return None
