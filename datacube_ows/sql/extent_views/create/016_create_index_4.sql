-- Creating Materialised View Index 4/4

CREATE unique INDEX space_time_view_idx
  ON space_time_view
  USING BTREE(id)
