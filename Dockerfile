FROM ubuntu:22.10 as builder

# Setup build env for postgresql-client-14
USER root
RUN apt-get update -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --fix-missing --no-install-recommends \
            git \
            # For pybabel
            python3-distutils \
            # For Psycopg2
            libpq-dev python3-dev \
            gcc \
            python3-pip \
            postgresql-client-14 \
            # For Pyproj build \
            proj-bin proj-data libproj-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/dpkg/* /var/tmp/* /var/log/dpkg.log

ENV GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR"

# make folders
RUN mkdir -p /code
# Copy source code and install it
WORKDIR /code
COPY . /code

RUN echo "version=\"$(python3 setup.py --version)\"" > datacube_ows/_version.py \
    && pip install --no-cache-dir .[ops,test]

## Only install pydev requirements if arg PYDEV_DEBUG is set to 'yes'
ARG PYDEV_DEBUG="no"
RUN if [ "$PYDEV_DEBUG" = "yes" ]; then \
    pip install --no-cache-dir .[dev] \
;fi

RUN pip freeze

FROM osgeo/gdal:ubuntu-small-latest

# all the python pip installed libraries
COPY --from=builder  /usr/local/lib/python3.10/dist-packages /usr/local/lib/python3.10/dist-packages
COPY --from=builder  /usr/lib/python3/dist-packages /usr/lib/python3/dist-packages
COPY --from=builder  /usr/lib/python3.10/distutils/* /usr/lib/python3.10/distutils/
# postgres client
COPY --from=builder  /usr/lib/postgresql /usr/lib/postgresql
COPY --from=builder  /usr/share/postgresql /usr/share/postgresql
# perl5 is used for pg_isready
COPY --from=builder  /usr/share/perl5 /usr/share/perl5
COPY --from=builder  /usr/bin/pg_isready /usr/bin/pg_isready
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
# make folders for testing and keep code in image
RUN mkdir -p /code
# Copy source code and install it
WORKDIR /code
COPY . /code

# Configure user
RUN useradd -m -s /bin/bash -N -g 100 -u 1001 ows
WORKDIR "/home/ows"

ENV GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR" \
    CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif, .tiff" \
    GDAL_HTTP_MAX_RETRY="10" \
    GDAL_HTTP_RETRY_DELAY="1"

RUN chown 1000:100 /dev/shm

USER ows
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--workers=3", "--threads=2", "-k", "gevent", "--timeout", "121", "--pid", "/home/ows/gunicorn.pid", "--log-level", "info", "--worker-tmp-dir", "/dev/shm", "--config", "python:datacube_ows.gunicorn_config", "datacube_ows.wsgi"]
