import enum

from datacube_ows.cube_pool import cube
from datacube_ows.mv_index import MVSelectOpts, mv_search_datasets

class WCS20Extent:
    def __init__(self, desc_cov):
        env = desc_cov[0].find("{http://www.opengis.net/gml/3.2}boundedBy")[0]
        self.native_crs = env.attrib["srsName"]
        self.time = [
            env.find("{http://www.opengis.net/gml/3.2}beginPosition").text,
            env.find("{http://www.opengis.net/gml/3.2}endPosition").text
        ]
        self.lower_corner = env.find("{http://www.opengis.net/gml/3.2}lowerCorner").text.split(" ")
        self.upper_corner = env.find("{http://www.opengis.net/gml/3.2}upperCorner").text.split(" ")

    def subsets(self, crs=None,
                xstart=0.3, xwidth=0.02,
                ystart=0.8, ywidth=0.02,
                first_time=False,
                multi_time=False):
        if crs is None or crs == self.native_crs:
            bbox = self.native_bbox()
        else:
            bbox = self.bbox_crs(crs)

        bbox = self.subset_bbox(bbox,
                         xstart=xstart, xwidth=xwidth,
                         ystart=ystart, ywidth=ywidth)
        if multi_time:
            time = ('time', self.time[0], self.time[1])
        elif first_time:
            time = ('time', self.time[0])
        else:
            time = ('time', self.time[1])

        return [
            ('x', bbox[0], bbox[2]),
            ('y', bbox[1], bbox[3]),
            time
        ]

    def native_bbox(self):
        return (
            float(self.lower_corner[0]),
            float(self.lower_corner[1]),
            float(self.upper_corner[0]),
            float(self.upper_corner[1])
        )

    def bbox_crs(self, crs):
        from datacube.utils import geometry
        low = geometry.point(*self.lower_corner, crs=self.native_crs).to_crs(crs)
        up = geometry.point(*self.upper_corner, crs=self.native_crs).to_crs(crs)
        return (
            float(low.coords[0][0]),
            float(low.coords[0][1]),
            float(up.coords[0][0]),
            float(up.coords[0][1])
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


class ODCExtent:
    class TimeRequestTypes(enum.Enum):
        FIRST = 0
        SECOND = 1
        LAST  = -1
        SECOND_LAST  = -2
        MIDDLE = 100
        FIRST_TWO = 200
        LAST_TWO = -200

        def slice(self, ls):
            try:
                if self == self.MIDDLE:
                    i = len(ls) // 2
                    return ls[i:i+1]
                elif self == self.FIRST_TWO:
                    return ls[0:1]
                elif self == self.LAST_TWO:
                    return ls[-2:]
                elif self == self.LAST:
                    return ls[-1:]
                else:
                    return ls[self.value:self.value+1]
            except IndexError:
                return []

        def is_multi(self):
            return self in (self.FIRST_TWO, self.LAST_TWO)

    FIRST = TimeRequestTypes.FIRST
    SECOND = TimeRequestTypes.SECOND
    LAST  = TimeRequestTypes.LAST
    SECOND_LAST  = TimeRequestTypes.SECOND_LAST
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
                self.IN_FULL_BUT_OUTSIDE_OF_TIMES
            )

        def needs_time_extent(self):
            return self not in (
                self.FULL_LAYER_EXTENT,
                self.OUTSIDE_OF_FULL_EXTENT
            )

    FULL_LAYER_EXTENT = SpaceRequestType.FULL_EXTENT_FOR_TIMES
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

    def subsets(self,
                space=SpaceRequestType.CENTRAL_SUBSET_FOR_TIMES,
                time=TimeRequestTypes.LAST,
                width_ratio=0.02,
                height_ratio=0.02):
        ext_times = time.slice(self.layer.ranges["times"])
        search_times = [t for t in ext_times]
        extent = None
        with cube() as dc:
            if space.needs_full_extent() and not self.full_extent:
                self.full_extent = mv_search_datasets(dc.index,
                                                 layer=self.layer,
                                                 sel=MVSelectOpts.EXTENT)
            if space.needs_time_extent():
                time_extent = mv_search_datasets(dc.index,
                                                 layer=self.layer,
                                                 sel=MVSelectOpts.EXTENT,
                                                 times=search_times)
            else:
                time_extent = None

            if space == self.FULL_LAYER_EXTENT:
                extent = self.full_extent
            elif space == self.FULL_EXTENT_FOR_TIMES:
                extent = time_extent
            elif space == self.OUTSIDE_OF_FULL_EXTENT:
                bbox = self.full_extent.boundingbox
        return extent, ext_times

