-- Creating NEW Materialised View Index 1/4

CREATE INDEX space_time_view_geom_idx_new
  ON space_time_view_new
  USING GIST (spatial_extent)
