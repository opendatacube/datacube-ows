-- Creating NEW Materialised View Index 3/4

CREATE INDEX space_time_view_ds_idx_new
  ON space_time_view_new
  USING BTREE(dataset_type_ref)
