# This file is part of datacube-ows, part of the Open Data Cube project.
# See https://opendatacube.org for more information.
#
# Copyright (c) 2017-2024 OWS Contributors
# SPDX-License-Identifier: Apache-2.0

from affine import Affine
from odc.geo import geom as odc_geom
from typing_extensions import override


class WCSScalerException(Exception):
    pass


class WCSScalerUnknownDimension(WCSScalerException):
    def __init__(self, dim: str, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.dim = dim


class WCSScalerOverspecifiedDimension(WCSScalerException):
    pass


class WCSScalarIllegalSize(WCSScalerException):
    pass


class SpatialParameter:
    def __init__(self, layer, crs: str, x=None, y=None) -> None:
        self.layer = layer
        self.crs_def = self.layer.global_cfg.published_CRSs[crs]
        self.x = x
        self.y = y

    def is_x_dim(self, dimension: str) -> bool:
        if dimension == self.crs_def["horizontal_coord"].lower():
            return True
        if dimension == self.crs_def["vertical_coord"].lower():
            return False
        if dimension == self.layer.native_CRS_def["horizontal_coord"].lower():
            return True
        if dimension == self.layer.native_CRS_def["vertical_coord"].lower():
            return False
        if dimension in ("x", "i", "lon", "long", "lng", "longitude"):
            return True
        if dimension in ("y", "j", "lat", "latitude"):
            return False
        raise WCSScalerUnknownDimension(dimension)

    def __getitem__(self, dim: str):
        if self.is_x_dim(dim):
            return self.x
        return self.y

    def __setitem__(self, dim: str, val) -> None:
        if self.is_x_dim(dim):
            self.x = val
        else:
            self.y = val

    def __getattr__(self, dim):
        return self[dim]

    @override
    def __setattr__(self, dim: str, val) -> None:
        if dim in ("x", "y", "layer", "crs_def"):
            super().__setattr__(dim, val)
        else:
            try:
                self[dim] = val
            except WCSScalerUnknownDimension:
                super().__setattr__(dim, val)

    def set(self, x, y) -> None:
        self.x = x
        self.y = y


class WCSScaler:
    def __init__(self, layer, crs: str | None = None) -> None:
        self.layer = layer
        self.cfg = self.layer.global_cfg
        if crs:
            self.crs = crs
        else:
            self.crs = self.layer.native_CRS
        self.min = SpatialParameter(self.layer, self.crs)
        self.max = SpatialParameter(self.layer, self.crs)
        self.size = SpatialParameter(self.layer, self.crs)
        self.subsetted = SpatialParameter(self.layer, self.crs, False, False)

    @property
    def crs(self) -> str:
        return self._crs

    @crs.setter
    def crs(self, crs: str) -> None:
        self.crs_def = self.layer.global_cfg.published_CRSs[crs]
        self._crs = crs

    def set_size(self, dim: str, size: int) -> None:
        if size <= 0:
            raise WCSScalarIllegalSize()
        if isinstance(size, float):
            size = int(size + 0.5)
        if self.size[dim] is None:
            self.size[dim] = size
        else:
            raise WCSScalerOverspecifiedDimension()

    def slice(self, dimension, value) -> None:
        self.min[dimension] = value
        self.max[dimension] = value
        self.subsetted[dimension] = True

    def is_slice(self, dim: str) -> bool:
        return self.subsetted[dim] and self.min[dim] == self.max[dim]

    def dim(self, dim: str) -> tuple:
        return self.size[dim], self.min[dim], self.max[dim]

    def trim(self, dimension: str, lower, higher) -> None:
        self.min[dimension] = lower
        self.max[dimension] = higher
        self.subsetted[dimension] = True

    def to_crs(self, new_crs: str) -> None:
        grid = self.layer.grids[new_crs]
        skip_x_xform = False
        skip_y_xform = False
        if not self.subsetted.x and not self.subsetted.y:
            # Neither axis subsetted
            self.min.x = self.layer.ranges.bboxes[new_crs]["left"]
            self.max.x = self.layer.ranges.bboxes[new_crs]["right"]
            self.min.y = self.layer.ranges.bboxes[new_crs]["bottom"]
            self.max.y = self.layer.ranges.bboxes[new_crs]["top"]
            self.crs = new_crs
        elif not self.subsetted.x or not self.subsetted.y:
            # One axis subsetted
            if self.subsetted.x:
                self.min.y = self.layer.ranges.bboxes[self.crs]["bottom"]
                self.max.y = self.layer.ranges.bboxes[self.crs]["top"]
                skip_y_xform = True
            if self.subsetted.y:
                self.min.x = self.layer.ranges.bboxes[self.crs]["left"]
                self.max.x = self.layer.ranges.bboxes[self.crs]["right"]
                skip_x_xform = True
        else:
            # Both axes subsetted
            pass

        if self.crs != new_crs:
            is_point = False
            # Prepare geometry for transformation
            old_crs_obj = self.cfg.crs(self.crs)
            if self.is_slice("x") and self.is_slice("y"):
                geom = odc_geom.point(self.min.x, self.min.y, old_crs_obj)
                is_point = True
            elif self.is_slice("x") or self.is_slice("y"):
                geom = odc_geom.line(
                    [(self.min.x, self.min.y), (self.max.x, self.max.y)], old_crs_obj
                )
            else:
                geom = odc_geom.polygon(
                    [
                        (self.min.x, self.min.y),
                        (self.min.x, self.max.y),
                        (self.max.x, self.max.y),
                        (self.max.x, self.min.y),
                        (self.min.x, self.min.y),
                    ],
                    old_crs_obj,
                )
            new_crs_obj = self.cfg.crs(new_crs)
            grid = self.layer.grids[new_crs]
            if is_point:
                prj_pt = geom.to_crs(new_crs_obj)
                x, y = prj_pt.coords[0]
                self.min.set(x, y)
                self.max.set(x + grid["resolution"][0], y + grid["resolution"][1])
                self.size.set(1, 1)
            else:
                proj_geom = geom.to_crs(new_crs_obj)
                bbox = proj_geom.boundingbox
                if skip_x_xform:
                    self.min.x = self.layer.ranges.bboxes[new_crs]["left"]
                    self.max.x = self.layer.ranges.bboxes[new_crs]["right"]
                else:
                    self.min.x = bbox.left
                    self.max.x = bbox.right
                if skip_y_xform:
                    self.min.y = self.layer.ranges.bboxes[new_crs]["bottom"]
                    self.max.y = self.layer.ranges.bboxes[new_crs]["top"]
                else:
                    self.min.y = bbox.bottom
                    self.max.y = bbox.top

                self.quantise_to_resolution(grid)
            self.crs = new_crs
        else:
            self.quantise_to_resolution(grid)

    def quantise_to_resolution(self, grid: dict) -> None:
        for idx, dim in enumerate("xy"):
            if abs(self.max[dim] - self.min[dim]) < abs(grid["resolution"][idx] * 1.5):
                self.max[dim] = self.min[dim] + grid["resolution"][idx]
                self.size[dim] = 1

    def scale_axis(self, dimension: str, factor: float) -> None:
        dim_size, dim_min, dim_max = self.dim(dimension)
        if dim_size is not None:
            raise WCSScalerOverspecifiedDimension()
        grid = self.layer.grids[self.crs]
        res = grid["resolution"][0 if self.min.is_x_dim(dimension) else 1]
        scaled_size = abs((dim_max - dim_min) * factor / res)
        self.set_size(dimension, scaled_size)

    def scale_size(self, dimension: str, size: int) -> None:
        self.set_size(dimension, size)

    def scale_extent(self, dimension: str, low: int, high: int) -> None:
        # TODO: What is this actually supposed to mean?
        self.set_size(dimension, high - low)

    def affine(self) -> Affine:
        if self.size.x is None:
            self.scale_axis("x", 1.0)
        if self.size.y is None:
            self.scale_axis("y", 1.0)

        x_scale = (self.max.x - self.min.x) / self.size.x
        # Y axis is reversed: image coordinate conventions
        y_scale = (self.min.y - self.max.y) / self.size.y
        # if self.crs_def["vertical_coord_first"]:
        # This should probably happen, but can't because PostGIS wants
        # coords to be horizontal first, regardless of what the CRS says.
        # trans_aff = Affine.translation(self.min.y, self.max.x)
        # scale_aff = Affine.scale(y_scale, x_scale)
        # else:
        trans_aff = Affine.translation(self.min.x, self.max.y)
        scale_aff = Affine.scale(x_scale, y_scale)
        return trans_aff * scale_aff
