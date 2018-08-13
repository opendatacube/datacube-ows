FROM opendatacube/wms:latest

# Make sure apt doesn't ask questions
ENV DEBIAN_FRONTEND=noninteractive

# install psql for WMS database script
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client awscli curl jq\
    && rm -rf /var/lib/apt/lists/*


# For alternate config without param store
RUN mkdir setup
WORKDIR setup
COPY assets/create-db.sh create-db.sh

CMD ./create-db.sh
