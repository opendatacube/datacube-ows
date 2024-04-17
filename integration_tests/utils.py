# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2023 OWS Contributors
# SPDX-License-Identifier: Apache-2.0
import enum

from odc.geo.geom import BoundingBox, Geometry
from shapely.ops import triangulate, unary_union

from datacube_ows.cube_pool import cube
from datacube_ows.mv_index import MVSelectOpts, mv_search


class WCS20Extent:
    def __init__(self, desc_cov):
        env = desc_cov[0].find("{http://www.opengis.net/gml/3.2}boundedBy")[0]
        self.native_crs = env.attrib["srsName"]
        self.time = [
            env.find("{http://www.opengis.net/gml/3.2}beginPosition").text,
            env.find("{http://www.opengis.net/gml/3.2}endPosition").text,
        ]
        self.lower_corner = env.find(
            "{http://www.opengis.net/gml/3.2}lowerCorner"
        ).text.split(" ")
        self.upper_corner = env.find(
            "{http://www.opengis.net/gml/3.2}upperCorner"
        ).text.split(" ")

    def subsets(
        self,
        crs=None,
        xstart=0.3,
        xwidth=0.02,
        ystart=0.8,
        ywidth=0.02,
        first_time=False,
        multi_time=False,
    ):
        if crs is None or crs == self.native_crs:
            bbox = self.native_bbox()
        else:
            bbox = self.bbox_crs(crs)

        bbox = self.subset_bbox(
            bbox, xstart=xstart, xwidth=xwidth, ystart=ystart, ywidth=ywidth
        )
        if multi_time:
            time = ("time", self.time[0], self.time[1])
        elif first_time:
            time = ("time", self.time[0])
        else:
            time = ("time", self.time[1])

        if crs in ["EPSG:4326"]:
            # Vertical coordinate First
            return [("x", bbox[1], bbox[3]), ("y", bbox[0], bbox[2]), time]
        else:
            return [("x", bbox[0], bbox[2]), ("y", bbox[1], bbox[3]), time]

    def native_bbox(self):
        return (
            float(self.lower_corner[0]),
            float(self.lower_corner[1]),
            float(self.upper_corner[0]),
            float(self.upper_corner[1]),
        )

    def bbox_crs(self, crs):
        from odc.geo.geom import point

        low = point(*self.lower_corner, crs=self.native_crs).to_crs(crs)
        up = point(*self.upper_corner, crs=self.native_crs).to_crs(crs)
        return (
            float(low.coords[0][0]),
            float(low.coords[0][1]),
            float(up.coords[0][0]),
            float(up.coords[0][1]),
        )

    @staticmethod
    def subcoord(c_min, c_max, start, end):
        diff = c_max - c_min
        return diff * start + c_min, diff * end + c_min

    @staticmethod
    def subset_bbox(bbox, xstart=0.3, xwidth=0.02, ystart=0.8, ywidth=0.02):
        x = WCS20Extent.subcoord(bbox[0], bbox[2], xstart, xstart + xwidth)
        y = WCS20Extent.subcoord(bbox[1], bbox[3], xstart, xstart + xwidth)
        return (x[0], y[0], x[1], y[1])


def geom_from_bbox(bbox, crs="EPSG:4326"):
    geojson = {
        "type": "Polygon",
        "coordinates": [
            [
                bbox.points[0],
                bbox.points[1],
                bbox.points[3],
                bbox.points[2],
                bbox.points[0],
            ]
        ],
    }
    return Geometry(geojson, crs=crs)


def simplify_geom(geom_in, crs="EPSG:4326"):
    geom = geom_in
    # Pick biggest polygon from multipolygon
    if geom.geom_type == "MultiPolygon":
        geom = max(geom.geom.geoms, key=lambda x: x.area)
    else:
        geom = geom.geom
    # Triangulate
    rawtriangles = list(triangulate(geom))
    triangles = list(
        filter(
            lambda x: geom_in.geom.contains(x.representative_point())
            and x.area / geom.area > 0.1,
            rawtriangles,
        )
    )
    geom = unary_union(triangles)
    if geom.geom_type == "MultiPolygon":
        geom = max(geom.geoms, key=lambda x: x.area)
    return Geometry(geom, crs=crs)


