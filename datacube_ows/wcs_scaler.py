from datacube.utils import geometry

from affine import Affine

class WCSScalerException(Exception):
    pass

class WCSScalerUnknownDimension(WCSScalerException):
    pass


class WCSScalerOverspecifiedDimension(WCSScalerException):
    pass


class WCSScaler:
    def __init__(self, layer, crs=None):
        self.layer = layer
        if crs:
            self.crs = crs
        else:
            self.layer.native_CRS
        self._update_crs_def()
        self.min_x = None
        self.max_x = None
        self.min_y = None
        self.max_y = None
        self.size_x = None
        self.size_y = None
        self.subsetted_x = False
        self.subsetted_y = False

    def _update_crs_def(self):
        self.crs_def = self.layer.global_cfg.published_CRSs[self.crs]

    def set_minmax(self, is_x, min_, max_):
        if is_x:
            self.min_x = min_
            self.max_x = max_
            self.subsetted_x = True
        else:
            self.min_y = min_
            self.max_y = max_
            self.subsetted_y = True

    def set_size(self, is_x, size):
        if is_x and self.size_x is None:
            self.size_x = size
        elif not is_x and self.size_y is None:
            self.size_y = size
        else:
            raise WCSScalerOverspecifiedDimension()

    def slice(self, dimension, value):
        self.set_minmax(self.is_x_dim(dimension), value, value)

    def is_x_slice(self):
        return self.subsetted_x and self.min_x == self.max_x

    def is_y_slice(self):
        return self.subsetted_y and self.min_y == self.max_y

    def dim(self, is_x):
        if is_x:
            return self.size_x, self.min_x, self.max_x
        else:
            return self.size_y, self.min_y, self.max_y

    def is_x_dim(self, dimension):
        if dimension == self.crs_def['horizontal_coord'].lower():
            return True
        elif dimension == self.crs_def['vertical_coord'].lower():
            return False
        elif dimension == self.layer.native_CRS_def['horizontal_coord'].lower():
            return True
        elif dimension == self.layer.native_CRS_def['vertical_coord'].lower():
            return False
        elif dimension in ("x", "i", "lon", "long", "lng", "longitude"):
            return True
        elif dimension in ("y", "j", "lat", "latitude"):
            return False
        else:
            raise WCSScalerUnknownDimension()

    def trim(self, dimension, lower, higher):
        self.set_minmax(self.is_x_dim(dimension), lower, higher)

    def transform_to_native(self):
        if self.crs != self.layer.native_CRS:
            if not self.subsetted_y and not self.subsetted_x:
                # Neither axis subsetted
                self.crs = self.layer.native_CRS
                self.min_x  = self.layer.ranges["bboxes"][self.layer.native_CRS]["left"]
                self.max_x  = self.layer.ranges["bboxes"][self.layer.native_CRS]["right"]
                self.min_y = self.layer.ranges["bboxes"][self.layer.native_CRS]["bottom"]
                self.max_y = self.layer.ranges["bboxes"][self.layer.native_CRS]["top"]
            elif not self.subsetted_x or not self.subsetted_y:
                # One axis subsetted
                if self.subsetted_x:
                    self.min_y = self.layer.ranges["bboxes"][self.crs]["bottom"]
                    self.max_y = self.layer.ranges["bboxes"][self.crs]["top"]
                if self.subsetted_y:
                    self.min_x = self.layer.ranges["bboxes"][self.crs]["left"]
                    self.max_y = self.layer.ranges["bboxes"][self.crs]["right"]
            else:
                # Both axes subsetted
                pass

        if self.crs != self.layer.native_CRS:
            is_point = False
            # Prepare geometry for transformation
            crs = geometry.CRS(self.crs)
            if self.is_x_slice() and self.is_y_slice():
                geom = geometry.point(self.min_x, self.min_y, crs)
                is_point = True
            elif self.is_x_slice() or self.is_y_slice():
                geom = geometry.line(
                    (
                        (self.min_x, self.min_y),
                        (self.max_x, self.max_y)
                    ), crs)
            else:
                geom = geometry.polygon(
                    (
                        (self.min_x, self.min_y),
                        (self.min_x, self.max_y),
                        (self.max_x, self.max_y),
                        (self.max_x, self.min_y),
                        (self.min_x, self.min_y),
                    ),
                    crs
                )
            crs = geometry.CRS(self.layer.native_CRS)
            if is_point:
                prj_pt = geom.to_crs(crs)
                x, y = prj_pt.coords[0]
                self.set_minmax(True, x, x + self.layer.resolution_x)
                self.set_minmax(False, y, y + self.layer.resolution_y)
                self.size_x = 1
                self.size_y = 1
            else:
                bbox = geom.to_crs(crs).boundingbox
                self.set_minmax(True, bbox.left, bbox.right)
                self.set_minmax(False, bbox.bottom, bbox.top)
                if self.max_x - self.min_x < self.layer.resolution_x * 1.5:
                    self.max_x = self.min_x + self.layer.resolution_x
                    self.size_x = 1
                if self.max_y - self.min_y < self.layer.resolution_y * 1.5:
                    self.max_y = self.min_y + self.layer.resolution_y
                    self.size_y = 1
                self.crs = self.layer.native_CRS
        else:
            if self.max_x - self.min_x < self.layer.resolution_x * 1.5:
                self.max_x = self.min_x + self.layer.resolution_x
                self.size_x = 1
            if self.max_y - self.min_y < self.layer.resolution_y * 1.5:
                self.max_y = self.min_y + self.layer.resolution_y
                self.size_y = 1

    def scale_axis(self, dimension, factor):
        is_x = self.is_x_dim(dimension)
        dim_size, dim_min, dim_max = self.dim(is_x)
        if dim_size is not None:
            raise WCSScalerOverspecifiedDimension()
        if is_x:
            res = self.layer.resolution_x
        else:
            res = self.layer.resolution_y
        self.set_size(is_x,
                      int((dim_max - dim_min) * factor / res + 0.5)
        )

    def scale_size(self, dimension, size):
        self.set_size(self.is_x_dim(dimension), size)

    def scale_extent(self, dimension, low, high):
        # TODO: What is this actually supposed to mean?
        self.set_size(self.is_x_dim(dimension), high - low)

    def affine(self):
        if self.size_x is None:
            self.scale_axis("x", 1.0)
        if self.size_y is None:
            self.scale_axis("y", 1.0)

        x_res = (self.max_x - self.min_x) / self.size_x
        y_res = (self.max_y - self.min_y) / self.size_y
        trans_aff = Affine.translation(self.min_x, self.max_y)
        scale_aff = Affine.scale(x_res, y_res)
        return trans_aff * scale_aff