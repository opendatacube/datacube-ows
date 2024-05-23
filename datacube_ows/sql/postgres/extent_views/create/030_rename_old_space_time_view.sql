-- Renaming old spacetime view (OWS down)

ALTER MATERIALIZED VIEW IF EXISTS ows.space_time_view
RENAME TO space_time_view_old
