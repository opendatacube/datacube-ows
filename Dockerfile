# syntax=docker/dockerfile:1
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.10.3@sha256:dab45abca3ca83695d442018692f4f8a0f41955871c57e6101d7f89a92375caa AS base

LABEL org.opencontainers.image.source=https://github.com/opendatacube/datacube-ows
LABEL org.opencontainers.image.description="Datacube OWS"
LABEL org.opencontainers.image.licences="Apache-2.0"

ENV LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

FROM base AS builder

# Setup build env for postgresql-client-16
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
            git \
            # For Psycopg2
            libpq-dev python3-dev \
            gcc \
            python3-pip \
            postgresql-client-16 \
            # For Pyproj build \
            proj-bin libproj-dev

WORKDIR /build

# Environment is test or deployment.
ARG ENVIRONMENT=deployment

RUN python3 -m pip --disable-pip-version-check -q wheel --no-binary psycopg2 psycopg2 \
    && ([ "$ENVIRONMENT" = "deployment" ] || \
          python3 -m pip --disable-pip-version-check -q wheel --no-binary pyproj pyproj)

FROM base

# Add login-script for UID/GID-remapping.
COPY --chown=root:root --link docker/files/remap-user.sh /usr/local/bin/remap-user.sh

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    export DEBIAN_FRONTEND=noninteractive \
    && apt-get update \
    && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends \
            git \
            gosu \
            python3-pip \
            tini

# Environment is test or deployment.
ARG ENVIRONMENT=deployment
RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    export DEBIAN_FRONTEND=noninteractive \
    && ([ "$ENVIRONMENT" = "deployment" ] || \
          apt-get install -y --no-install-recommends \
            proj-bin)

# Copy source code and install it
WORKDIR /src
COPY . /src

## Only install pydev requirements if arg PYDEV_DEBUG is set to 'yes'
ARG PYDEV_DEBUG="no"
COPY --from=builder --link /build/*.whl ./
RUN EXTRAS=$([ "$ENVIRONMENT" = "deployment" ] || echo ",test") && \
    python3 -m pip --disable-pip-version-check install ./*.whl --break-system-packages && \
    rm ./*.whl && \
    echo "version=\"$(python3 setup.py --version)\"" > datacube_ows/_version.py  && \
    python3 -m pip --disable-pip-version-check install --no-cache-dir ".[ops$EXTRAS]" --break-system-packages && \
    ([ "$PYDEV_DEBUG" != "yes" ] || \
       python3 -m pip --disable-pip-version-check install --no-cache-dir .[dev] --break-system-packages) && \
    python3 -m pip freeze && \
    ([ "$ENVIRONMENT" != "deployment" ] || \
       (rm -rf /src/* /src/.git* && \
        apt-get purge -y \
           git \
           git-man \
           python3-pip))

# Configure user
WORKDIR "/home/ubuntu"

ENV GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR" \
    CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif, .tiff" \
    GDAL_HTTP_MAX_RETRY="10" \
    GDAL_HTTP_RETRY_DELAY="1"

ENTRYPOINT ["/usr/local/bin/remap-user.sh"]
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--workers=3", "-k", "gevent", "--timeout", "121", "--pid", "/home/ubuntu/gunicorn.pid", "--log-level", "info", "--worker-tmp-dir", "/dev/shm", "--config", "python:datacube_ows.gunicorn_config", "datacube_ows.wsgi"]
