# Note that this is now pinned to a fixed version.  Remember to check for new versions periodically.
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.2 AS builder

# Environment is test or deployment.
ARG ENVIRONMENT=deployment

# Setup build env for postgresql-client-16
USER root
RUN apt-get update -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --fix-missing --no-install-recommends \
            git \
            # For Psycopg2
            libpq-dev python3-dev \
            gcc \
            python3-pip \
            postgresql-client-16 \
            # For Pyproj build \
            proj-bin libproj-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/dpkg/* /var/tmp/* /var/log/dpkg.log

WORKDIR /build

RUN python3 -m pip --disable-pip-version-check -q wheel --no-binary psycopg2 psycopg2 \
    && ([ "$ENVIRONMENT" = "deployment" ] || \
          python3 -m pip --disable-pip-version-check -q wheel --no-binary pyproj pyproj)

# Should match builder base.
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.2

# Environment is test or deployment.
ARG ENVIRONMENT=deployment
RUN export DEBIAN_FRONTEND=noninteractive \
    && apt-get update -y \
    && apt-get install -y --no-install-recommends \
            git \
            gosu \
            python3-pip \
            tini \
    && ([ "$ENVIRONMENT" = "deployment" ] || \
          apt-get install -y --no-install-recommends \
            proj-bin) \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/dpkg/* /var/tmp/* /var/log/dpkg.log

# Add login-script for UID/GID-remapping.
COPY --chown=root:root --link docker/files/remap-user.sh /usr/local/bin/remap-user.sh

# Copy source code and install it
WORKDIR /code
COPY . /code

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
       (rm -rf /code/* /code/.git* && \
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
