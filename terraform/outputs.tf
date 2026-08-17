output "s3_data_lake_bucket" {
  description = "S3 Data Lake Bucket Name"
  value       = module.s3_datalake.bucket_id
}

output "glue_database" {
  description = "AWS Glue Catalog Database"
  value       = module.glue.glue_database_name
}

output "redshift_endpoint" {
  description = "Amazon Redshift Endpoint"
  value       = module.redshift.endpoint
}
