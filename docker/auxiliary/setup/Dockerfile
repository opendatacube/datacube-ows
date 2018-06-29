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

WORKDIR /code/firsttime

COPY assets/setup.sh setup.sh

WORKDIR /code

COPY assets/main.tf main.tf
ENTRYPOINT terraform init -backend-config="bucket=$TF_VAR_state_bucket" -backend-config="key=db-$TF_VAR_cluster-$TF_VAR_database.tfstate" && terraform apply -auto-approve
