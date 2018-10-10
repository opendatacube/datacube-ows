FROM opendatacube/datacube-core:1.6.1

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

# Terraform
RUN curl -o terraform.zip $(echo "https://releases.hashicorp.com/terraform/$(curl -s https://checkpoint-api.hashicorp.com/v1/check/terraform | jq -r -M '.current_version')/terraform_$(curl -s https://checkpoint-api.hashicorp.com/v1/check/terraform | jq -r -M '.current_version')_linux_amd64.zip")
RUN unzip terraform.zip && \
    mv terraform /usr/local/bin/terraform && \
    terraform -v 

RUN pip3 install \
    colour \
    flask \
    scikit-image \
    gevent \
    eventlet \
    gunicorn \
    gunicorn[gevent] \
    gunicorn[eventlet] \
    boto3 \
    rasterio==1.0.6 \
    ruamel.yaml \
    prometheus-client \
    flask-request-id-middleware \
    pytest-localserver \
    pytest-mock \
    requests \
    && rm -rf $HOME/.cache/pip

WORKDIR /code

ADD . .

RUN python3 setup.py install

COPY docker/wms-entrypoint.sh /usr/local/bin/wms-entrypoint.sh
COPY docker/get_wms_config.sh /usr/local/bin/get_wms_config.sh

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

CMD gunicorn -b '0.0.0.0:8000' -w 4 --timeout 120 datacube_wms:wms
