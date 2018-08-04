FROM opendatacube/wms:0.2.8

RUN pip3 install \
    ruamel.yaml \
    && rm -rf $HOME/.cache/pip

WORKDIR indexing

COPY assets/update_ranges.sh update_ranges.sh
COPY assets/update_ranges_wrapper.sh update_ranges_wrapper.sh
RUN wget https://raw.githubusercontent.com/opendatacube/datacube-ecs/master/indexer/ls_s2_cog.py


WORKDIR ..

CMD /bin/bash -c indexing/update_ranges_wrapper.sh
