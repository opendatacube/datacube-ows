FROM opendatacube/wms:latest

# Make sure apt doesn't ask questions
ENV DEBIAN_FRONTEND=noninteractive

# install psql for WMS database script
RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client awscli curl jq\
    && rm -rf /var/lib/apt/lists/*

# Terraform
RUN curl -o terraform.zip $(echo "https://releases.hashicorp.com/terraform/$(curl -s https://checkpoint-api.hashicorp.com/v1/check/terraform | jq -r -M '.current_version')/terraform_$(curl -s https://checkpoint-api.hashicorp.com/v1/check/terraform | jq -r -M '.current_version')_linux_amd64.zip")
RUN unzip terraform.zip && \
    mv terraform /usr/local/bin/terraform && \
    terraform -v 


# For alternate config without param store
RUN mkdir setup
WORKDIR setup
COPY assets/create-db.sh create-db.sh
COPY assets/create-db.tf create-db.tf

CMD ./create-db.sh
