from datacube.utils import geometry
import numpy
import xarray
from affine import Affine

class WCSScalerException(Exception):
    pass

class WCSScalerUnknownDimension(WCSScalerException):
    pass


class WCSScalerOverspecifiedDimension(WCSScalerException):
    pass

class WCSScalarIllegalSize(WCSScalerException):
    pass

class WCSScaler:
    def __init__(self, layer, crs=None):
        self.layer = layer
        if crs:
            self.crs = crs
        else:
            self.crs = self.layer.native_CRS
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
        if size <= 0:
            raise WCSScalarIllegalSize()
        if isinstance(size, float):
            size = int(size + 0.5)
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

    def to_crs(self, new_crs):
        grid = self.layer.grids[new_crs]
        if self.crs != new_crs:
            if not self.subsetted_y and not self.subsetted_x:
                # Neither axis subsetted
                self.set_minmax(True,
                        self.layer.ranges["bboxes"][new_crs]["left"],
                        self.layer.ranges["bboxes"][new_crs]["right"]
                )
                self.set_minmax(False,
                        self.layer.ranges["bboxes"][new_crs]["bottom"],
                        self.layer.ranges["bboxes"][new_crs]["top"]
                )
                self.crs = new_crs
                self._update_crs_def()
            elif not self.subsetted_x or not self.subsetted_y:
                # One axis subsetted
                if self.subsetted_x:
                    self.min_y = self.layer.ranges["bboxes"][self.crs]["bottom"]
                    self.max_y = self.layer.ranges["bboxes"][self.crs]["top"]
                if self.subsetted_y:
                    self.min_x = self.layer.ranges["bboxes"][self.crs]["left"]
                    self.max_x = self.layer.ranges["bboxes"][self.crs]["right"]
            else:
                # Both axes subsetted
                pass

        if self.crs != new_crs:
            is_point = False
            # Prepare geometry for transformation
            old_crs_obj = geometry.CRS(self.crs)
            if self.is_x_slice() and self.is_y_slice():
                geom = geometry.point(self.min_x, self.min_y, old_crs_obj)
                is_point = True
            elif self.is_x_slice() or self.is_y_slice():
                geom = geometry.line(
                    (
                        (self.min_x, self.min_y),
                        (self.max_x, self.max_y)
                    ), old_crs_obj)
            else:
                geom = geometry.polygon(
                    (
                        (self.min_x, self.min_y),
                        (self.min_x, self.max_y),
                        (self.max_x, self.max_y),
                        (self.max_x, self.min_y),
                        (self.min_x, self.min_y),
                    ),
                    old_crs_obj
                )
            new_crs_obj = geometry.CRS(new_crs)
            grid = self.layer.grids[new_crs]
            if is_point:
                prj_pt = geom.to_crs(new_crs_obj)
                x, y = prj_pt.coords[0]
                self.set_minmax(True, x, x + grid["resolution"][0])
                self.set_minmax(False, y, y + grid["resolution"][1])
                self.size_x = 1
                self.size_y = 1
            else:
                bbox = geom.to_crs(new_crs_obj).boundingbox
                self.set_minmax(True, bbox.left, bbox.right)
                self.set_minmax(False, bbox.bottom, bbox.top)
                self.quantise_to_resolution(grid)
            self.crs = new_crs
            self._update_crs_def()
        else:
            self.quantise_to_resolution(grid)

    def quantise_to_resolution(self, grid):
        if self.max_x - self.min_x < grid["resolution"][0] * 1.5:
            self.max_x = self.min_x + grid["resolution"][0]
            self.size_x = 1
        if self.max_y - self.min_y < grid["resolution"][1] * 1.5:
            self.max_y = self.min_y + grid["resolution"][1]
            self.size_y = 1

    def scale_axis(self, dimension, factor):
        is_x = self.is_x_dim(dimension)
        dim_size, dim_min, dim_max = self.dim(is_x)
        if dim_size is not None:
            raise WCSScalerOverspecifiedDimension()
        grid = self.layer.grids[self.crs]
        if is_x:
            res = grid["resolution"][0]
        else:
            res = grid["resolution"][1]
        scaled_size = abs((dim_max - dim_min) * factor / res)
        self.set_size(is_x, scaled_size)

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

        x_scale = (self.max_x - self.min_x) / self.size_x
        # Y axis is reversed: image coordinate conventions
        y_scale = (self.min_y - self.max_y) / self.size_y
        trans_aff = Affine.translation(self.min_x, self.max_y)
        scale_aff = Affine.scale(x_scale, y_scale)
        return trans_aff * scale_aff

    def empty_dataset(self, bands, times):
        xvals = numpy.linspace(
            self.min_x,
            self.max_x,
            num = self.size_x
        )
        yvals = numpy.linspace(
            self.min_y,
            self.max_y,
            num = self.size_y
        )
        x_name = self.crs_def["horizontal_coord"],
        y_name = self.crs_def["vertical_coord"],
        if self.crs_def["vertical_coord_first"]:
            nparrays = {
                band: (
                        ("time", y_name, x_name),
                        numpy.full(
                            (len(times), self.size_y, self.size.x),
                            self.layer.nodata_dict[band]
                        )
                )
                for band in bands
            }
        else:
            nparrays = {
                band: (
                    ("time", x_name, y_name),
                    numpy.full(
                        (len(times), self.size_x, self.size.y),
                        self.layer.nodata_dict[band]
                    )
                )
                for band in bands
            }

        return xarray.Dataset(
                nparrays,
                coords={
                    "time": times,
                    x_name: xvals,
                    y_name: yvals,
                }
        ).astype("int16")
