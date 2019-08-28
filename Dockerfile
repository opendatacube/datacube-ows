FROM opendatacube/datacube-core:1.7

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3-matplotlib \
    python3-pil\
    libpng-dev \
    wget \
    unzip \
    git \
    postgresql-client \
    jq \
    awscli \
    curl \
    libev-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

ADD . .

RUN pip3 install --upgrade pip \
    && rm -rf $HOME/.cache/pip

RUN pip3 install -r requirements.txt \
    && rm -rf $HOME/.cache/pip

RUN pip install -U 'aiobotocore[awscli,boto3]' \
    && rm -rf $HOME/.cache/pip

RUN pip install --extra-index-url="https://packages.dea.gadevs.ga" \
    odc-apps-cloud \
    odc-apps-dc-tools \
    && rm -rf $HOME/.cache/pip

# RUN pip3 install -r requirements-opencensus.txt \
#     && rm -rf $HOME/.cache/pip

RUN pip3 install . \
  && rm -rf $HOME/.cache/pip

COPY docker/wms-entrypoint.sh /usr/local/bin/wms-entrypoint.sh
COPY docker/get_wms_config.sh /usr/local/bin/get_wms_config.sh
COPY docker/update-and-reload.sh /usr/local/bin/update-and-reload.sh

# Perform setup install
RUN mkdir -p /code/setup
WORKDIR /code/setup

COPY docker/auxiliary/setup-k/assets/create-db.sh .
COPY docker/auxiliary/setup-k/assets/drop-db.sh .

# Perform index install
RUN mkdir -p /code/index/indexing
WORKDIR /code/index/indexing

COPY docker/auxiliary/index-k/assets/update_ranges.sh .
COPY docker/auxiliary/index-k/assets/update_ranges_wrapper.sh .
ADD https://raw.githubusercontent.com/opendatacube/datacube-dataset-config/master/scripts/index_from_s3_bucket.py ls_s2_cog.py

WORKDIR /code/index
COPY docker/auxiliary/index-k/assets/create-index.sh .

# Archive install
RUN mkdir -p /code/archive/archiving
WORKDIR /code/archive

COPY docker/auxiliary/archive/assets/archive-wrapper.sh .

WORKDIR /code/archive/archiving
COPY docker/auxiliary/archive/assets/archive.sh .
ADD https://raw.githubusercontent.com/opendatacube/datacube-dataset-config/master/scripts/index_from_s3_bucket.py ls_s2_cog.py

WORKDIR /code

ENTRYPOINT ["wms-entrypoint.sh"]

# Increase the maximum number of open file descriptors for a given process, ulimit (65535*3 = 196605)
CMD ulimit -n 196605

CMD gunicorn -b '0.0.0.0:8000' --workers=3 --threads=2 -k gevent --timeout 121 --pid gunicorn.pid --log-level info --worker-tmp-dir /dev/shm datacube_wms.wsgi
