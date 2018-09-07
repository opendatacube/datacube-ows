FROM opendatacube/wms:latest

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install \
    ruamel.yaml \
    && rm -rf $HOME/.cache/pip

WORKDIR indexing

COPY assets/update_ranges.sh update_ranges.sh
COPY assets/update_ranges_wrapper.sh update_ranges_wrapper.sh
RUN wget https://raw.githubusercontent.com/opendatacube/datacube-dataset-config/master/scripts/index_from_s3_bucket.py \
    -O ls_s2_cog.py

WORKDIR ..

COPY assets/create-index.sh create-index.sh

CMD ./create-index.sh
