ARG V_BASE=-3.0.4
ARG py_env_path=/env
FROM opendatacube/geobase:wheels${V_BASE} as env_builder

COPY requirements.txt /
RUN /usr/local/bin/env-build-tool new /requirements.txt ${py_env_path}

COPY requirements-docker.txt /
RUN /usr/local/bin/env-build-tool extend /requirements-docker.txt ${py_env_path}

FROM opendatacube/geobase:runner${V_BASE}

ENV LC_ALL=C.UTF-8 \
    DEBIAN_FRONTEND=noninteractive \
    SHELL=bash

RUN apt-get update && apt install -y \
    curl \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install keys for postgres-11, then install deps
RUN curl https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt/ bionic-pgdg main" > /etc/apt/sources.list.d/pgdg.list' && \
    apt-get update && apt install -y \
    postgresql-client-11 \
    && rm -rf /var/lib/apt/lists/*

ARG py_env_path
COPY --chown=1000:100 --from=env_builder $py_env_path $py_env_path

ENV PATH=${py_env_path}/bin:$PATH

CMD gunicorn -b '0.0.0.0:8000' --workers=3 --threads=2 -k gevent --timeout 121 --pid gunicorn.pid --log-level info --worker-tmp-dir /dev/shm datacube_ows.wsgi