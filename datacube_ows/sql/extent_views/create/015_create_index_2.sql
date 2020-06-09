-- Creating Materialised View Index 2/4

     CREATE INDEX space_time_view_time_idx
  ON space_time_view
  USING SPGIST (temporal_extent)
