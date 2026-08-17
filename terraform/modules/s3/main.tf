resource "aws_s3_bucket" "data_lake" {
  bucket        = var.bucket_name
  force_destroy = true

  tags = {
    Name        = "DataPulse Lakehouse Bucket"
    Environment = var.environment
    Platform    = "DataPulse"
  }
}

resource "aws_s3_bucket_versioning" "versioning" {
  bucket = aws_s3_bucket.data_lake.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "encryption" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Prefixes representing data tiers
resource "aws_s3_object" "raw_tier" {
  bucket = aws_s3_bucket.data_lake.id
  key    = "raw/"
}

resource "aws_s3_object" "processed_tier" {
  bucket = aws_s3_bucket.data_lake.id
  key    = "processed/"
}

resource "aws_s3_object" "quarantine_tier" {
  bucket = aws_s3_bucket.data_lake.id
  key    = "quarantine/"
}

output "bucket_id" {
  value = aws_s3_bucket.data_lake.id
}

output "bucket_arn" {
  value = aws_s3_bucket.data_lake.arn
}
