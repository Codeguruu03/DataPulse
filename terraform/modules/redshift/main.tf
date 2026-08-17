resource "aws_redshift_cluster" "dw_cluster" {
  cluster_identifier = var.cluster_identifier
  database_name      = var.database_name
  master_username    = var.master_username
  master_password    = var.master_password
  node_type          = "dc2.large"
  cluster_type       = "single-node"
  publicly_accessible = false
  skip_final_snapshot = true

  tags = {
    Name        = "DataPulse Redshift Warehouse"
    Environment = var.environment
    Platform    = "DataPulse"
  }
}

output "endpoint" {
  value = aws_redshift_cluster.dw_cluster.endpoint
}

output "database_name" {
  value = aws_redshift_cluster.dw_cluster.database_name
}
