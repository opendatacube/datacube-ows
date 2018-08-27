FROM opendatacube/wms

RUN curl -L https://github.com/docker/compose/releases/download/1.22.0/docker-compose-`uname -s`-`uname -m` > docker-compose && chmod +x docker-compose && mv docker-compose /usr/local/bin/

WORKDIR /code

ENTRYPOINT ["wms-entrypoint.sh"]