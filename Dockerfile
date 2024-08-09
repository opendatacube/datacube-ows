# Note that this is now pinned to a fixed version.  Remember to check for new versions periodically.
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.1 AS builder

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
            proj-bin proj-data libproj-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/dpkg/* /var/tmp/* /var/log/dpkg.log

ENV GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"

# Copy source code and install it
WORKDIR /code
COPY . /code

RUN echo "version=\"$(python3 setup.py --version)\"" > datacube_ows/_version.py \
    && pip --disable-pip-version-check install --no-cache-dir .[ops,test] --break-system-packages

## Only install pydev requirements if arg PYDEV_DEBUG is set to 'yes'
ARG PYDEV_DEBUG="no"
RUN if [ "$PYDEV_DEBUG" = "yes" ]; then \
    pip --disable-pip-version-check install --no-cache-dir .[dev] --break-system-packages \
;fi

RUN pip freeze

# Should match builder base.
FROM ghcr.io/osgeo/gdal:ubuntu-small-3.9.1

RUN apt-get update -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
            gosu \
            tini \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/dpkg/* /var/tmp/* /var/log/dpkg.log

# Add login-script for UID/GID-remapping.
COPY --chown=root:root --link docker/files/remap-user.sh /usr/local/bin/remap-user.sh

# all the python pip installed libraries
COPY --from=builder  /usr/local/lib/python3.12/dist-packages /usr/local/lib/python3.12/dist-packages
COPY --from=builder  /usr/lib/python3/dist-packages /usr/lib/python3/dist-packages
# postgres client
COPY --from=builder  /usr/lib/postgresql /usr/lib/postgresql
COPY --from=builder  /usr/share/postgresql /usr/share/postgresql
# datacube cli
COPY --from=builder  /usr/local/bin/datacube /usr/local/bin/datacube
# datacube-ows cli
COPY --from=builder  /usr/local/bin/datacube-ows /usr/local/bin/datacube-ows
# datacube-ows-update cli
COPY --from=builder  /usr/local/bin/datacube-ows-update /usr/local/bin/datacube-ows-update
# datacube-ows-cfg check
COPY --from=builder  /usr/local/bin/datacube-ows-cfg /usr/local/bin/datacube-ows-cfg
# flask cli
COPY --from=builder  /usr/local/bin/flask /usr/local/bin/flask
# gunicorn cli
COPY --from=builder  /usr/local/bin/gunicorn /usr/local/bin/gunicorn
# pybabel cli
COPY --from=builder  /usr/local/bin/pybabel /usr/local/bin/pybabel

# Copy source code and install it
WORKDIR /code
COPY . /code

# Configure user
WORKDIR "/home/ubuntu"

ENV GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR" \
    CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif, .tiff" \
    GDAL_HTTP_MAX_RETRY="10" \
    GDAL_HTTP_RETRY_DELAY="1"

ENTRYPOINT ["/usr/local/bin/remap-user.sh"]
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--workers=3", "--threads=2", "-k", "gevent", "--timeout", "121", "--pid", "/home/ubuntu/gunicorn.pid", "--log-level", "info", "--worker-tmp-dir", "/dev/shm", "--config", "python:datacube_ows.gunicorn_config", "datacube_ows.wsgi"]
