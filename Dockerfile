# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.11.24@sha256:99ea34acedc870ba4ad11a1f540a1c04267c9f30aadc465a94406f52dfda2c36 AS uv

FROM ghcr.io/osgeo/gdal:ubuntu-small-3.13.1@sha256:836d1646ff9ab30d7db947c7b9690de55f34c2fd7cc5af6086a0854ccb378f59 AS base

LABEL org.opencontainers.image.source=https://github.com/opendatacube/datacube-ows
LABEL org.opencontainers.image.description="Datacube OWS"
LABEL org.opencontainers.image.licences="Apache-2.0"

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

FROM base AS builder

ARG PG_VERSION=18

# hadolint ignore=DL4006
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get -qq -y --no-install-recommends install dirmngr gpg gpg-agent  > /dev/null \
    && GNUPGHOME="$(mktemp -d)" \
    && export GNUPGHOME \
    && pg_key="B97B0AFCAA1A47F044F244A07FCC7D46ACCC4CF8" \
    && gpg --batch --keyserver keyserver.ubuntu.com --recv-keys "$pg_key" \
    && gpg --batch --export --armor "$pg_key" > /etc/apt/keyrings/postgres.gpg.asc \
    && gpgconf --kill all \
    && echo "deb [signed-by=/etc/apt/keyrings/postgres.gpg.asc] http://apt.postgresql.org/pub/repos/apt resolute-pgdg main $PG_VERSION" | tee /etc/apt/sources.list.d/postgres.list \
    && apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        git \
        # For shapely with --no-binary.
        libgeos-dev \
        libhdf5-dev \
        libnetcdf-dev \
        libudunits2-dev \
        # For psycopg2.
        libpq-dev \
        python3-dev

ENV UV_COMPILE_BYTECODE=0 \
    UV_HTTP_RETRIES=10 \
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.14

WORKDIR /build

COPY --link --from=uv /uv /uvx /usr/local/bin/

COPY --link pyproject.toml uv.lock /build/

# Use a separate cache volume for uv on opendatacube projects, so it is
# not inseparable from pip/poetry/npm/etc. cache stored in /root/.cache.
RUN --mount=type=cache,id=opendatacube-uv-cache,target=/root/.cache \
    uv sync --frozen --extra=ops --no-install-project \
      --no-binary-package fiona \
      --no-binary-package netcdf4 \
      --no-binary-package psycopg \
      --no-binary-package psycopg-c \
      --no-binary-package psycopg2 \
      --no-binary-package rasterio \
      --no-binary-package shapely

COPY --link . /build/

## Only install pydev requirements if arg PYDEV_DEBUG is set to 'yes'
ARG PYDEV_DEBUG="no"
ARG ENVIRONMENT=deployment
# The deployment image should not have binaries that aid an attacker to get their
# rootkit in place, and uv downloads over the network. There is no conditional
# copy in Docker, so truncate the uv binaries to 0 bytes to render them harmless
# in the resulting deployment image.
# hadolint ignore=SC2086
RUN --mount=type=cache,id=opendatacube-uv-cache,target=/root/.cache \
    EXTRAS=$( ([ "$ENVIRONMENT" = "deployment" ] && echo "--extra=ops --no-dev") || \
               ( ([ "$PYDEV_DEBUG" != "no" ] && echo "--extra=ops --extra=test --extra=dev") || \
                 echo "--extra=ops --extra=test") ) \
    && uv sync --frozen $EXTRAS --no-editable \
    && ([ "$ENVIRONMENT" != "deployment" ] || \
        (chmod 644 /usr/local/bin/uv* && \
         echo "" > /usr/local/bin/uv && \
         echo "" > /usr/local/bin/uvx))

FROM base

# Add login-script for UID/GID-remapping.
COPY --chown=root:root --link docker/files/remap-user.sh /usr/local/bin/remap-user.sh

COPY --from=builder --link /etc/apt/keyrings/postgres.gpg.asc /etc/apt/keyrings/postgres.gpg.asc
COPY --from=builder --link /etc/apt/sources.list.d/postgres.list /etc/apt/sources.list.d/postgres.list

ARG PG_VERSION=18
ARG ENVIRONMENT=deployment
# hadolint ignore=SC2086
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    export DEBIAN_FRONTEND=noninteractive \
    && EXTRAS=$([ "$ENVIRONMENT" = "deployment" ] || echo "postgresql-client-$PG_VERSION") \
    && apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
            gosu \
            tini \
            $EXTRAS \
    && mkdir /app \
    && chown ubuntu:ubuntu /app

COPY --from=builder --link /usr/local/bin/uv* /usr/local/bin/

COPY --from=builder --link --chown=1000:1000 /app /app

# Configure user
WORKDIR "/home/ubuntu"

ENV GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR" \
    CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif, .tiff" \
    GDAL_HTTP_MAX_RETRY="10" \
    GDAL_HTTP_RETRY_DELAY="1" \
    PATH=/app/bin:$PATH

ENTRYPOINT ["/usr/local/bin/remap-user.sh"]
CMD [\
    "gunicorn", \
    "-b", "0.0.0.0:8000", \
    "--workers=2", \
    "--threads=2", \
    "-k", \
    "gthread", \
    "--timeout", "121", \
    "--pid", "/home/ubuntu/gunicorn.pid", \
    "--log-level", "info", \
    "--worker-tmp-dir", "/dev/shm", \
    "--config", "python:datacube_ows.gunicorn_config", \
    "datacube_ows.startup_utils:create_app()"\
]
