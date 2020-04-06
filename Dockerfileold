FROM opendatacube/datacube-core:1.7

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3-matplotlib \
    python3-pil\
    libpng-dev \
    wget \
    unzip \
    git \
    jq \
    awscli \
    curl \
    libev-dev \
    gpg-agent \
    && rm -rf /var/lib/apt/lists/*


RUN curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add -

RUN sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ bionic-pgdg main" > /etc/apt/sources.list.d/pgdg.list'

RUN apt-get update

RUN apt install -y postgresql-client-11

WORKDIR /code

ADD . .

RUN pip3 install --upgrade pip \
    && rm -rf $HOME/.cache/pip

RUN pip3 install -r requirements.txt \
    && rm -rf $HOME/.cache/pip

RUN pip install -U 'aiobotocore[awscli,boto3]' \
    && rm -rf $HOME/.cache/pip

RUN pip3 install . \
  && rm -rf $HOME/.cache/pip

COPY docker/ows-entrypoint.sh /usr/local/bin/ows-entrypoint.sh
COPY docker/update-and-reload.sh /usr/local/bin/update-and-reload.sh

# Create Directory inside python path for config - mount your config volume here!
RUN mkdir -p /code/datacube_ows/config

WORKDIR /code

ENTRYPOINT ["ows-entrypoint.sh"]

# Increase the maximum number of open file descriptors for a given process, ulimit (65535*3 = 196605)
#RUN ulimit -n 196605

CMD gunicorn -b '0.0.0.0:8000' --workers=3 --threads=2 -k gevent --timeout 121 --pid gunicorn.pid --log-level info --worker-tmp-dir /dev/shm datacube_ows.wsgi
