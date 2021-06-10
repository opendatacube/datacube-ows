ARG V_BASE=3.3.0
ARG py_env_path=/env

# Build python libs in env_builder
FROM opendatacube/geobase-builder:${V_BASE} as env_builder

# REVISIT: Does this do anything, given we've already declared it above?
ARG py_env_path

COPY requirements.txt /
COPY constraints.txt /
RUN /usr/local/bin/env-build-tool new /requirements.txt /constraints.txt ${py_env_path}

ENV PATH=${py_env_path}/bin:$PATH \
    PYTHONPATH=${py_env_path}

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

# Runner image starts here
FROM opendatacube/geobase-runner:${V_BASE}


ENV LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    SHELL=bash

RUN apt-get update && apt-get install -y --no-install-recommends\
    curl \
    gnupg \
    postgresql-client-12 \
    && rm -rf /var/lib/apt/lists/* /var/dpkg/* /var/log/dpkg.log

# Configure user
RUN useradd -m -s /bin/bash -N -g 100 -u 1001 ows
WORKDIR "/home/ows"

# Copy python libs, add them to the path, configure GDAL
ARG py_env_path
COPY --from=env_builder ${py_env_path} ${py_env_path}
ENV PATH=${py_env_path}/bin:$PATH \
    PYTHONPATH=${py_env_path} \
    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR" \
    CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif, .tiff" \
    GDAL_HTTP_MAX_RETRY="10" \
    GDAL_HTTP_RETRY_DELAY="1"


RUN chown 1000:100 /dev/shm

USER ows
CMD ["gunicorn", "-b", "0.0.0.0:8000", "--workers=3", "--threads=2", "-k", "gevent", "--timeout", "121", "--pid", "/home/ows/gunicorn.pid", "--log-level", "info", "--worker-tmp-dir", "/dev/shm", "--config", "python:datacube_ows.gunicorn_config", "datacube_ows.wsgi"]
