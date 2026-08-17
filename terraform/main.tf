terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# S3 Data Lake Module
module "s3_datalake" {
  source      = "./modules/s3"
  bucket_name = var.data_lake_bucket_name
  environment = var.environment
}

# IAM Role & Access Policy Module
module "iam" {
  source      = "./modules/iam"
  bucket_arn  = module.s3_datalake.bucket_arn
  environment = var.environment
}

# AWS Glue Catalog & Crawler Module
module "glue" {
  source        = "./modules/glue"
  bucket_id     = module.s3_datalake.bucket_id
  glue_role_arn = module.iam.glue_role_arn
  environment   = var.environment
}

# Amazon Redshift Warehouse Module
module "redshift" {
  source             = "./modules/redshift"
  cluster_identifier = var.redshift_cluster_identifier
  database_name      = var.redshift_database_name
  master_username    = var.redshift_master_username
  master_password    = var.redshift_master_password
  environment        = var.environment
}
