FROM python:3.8 AS compile-image
RUN apt-get update

ENV LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    SHELL=bash

RUN apt-get install -y --no-install-recommends build-essential gcc
RUN echo "deb http://apt.postgresql.org/pub/repos/apt/ bionic-pgdg main" > /etc/apt/sources.list.d/pgdg.list
RUN wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -
# install packages
RUN apt-get update && apt-get install -y --no-install-recommends\
    git \
    curl \
    gnupg \
    # For Psycopg2
    libpq-dev libpcap-dev python3-dev \
    postgresql-client-12 \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/* /var/dpkg/* /var/tmp/* /var/log/dpkg.log

RUN python -m venv /opt/venv
# Make sure we use the virtualenv:
ENV PATH="/opt/venv/bin:$PATH"

# make folders
RUN mkdir -p /code
# Copy source code and install it
WORKDIR /code
COPY . /code

RUN echo "version=\"$(python setup.py --version)\"" > datacube_ows/_version.py \
    && pip install --no-cache-dir -r requirements.txt -c constraints.txt \
    && pip install --no-cache-dir .

## Only install pydev requirements if arg PYDEV_DEBUG is set to 'yes'
ARG PYDEV_DEBUG="no"
RUN if [ "$PYDEV_DEBUG" = "yes" ]; then \
    pip install --no-cache-dir pydevd-pycharm~=211.7142.13 \
;fi

FROM osgeo/gdal:ubuntu-small-3.3.1
COPY --from=compile-image /opt/venv /opt/venv

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