class ODCExtent:
    class TimeRequestTypes(enum.Enum):
        FIRST = 0
        SECOND = 1
        LAST = -1
        SECOND_LAST = -2
        MIDDLE = 100
        FIRST_TWO = 200
        LAST_TWO = -200

        def slice(self, ls):
            try:
                if self == self.MIDDLE:
                    i = len(ls) // 2
                    return ls[i: i + 1]
                elif self == self.FIRST_TWO:
                    return ls[0:1]
                elif self == self.LAST_TWO:
                    return ls[-2:]
                elif self == self.LAST:
                    return ls[-1:]
                else:
                    return ls[self.value: self.value + 1]
            except IndexError:
                return []

        def is_multi(self):
            return self in (self.FIRST_TWO, self.LAST_TWO)

    FIRST = TimeRequestTypes.FIRST
    SECOND = TimeRequestTypes.SECOND
    LAST = TimeRequestTypes.LAST
    SECOND_LAST = TimeRequestTypes.SECOND_LAST
    MIDDLE = TimeRequestTypes.MIDDLE
    FIRST_TWO = TimeRequestTypes.FIRST_TWO
    LAST_TWO = TimeRequestTypes.LAST_TWO

    class SpaceRequestType(enum.Enum):
        FULL_LAYER_EXTENT = 0
        FULL_EXTENT_FOR_TIMES = 1
        CENTRAL_SUBSET_FOR_TIMES = 2
        OFFSET_SUBSET_FOR_TIMES = 3
        EDGE_SUBSET_FOR_TIMES = 4
        OUTSIDE_OF_FULL_EXTENT = -1
        IN_FULL_BUT_OUTSIDE_OF_TIMES = -2

        def needs_full_extent(self):
            return self in (
                self.FULL_LAYER_EXTENT,
                self.OUTSIDE_OF_FULL_EXTENT,
                self.IN_FULL_BUT_OUTSIDE_OF_TIMES,
            )

        def needs_time_extent(self):
            return self not in (self.FULL_LAYER_EXTENT, self.OUTSIDE_OF_FULL_EXTENT)

        def subset(self, time_extent, full_extent):
            if self == self.FULL_LAYER_EXTENT:
                return full_extent
            if self == self.FULL_EXTENT_FOR_TIMES:
                return time_extent
            if self == self.OUTSIDE_OF_FULL_EXTENT:
                full_bbox = full_extent.boundingbox
                width = full_bbox.right - full_bbox.left
                height = full_bbox.top - full_bbox.bottom
                outside_bbox = BoundingBox(
                    top=full_bbox.top + height,
                    bottom=full_bbox.top + height * 0.8,
                    left=full_bbox.left - width,
                    right=full_bbox.right - width * 0.8,
                )
                return geom_from_bbox(outside_bbox)
            if self == self.IN_FULL_BUT_OUTSIDE_OF_TIMES:
                outside_times = full_extent.difference(time_extent)
                outside_times = simplify_geom(outside_times)
                sub = self.CENTRAL_SUBSET_FOR_TIMES.subset(outside_times, full_extent)
                return sub

            bbox = time_extent.boundingbox
            width = bbox.right - bbox.left
            height = bbox.top - bbox.bottom
            if width < 0 or height < 0:
                print(
                    "I think this should still work, but I haven't worked through it properly"
                )
            # Slice on vertical coordinate (horizontal slice)
            centre_y = (bbox.top + bbox.bottom) / 2
            if self == self.CENTRAL_SUBSET_FOR_TIMES:
                hslice_bbox = BoundingBox(
                    left=bbox.left,
                    right=bbox.right,
                    top=centre_y + 0.02 * height,
                    bottom=centre_y - 0.02 * height,
                )
                hslice_geom = geom_from_bbox(hslice_bbox)
                hslice_geom = hslice_geom.intersection(time_extent)
            elif self == self.OFFSET_SUBSET_FOR_TIMES:
                offset_y = centre_y + 0.35 * height
                hslice_bbox = BoundingBox(
                    left=bbox.left,
                    right=bbox.right,
                    top=offset_y + 0.02 * height,
                    bottom=offset_y - 0.02 * height,
                )
                hslice_geom = geom_from_bbox(hslice_bbox)
                hslice_geom = hslice_geom.intersection(time_extent)
            else:  # if self == self.EDGE_SUBSET_FOR_TIMES:
                hslice_bbox = BoundingBox(
                    left=bbox.left,
                    right=bbox.right,
                    top=bbox.bottom + 0.02 * height,
                    bottom=bbox.bottom,
                )
                hslice_geom = geom_from_bbox(hslice_bbox)
                hslice_geom = hslice_geom.intersection(time_extent)
            # Slice on horizontal coordinate (vertical slice)
            slice_bbox = hslice_geom.boundingbox
            centre_x = (slice_bbox.left + slice_bbox.right) / 2
            if self == self.CENTRAL_SUBSET_FOR_TIMES:
                vslice_bbox = BoundingBox(
                    left=centre_x - 0.02 * width,
                    right=centre_x + 0.02 * width,
                    top=slice_bbox.top,
                    bottom=slice_bbox.bottom,
                )
                vslice_geom = geom_from_bbox(vslice_bbox)
            elif self == self.OFFSET_SUBSET_FOR_TIMES:
                offset_x = centre_x + 0.25 * height
                vslice_bbox = BoundingBox(
                    left=offset_x - 0.02 * width,
                    right=offset_x + 0.02 * width,
                    top=slice_bbox.top,
                    bottom=slice_bbox.bottom,
                )
                vslice_geom = geom_from_bbox(hslice_bbox)
            else:  # if self == self.EDGE_SUBSET_FOR_TIMES:
                vslice_bbox = BoundingBox(
                    left=slice_bbox.left,
                    right=slice_bbox.left + 0.02 * width,
                    top=slice_bbox.top,
                    bottom=slice_bbox.bottom,
                )
                vslice_geom = geom_from_bbox(hslice_bbox)

            return vslice_geom

    FULL_LAYER_EXTENT = SpaceRequestType.FULL_LAYER_EXTENT
    FULL_EXTENT_FOR_TIMES = SpaceRequestType.FULL_EXTENT_FOR_TIMES
    CENTRAL_SUBSET_FOR_TIMES = SpaceRequestType.CENTRAL_SUBSET_FOR_TIMES
    OFFSET_SUBSET_FOR_TIMES = SpaceRequestType.OFFSET_SUBSET_FOR_TIMES
    EDGE_SUBSET_FOR_TIMES = SpaceRequestType.EDGE_SUBSET_FOR_TIMES
    OUTSIDE_OF_FULL_EXTENT = SpaceRequestType.OUTSIDE_OF_FULL_EXTENT
    IN_FULL_BUT_OUTSIDE_OF_TIMES = SpaceRequestType.IN_FULL_BUT_OUTSIDE_OF_TIMES

    def __init__(self, layer):
        self.layer = layer
        self.native_crs = layer.native_CRS
        self.full_extent = None

    def wcs1_args(
        self,
        space=SpaceRequestType.CENTRAL_SUBSET_FOR_TIMES,
        time=TimeRequestTypes.LAST,
        crs="EPSG:4326",
    ):
        extent, times = self.subsets(space, time)
        if len(times) == 1:
            time_strs = (times[0].strftime("%Y-%m-%d"),)
        else:
            time_strs = (times[0].strftime("%Y-%m-%d"), times[-1].strftime("%Y-%m-%d"))
        if crs == "EPSG:4326":
            crs_extent = extent
        else:
            crs_extent = extent.to_crs(crs)
        crs_bbox = crs_extent.boundingbox
        return {
            "bbox": f"{min(crs_bbox.left,crs_bbox.right)},{min(crs_bbox.top,crs_bbox.bottom)},{max(crs_bbox.left,crs_bbox.right)},{max(crs_bbox.top,crs_bbox.bottom)}",
            "times": ",".join(time_strs),
        }

    def wcs2_subsets(
        self,
        space=SpaceRequestType.CENTRAL_SUBSET_FOR_TIMES,
        time=TimeRequestTypes.LAST,
        crs="EPSG:4326",
    ):
        extent, times = self.subsets(space, time)
        if len(times) == 1:
            time_sub = ("time", times[0].strftime("%Y-%m-%d"))
        else:
            time_sub = (
                "time",
                times[0].strftime("%Y-%m-%d"),
                times[-1].strftime("%Y-%m-%d"),
            )
        if crs == "EPSG:4326":
            crs_extent = extent
        else:
            crs_extent = extent.to_crs(crs)
        crs_bbox = crs_extent.boundingbox
        return (
            (
                "x",
                min(crs_bbox.left, crs_bbox.right),
                max(crs_bbox.left, crs_bbox.right),
            ),
            (
                "y",
                min(crs_bbox.top, crs_bbox.bottom),
                max(crs_bbox.top, crs_bbox.bottom),
            ),
            time_sub,
        )

    def raw_wcs2_subsets(
        self,
        space=SpaceRequestType.CENTRAL_SUBSET_FOR_TIMES,
        time=TimeRequestTypes.LAST,
        crs="EPSG:4326",
    ):
        extent, times = self.subsets(space, time)
        if len(times) == 1:
            time_sub = f'time("{times[0].strftime("%Y-%m-%d")}")'
        else:
            time_sub = f'time("{times[0].strftime("%Y-%m-%d")}","{times[-1].strftime("%Y-%m-%d")}")'
        if crs == "EPSG:4326":
            crs_extent = extent
        else:
            crs_extent = extent.to_crs(crs)
        crs_bbox = crs_extent.boundingbox
        return (
            f"x({min(crs_bbox.left, crs_bbox.right)},{max(crs_bbox.left, crs_bbox.right)})",
            f"y({min(crs_bbox.top, crs_bbox.bottom)},{max(crs_bbox.top, crs_bbox.bottom)})",
            time_sub,
        )

    def subsets(
        self,
        space=SpaceRequestType.CENTRAL_SUBSET_FOR_TIMES,
        time=TimeRequestTypes.LAST,
    ):
        ext_times = time.slice(self.layer.ranges["times"])
        search_times = [self.layer.search_times(t) for t in ext_times]
        with cube() as dc:
            if space.needs_full_extent() and not self.full_extent:
                self.full_extent = mv_search(
                    dc.index, products=self.layer.products, sel=MVSelectOpts.EXTENT
                )
            if space.needs_time_extent():
                time_extent = mv_search(
                    dc.index,
                    products=self.layer.products,
                    sel=MVSelectOpts.EXTENT,
                    times=search_times,
                )
            else:
                time_extent = None

            extent = space.subset(time_extent, self.full_extent)

        return extent, ext_times
