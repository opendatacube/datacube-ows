FROM opendatacube/wms:latest

RUN pip3 install \
    ruamel.yaml \
    awscli \
    && rm -rf $HOME/.cache/pip

WORKDIR archiving

COPY assets/archive-wrapper.sh archive-wrapper.sh
COPY assets/archive.sh archive.sh
RUN wget https://raw.githubusercontent.com/opendatacube/datacube-ecs/master/indexer/ls_s2_cog.py

WORKDIR ..

CMD /bin/bash -c archiving/archive-wrapper.sh