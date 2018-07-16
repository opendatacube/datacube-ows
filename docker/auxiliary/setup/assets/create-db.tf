terraform {
  required_version = ">= 0.10.0"

  backend "s3" {
    # This is an s3bucket you will need to create in your aws 
    # space
    bucket = "dea-devs-tfstate"

    region = "ap-southeast-2"

    # This is a DynamoDB table with the Primary Key set to LockID
    lock_table = "terraform"

    #Enable server side encryption on your terraform state
    encrypt = true
  }
}

# --------------
# Variables

variable "db_hostname" {
  default = "database.local"
}

variable "db_username" {}

variable "db_password" {}

variable "admin_username" {}

variable "admin_password" {}

variable "db_port" {
  default = 5432
}

variable "database" {}

# --------------
# AWS
provider "aws" {
  region = "ap-southeast-2"
}

provider "postgresql" {
  host     = "${var.db_hostname}"
  port     = "${var.db_port}"
  username = "${var.admin_username}"
  password = "${var.admin_password}"
}

resource "postgresql_role" "my_role" {
  name     = "${var.db_username}"
  login    = true
  password = "${var.db_password}"
}

resource "postgresql_database" "my_db" {
  name              = "${var.database}"
  owner             = "${postgresql_role.my_role.name}"
  connection_limit  = -1
  allow_connections = true
}
