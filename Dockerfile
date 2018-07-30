FROM opendatacube/datacube-core:2018-07-26

RUN pip3 install \
    flask scikit-image gunicorn boto3 \
    && rm -rf $HOME/.cache/pip

RUN apt-get update && apt-get install -y \
    wget unzip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

ADD . .

RUN python3 setup.py install

COPY docker/wms-entrypoint.sh /usr/local/bin/wms-entrypoint.sh
COPY docker/get_wms_config.sh /usr/local/bin/get_wms_config.sh

ENTRYPOINT ["wms-entrypoint.sh"]

CMD gunicorn -b '0.0.0.0:8000' -w 4 --timeout 120 datacube_wms:wms
