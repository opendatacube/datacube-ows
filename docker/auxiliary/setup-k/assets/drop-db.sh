#! /usr/bin/env bash
# Force non superusers to disconnect from the database
# and attempt to drop it
set -e

PGPASSWORD=$ADMIN_PASSWORD psql -h $DB_HOSTNAME -p $DB_PORT -U $ADMIN_USERNAME -d postgres <<-SQL
ALTER DATABASE "$DB_DATABASE" OWNER TO $ADMIN_USERNAME;
ALTER DATABASE "$DB_DATABASE" CONNECTION LIMIT 0;

SELECT pg_terminate_backend(pid)
    FROM pg_stat_activity
    WHERE datname="$DB_DATABASE";

DROP DATABASE "$DB_DATABASE";

DROP ROLE "$DB_USERNAME";
SQL
