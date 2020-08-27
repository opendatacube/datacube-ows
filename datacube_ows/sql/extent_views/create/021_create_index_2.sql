-- Creating NEW Materialised View Index 2/4

CREATE INDEX space_time_view_time_idx_new
  ON space_time_view_new
  USING SPGIST (temporal_extent)
