ARG V_BASE=-3.0.4
ARG py_env_path=/env

# Build python libs in env_builder
FROM opendatacube/geobase:wheels${V_BASE} as env_builder
ARG py_env_path

COPY requirements.txt /
RUN /usr/local/bin/env-build-tool new /requirements.txt ${py_env_path}

ENV PATH=${py_env_path}/bin:$PATH \
    PYTHONPATH=${py_env_path}

# Copy source code and install it
RUN mkdir -p /code
WORKDIR /code
ADD . /code

RUN pip install .


# Runner image starts here
FROM opendatacube/geobase:runner${V_BASE}

ENV LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    SHELL=bash

RUN apt-get update && apt install -y \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install postgres client 11
RUN curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ bionic-pgdg main" > /etc/apt/sources.list.d/pgdg.list' && \
    apt-get update && apt-get install -y \
    postgresql-client-11 \
    && rm -rf /var/lib/apt/lists/*

# Configure user
RUN useradd -m -s /bin/bash -N -g 100 -u 1000 ows
WORKDIR "/home/ows"

# Copy python libs, add them to the path, configure GDAL
ARG py_env_path
COPY --chown=1000:100 --from=env_builder $py_env_path $py_env_path
ENV PATH=${py_env_path}/bin:$PATH \
    PYTHONPATH=${py_env_path} \
    GDAL_DISABLE_READDIR_ON_OPEN="EMPTY_DIR" \
    CPL_VSIL_CURL_ALLOWED_EXTENSIONS=".tif, .tiff" \
    GDAL_HTTP_MAX_RETRY="10" \
    GDAL_HTTP_RETRY_DELAY="1" 

## Only install pydev requirements if arg PYDEV_DEBUG is set to 'yes'
ARG PYDEV_DEBUG="no"
RUN if [ "$PYDEV_DEBUG" = "yes" ]; then \
    pip install pydevd-pycharm~=201.6668.115 \
;fi

RUN chown 1000:100 /dev/shm

USER ows
CMD gunicorn -b '0.0.0.0:8000' --workers=3 --threads=2 -k gevent --timeout 121 --pid /home/ows/gunicorn.pid --log-level info --worker-tmp-dir /dev/shm datacube_ows.wsgi