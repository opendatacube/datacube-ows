#!/bin/bash

set -e
# Convert vars to TF specific ones
export TF_VAR_db_hostname=$DB_HOSTNAME
export TF_VAR_database=$DB_DATABASE
export TF_VAR_db_username=$DB_USERNAME
export TF_VAR_db_password=$DB_PASSWORD
export TF_VAR_admin_username=$ADMIN_USERNAME
export TF_VAR_admin_password=$ADMIN_PASSWORD

terraform init -backend-config="bucket=$STATE_BUCKET" -backend-config="key=$DB_DATABASE.tfstate" && terraform apply -auto-approve
