-- Giving other schemas access to PostGIS functions installed in the public schema

ALTER DATABASE "{database}"
SET search_path = public, agdc
