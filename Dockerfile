# syntax=docker/dockerfile:1
FROM ghcr.io/astral-sh/uv:0.9.18@sha256:5713fa8217f92b80223bc83aac7db36ec80a84437dbc0d04bbc659cae030d8c9 AS uv

FROM ghcr.io/osgeo/gdal:ubuntu-small-3.10.3@sha256:dab45abca3ca83695d442018692f4f8a0f41955871c57e6101d7f89a92375caa AS base

LABEL org.opencontainers.image.source=https://github.com/opendatacube/datacube-ows
LABEL org.opencontainers.image.description="Datacube OWS"
LABEL org.opencontainers.image.licences="Apache-2.0"

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

FROM base AS builder

ARG UV=https://github.com/astral-sh/uv/releases/download/0.8.6/uv-x86_64-unknown-linux-gnu.tar.gz

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    export DEBIAN_FRONTEND=noninteractive \
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
    UV_LINK_MODE=copy \
    UV_PROJECT_ENVIRONMENT=/app \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=python3.12

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

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
            gosu \
            tini \
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
    "--workers=3", \
    "-k", \
    "gevent", \
    "--timeout", "121", \
    "--pid", "/home/ubuntu/gunicorn.pid", \
    "--log-level", "info", \
    "--worker-tmp-dir", "/dev/shm", \
    "--config", "python:datacube_ows.gunicorn_config", \
    "datacube_ows.startup_utils:create_app()"\
]
