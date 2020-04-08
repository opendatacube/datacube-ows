FROM kartoza/postgis:11.0-2.5 as donor
ENV PGDATA=/pgdata
COPY dump.sql /docker-entrypoint-initdb.d/