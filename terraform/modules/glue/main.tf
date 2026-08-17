resource "aws_glue_catalog_database" "datapulse_catalog" {
  name        = "datapulse_catalog_${var.environment}"
  description = "Glue Data Catalog for DataPulse Lakehouse"
}

resource "aws_glue_crawler" "processed_crawler" {
  database_name = aws_glue_catalog_database.datapulse_catalog.name
  name          = "datapulse-processed-crawler-${var.environment}"
  role          = var.glue_role_arn

  s3_target {
    path = "s3://${var.bucket_id}/processed/"
  }

  schema_change_policy {
    update_behavior = "UPDATE_IN_DATABASE"
    delete_behavior = "DEPRECATE_IN_DATABASE"
  }
}

resource "aws_glue_job" "etl_transformation_job" {
  name     = "datapulse-etl-transform-${var.environment}"
  role_arn = var.glue_role_arn
  glue_version = "4.0"
  number_of_workers = 2
  worker_type = "G.1X"

  command {
    script_location = "s3://${var.bucket_id}/scripts/glue_etl_job.py"
    python_version  = "3"
  }

  default_arguments = {
    "--job-language"        = "python"
    "--enable-metrics"      = "true"
    "--enable-continuous-cloudwatch-log" = "true"
    "--S3_BUCKET"           = var.bucket_id
    "--QUALITY_THRESHOLD"   = "95.0"
  }
}

output "glue_database_name" {
  value = aws_glue_catalog_database.datapulse_catalog.name
}
