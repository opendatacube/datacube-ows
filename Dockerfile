FROM ubuntu:20.04 as builder

# Setup build env for postgresql-client-12
USER root
RUN apt-get update -y \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --fix-missing --no-install-recommends \
            build-essential ca-certificates \
            git make cmake wget unzip libtool automake \
                # For Psycopg2
            libpq-dev python3-dev \
            gcc \
            python3-pip \
            postgresql-client-12 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* /var/dpkg/* /var/tmp/* /var/log/dpkg.log

# make folders
RUN mkdir -p /code
# Copy source code and install it
WORKDIR /code
COPY . /code

RUN cat requirements.txt
RUN echo "version=\"$(python setup.py --version)\"" > datacube_ows/_version.py \
    && pip install --no-cache-dir -r requirements.txt -c constraints.txt \
    && pip install --no-cache-dir .

FROM osgeo/gdal:ubuntu-small-latest
COPY --from=builder  /usr/local/lib/python3.8/dist-packages /usr/local/lib/python3.8/dist-packages
COPY --from=builder  /usr/local/bin/moto_server /usr/local/bin/moto_server
COPY --from=builder  /usr/share/perl5 /usr/share/perl5
COPY --from=builder  /usr/bin/pg_isready /usr/bin/pg_isready

# ENV LC_ALL=C.UTF-8 \
#     DEBIAN_FRONTEND=noninteractive \
#     SHELL=bash

# # install packages
RUN apt-get update && apt-get install -y --no-install-recommends\
#     git \
#     curl \
#     gnupg \
#     python-setuptools \
    postgresql-client-12 \
    # python3-pip \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/* /var/dpkg/* /var/tmp/* /var/log/dpkg.log

# make folders
RUN mkdir -p /code
# Copy source code and install it
WORKDIR /code
COPY . /code

# RUN cat requirements.txt
# # RUN echo "version=\"$(python setup.py --version)\"" > datacube_ows/_version.py \
# #     && pip install --no-cache-dir -r requirements.txt -c constraints.txt \
# #     && pip install --no-cache-dir .


# Configure user
RUN useradd -m -s /bin/bash -N -g 100 -u 1001 ows
WORKDIR "/home/ows"

## Only install pydev requirements if arg PYDEV_DEBUG is set to 'yes'
ARG PYDEV_DEBUG="no"
RUN if [ "$PYDEV_DEBUG" = "yes" ]; then \
    pip install --no-cache-dir pydevd-pycharm~=211.7142.13 \
;fi

ENV GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR" \
    CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif, .tiff" \
    GDAL_HTTP_MAX_RETRY="10" \
    GDAL_HTTP_RETRY_DELAY="1"

RUN chown 1000:100 /dev/shm

USER ows
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--workers=3", "--threads=2", "-k", "gevent", "--timeout", "121", "--pid", "/home/ows/gunicorn.pid", "--log-level", "info", "--worker-tmp-dir", "/dev/shm", "--config", "python:datacube_ows.gunicorn_config", "datacube_ows.wsgi"]
