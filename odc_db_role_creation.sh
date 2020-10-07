#!/bin/bash
# Function : Initialize ODC DB User Roles
#############################################################################################################################
#  Activate the dea-prod-eks or dea-dev-eks according to environment in use
#  setup_aws_vault dea-dev-eks / dea-prod-eks
#  ap dea-dev-eks / dea-prod-eks
#
#  export DB_PORT=5432
#  screen -dmS pg_proxy kubectl port-forward deployment/pg-proxy $DB_PORT:5432 -n service
#  export ADMIN_PASSWORD=$(kubectl get secret db-aurora-admin -o yaml -n admin| grep "postgres-password:" | sed 's/postgres-password: //' | base64 -d -i)
#  export DB_HOSTNAME=localhost
#  export CLUSTER_ID=dea-dev-eks
#
#  Optional environment variables:
#  export REGION=<AWS_REGION>. Default is set to 'ap-southeast-2'.
#  export ODC_READER_USER=<ODC_READER_USER>. Default is set to 'odc_reader'.
#  export ODC_WRITER_USER=<ODC_WRITER_USER>. Default is set to 'odc_writer'.
#  export ODC_ADMIN_USER=<ODC_ADMIN_USER>. Default is set to 'odc_admin'.
#
#  Execution:
#  ./script/db_scripts/odc_db_role_creation.sh
#############################################################################################################################

# Random password generator from https://gist.github.com/earthgecko/3089509
random-string()
{
    cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w ${1:-32} | head -n 1
}

if [[ -z ${DB_HOSTNAME} || -z ${ADMIN_PASSWORD} || -z ${CLUSTER_ID} ]]; then
  echo "Please provide following env variables: DB_HOSTNAME, ADMIN_PASSWORD, CLUSTER_ID"
  exit 1;
fi

# DB_PASSWORD here is DB superuser password extracted from k8s secrets
# https://docs.dev.dea.ga.gov.au/internal_services/rds_databases.html?postgresql-major-version-upgrades-9-6-11-5#postgresql-major-version-upgrades-9-6-11-5
export PGPASSWORD=$ADMIN_PASSWORD
ADMIN_USER=superuser
DB_PORT=${DB_PORT:-"5432"}
REGION=${REGION:-"ap-southeast-2"}

# STEP 1: Create odc_reader role
################################################
ODC_READER_USER=${ODC_READER_USER:-"odc_reader"}

# Create odc_reader login role if it does not exist
echo "Creating $ODC_READER_USER user role"
createuser -h "$DB_HOSTNAME" -p "$DB_PORT" -U "$ADMIN_USER" "$ODC_READER_USER" || true

# Reset odc_reader DB user password
echo "Resetting $ODC_READER_USER user password"
ODC_READER_PASSWORD=$(random-string 16)
psql -h "$DB_HOSTNAME" -p "$DB_PORT" -U "$ADMIN_USER" -d postgres -c "ALTER USER ${ODC_READER_USER} WITH PASSWORD '${ODC_READER_PASSWORD}'"

echo "Adding $ODC_READER_USER credentials to param-store"
aws ssm put-parameter --region "${REGION}" \
  --name "/${CLUSTER_ID}/odc_reader/db.creds" \
  --value "${ODC_READER_USER}:${ODC_READER_PASSWORD}" \
  --description "${ODC_READER_USER} db role credentials" \
  --type "SecureString" --overwrite

# STEP 2: Create odc_writer role
################################################
export PGPASSWORD=$ADMIN_PASSWORD
ODC_WRITER_USER=${ODC_WRITER_USER:-"odc_writer"}

# Create odc_reader login role if it does not exist
echo "Creating $ODC_WRITER_USER user role"
createuser -h "$DB_HOSTNAME" -p "$DB_PORT" -U "$ADMIN_USER" "$ODC_WRITER_USER" || true

# Reset odc_reader DB user password
echo "Resetting $ODC_WRITER_USER user password"
ODC_WRITER_PASSWORD=$(random-string 16)
psql -h "$DB_HOSTNAME" -p "$DB_PORT" -U "$ADMIN_USER" -d postgres -c "ALTER USER ${ODC_WRITER_USER} WITH PASSWORD '${ODC_WRITER_PASSWORD}'"
psql -h "$DB_HOSTNAME" -p "$DB_PORT" -U "$ADMIN_USER" -d postgres -c "GRANT ${ODC_READER_USER} TO ${ODC_WRITER_USER}"

echo "Adding $ODC_WRITER_USER credentials to param-store"
aws ssm put-parameter --region "${REGION}" \
  --name "/${CLUSTER_ID}/odc_writer/db.creds" \
  --value "${ODC_WRITER_USER}:${ODC_WRITER_PASSWORD}" \
  --description "${ODC_WRITER_USER} db role credentials" \
  --type "SecureString" --overwrite

# STEP 3: Create odc_admin role
#####################################################
ODC_ADMIN_USER=${ODC_ADMIN_USER:-"odc_admin"}

# Create odc_admin login role if it does not exist
echo "Creating $ODC_ADMIN_USER user role"
# NOTE: giving createdb permission to odc_admin to setup NCI db
createuser -h "$DB_HOSTNAME" -p "$DB_PORT" -U "$ADMIN_USER" --createdb --pwprompt "$ODC_ADMIN_USER" || true

echo "Resetting $ODC_ADMIN_USER db user password"
ODC_ADMIN_PASSWORD=$(random-string 16)
psql -h "$DB_HOSTNAME" -p "$DB_PORT" -U "$ADMIN_USER" -d postgres -c "ALTER USER ${ODC_ADMIN_USER} WITH PASSWORD '${ODC_ADMIN_PASSWORD}'"
psql -h "$DB_HOSTNAME" -p "$DB_PORT" -U "$ADMIN_USER" -d postgres -c "GRANT ${ODC_WRITER_USER} TO ${ODC_ADMIN_USER}"
# NOTE: This GRANT needed for aws s3 import - NCI db setup
psql -h "$DB_HOSTNAME" -p "$DB_PORT" -U "$ADMIN_USER" -d postgres -c "GRANT rds_superuser TO ${ODC_ADMIN_USER}"

echo "Adding $ODC_ADMIN_USER credentials to param-store"
aws ssm put-parameter --region "${REGION}" \
  --name "/${CLUSTER_ID}/odc_admin/db.creds" \
  --value "${ODC_ADMIN_USER}:${ODC_ADMIN_PASSWORD}" \
  --description "${ODC_ADMIN_USER} db role credentials" \
  --type "SecureString" --overwrite