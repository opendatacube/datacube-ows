#!/bin/bash -e

for db in "odc_postgres" "odc_postgis"; do
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" <<-EOF
    CREATE DATABASE $db;
    GRANT ALL PRIVILEGES ON DATABASE $db TO opendatacubeusername;
EOF
  psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" -d $db <<-EOF
    CREATE EXTENSION POSTGIS;
EOF
done
