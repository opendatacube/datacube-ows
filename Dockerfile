FROM osgeo/gdal:ubuntu-small-latest

ENV LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    SHELL=bash

# install packages
RUN apt-get update && apt-get install -y --no-install-recommends\
    git \
    curl \
    gnupg \
    python3-setuptools \
    # For Psycopg2
    libpq-dev libpcap-dev python3-dev \
    gcc \
    postgresql-client-12 \
    python3-pip \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/* /var/dpkg/* /var/tmp/* /var/log/dpkg.log

ENV PATH=${py_env_path}/bin:$PATH \
    PYTHONPATH=${py_env_path}

# make folders
RUN mkdir -p /code
# Copy source code and install it
COPY . /code
WORKDIR /code

RUN echo "version=\"$(python setup.py --version)\"" > datacube_ows/_version.py \
    && pip install --no-cache-dir -r requirements.txt -c constraints.txt \
    && pip install --no-cache-dir -e .


# Configure user
RUN useradd -m -s /bin/bash -N -g 100 -u 1001 ows
WORKDIR "/home/ows"

## Only install pydev requirements if arg PYDEV_DEBUG is set to 'yes'
ARG PYDEV_DEBUG="no"
RUN if [ "$PYDEV_DEBUG" = "yes" ]; then \
    pip install --no-cache-dir pydevd-pycharm~=211.7142.13 \
;fi

ENV PATH=${py_env_path}/bin:$PATH \
    PYTHONPATH=${py_env_path} \
    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR" \
    CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif, .tiff" \
    GDAL_HTTP_MAX_RETRY="10" \
    GDAL_HTTP_RETRY_DELAY="1"

RUN chown 1000:100 /dev/shm

USER ows
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--workers=3", "--threads=2", "-k", "gevent", "--timeout", "121", "--pid", "/home/ows/gunicorn.pid", "--log-level", "info", "--worker-tmp-dir", "/dev/shm", "--config", "python:datacube_ows.gunicorn_config", "datacube_ows.wsgi"]
