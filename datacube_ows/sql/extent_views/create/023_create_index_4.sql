-- Creating NEW Materialised View Index 4/4

CREATE unique INDEX space_time_view_idx_new
  ON space_time_view_new
  USING BTREE(id)
