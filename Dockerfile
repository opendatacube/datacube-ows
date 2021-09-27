FROM osgeo/gdal:ubuntu-small-3.3.1

ENV LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    SHELL=bash

RUN apt-get update && apt-get install -y --no-install-recommends\
    curl \
    gnupg \
    # For Psycopg2
    libpq-dev libpcap-dev python3-dev \
    gcc \
    postgresql-client-12 \
    python3-pip \
    && apt-get autoclean && \
    apt-get autoremove && \
    rm -rf /var/lib/{apt,dpkg,cache,log}

RUN mkdir -p /conf
COPY requirements.txt constraints.txt /conf/
RUN pip install -r /conf/requirements.txt -c /conf/constraints.txt

# Copy source code and install it
RUN mkdir -p /code
WORKDIR /code
COPY . /code

RUN echo "version=\"$(python setup.py --version)\"" > datacube_ows/_version.py \
    && pip install --no-cache-dir .


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
