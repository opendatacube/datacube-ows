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
        x = WCS2Extent.subcoord(bbox[0], bbox[2], xstart, xstart + xwidth)
        y = WCS2Extent.subcoord(bbox[1], bbox[3], xstart, xstart + xwidth)
        return (x[0], y[0], x[1], y[1])