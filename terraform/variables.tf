variable "aws_region" {
  description = "AWS Region for DataPulse cloud infrastructure"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "data_lake_bucket_name" {
  description = "Name of S3 bucket for DataPulse Lakehouse"
  type        = string
  default     = "datapulse-lakehouse-datalake"
}

variable "redshift_cluster_identifier" {
  description = "Identifier for Amazon Redshift cluster"
  type        = string
  default     = "datapulse-redshift-cluster"
}

variable "redshift_database_name" {
  description = "Database name for Redshift"
  type        = string
  default     = "datapulse_dw"
}

variable "redshift_master_username" {
  description = "Master username for Redshift"
  type        = string
  default     = "datapulse_admin"
}

variable "redshift_master_password" {
  description = "Master password for Redshift"
  type        = string
  sensitive   = true
  default     = "DataPulseSecurePass2026!"
}
