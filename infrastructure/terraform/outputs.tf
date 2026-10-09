output "alb_dns_name" {
  description = "Public URL of the Application Load Balancer"
  value       = "http://${aws_lb.main.dns_name}"
}

output "backend_ecr_url" {
  description = "ECR Repository URL for Backend"
  value       = aws_ecr_repository.backend.repository_url
}

output "frontend_ecr_url" {
  description = "ECR Repository URL for Frontend"
  value       = aws_ecr_repository.frontend.repository_url
}

output "s3_assets_bucket" {
  description = "S3 Bucket Name for Multimodal Assets"
  value       = aws_s3_bucket.assets.bucket
}

output "rds_endpoint" {
  description = "PostgreSQL RDS Database Endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "app_server_public_ip" {
  description = "Public IP of the Application Server"
  value       = aws_instance.app_server.public_ip
}

output "app_server_private_ip" {
  description = "Private IP of the Application Server (registered with ALB)"
  value       = aws_instance.app_server.private_ip
}
