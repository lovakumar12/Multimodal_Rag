# EC2 Compute Host for Backend and Frontend Containers behind Application Load Balancer
resource "aws_instance" "app_server" {
  ami                         = "ami-091138d0f0d41ff90" # Ubuntu 24.04 LTS
  instance_type               = "t3.medium"
  key_name                    = "mmrag-key"
  subnet_id                   = aws_subnet.public[0].id
  vpc_security_group_ids      = [aws_security_group.ecs_backend.id, aws_security_group.ecs_frontend.id]
  associate_public_ip_address = true

  root_block_device {
    volume_size           = 30
    volume_type           = "gp3"
    delete_on_termination = true
  }

  user_data_replace_on_change = true

  user_data = <<-EOF
              #!/bin/bash
              set -ex
              exec > >(tee -a /var/log/user-data.log | logger -t user-data -s 2>/dev/console) 2>&1

              # 1. Update and install Docker, Git & AWS CLI
              apt-get update -y
              apt-get install -y docker.io curl unzip git
              systemctl start docker
              systemctl enable docker

              curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
              unzip -q awscliv2.zip
              ./aws/install

              # 2. Authenticate Docker with Amazon ECR
              export AWS_ACCESS_KEY_ID="${var.aws_access_key_id}"
              export AWS_SECRET_ACCESS_KEY="${var.aws_secret_access_key}"
              export AWS_DEFAULT_REGION="${var.aws_region}"

              aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin ${var.aws_account_id}.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com

              # 3. Create shared bridge network
              docker network create app-net || true

              # 4. Clone repository and build backend image on EC2 (fast 5Gbps AWS network)
              rm -rf /app
              git clone https://github.com/lovakumar12/Multimodal_Rag.git /app
              cd /app
              docker build -f backend/Dockerfile -t ${aws_ecr_repository.backend.repository_url}:latest .
              docker push ${aws_ecr_repository.backend.repository_url}:latest || true

              # 5. Pull Frontend image from ECR
              docker pull ${aws_ecr_repository.frontend.repository_url}:latest

              # 6. Start Backend Container (Port 8000)
              docker run -d \
                --name multimodal-rag-backend \
                --network app-net \
                --network-alias backend \
                --restart always \
                -p 8000:8000 \
                -e AWS_ACCESS_KEY_ID="${var.aws_access_key_id}" \
                -e AWS_SECRET_ACCESS_KEY="${var.aws_secret_access_key}" \
                -e AWS_REGION="${var.aws_region}" \
                -e OBJECT_STORAGE_BUCKET="${aws_s3_bucket.assets.bucket}" \
                -e STORAGE_BACKEND="s3" \
                -e GROQ_API_KEY="${var.groq_api_key}" \
                -e GEMINI_API_KEY="${var.gemini_api_key}" \
                -e LLM_PROVIDER="groq" \
                -e LLM_MODEL="${var.llm_model}" \
                -e MONGODB_URI="${var.mongodb_uri}" \
                -e DATABASE_URL="postgresql+asyncpg://${var.db_username}:${var.db_password}@${aws_db_instance.postgres.endpoint}/${var.db_name}" \
                ${aws_ecr_repository.backend.repository_url}:latest

              # 7. Start Frontend Container (Port 80)
              docker run -d \
                --name multimodal-rag-frontend \
                --network app-net \
                --restart always \
                -p 80:80 \
                ${aws_ecr_repository.frontend.repository_url}:latest

              EOF

  depends_on = [
    aws_db_instance.postgres,
    aws_ecr_repository.backend,
    aws_ecr_repository.frontend
  ]

  tags = {
    Name        = "${var.project_name}-app-server-${var.environment}"
    Project     = var.project_name
    Environment = var.environment
  }
}

# Register EC2 IP target with Backend Target Group (Port 8000)
resource "aws_lb_target_group_attachment" "backend" {
  target_group_arn = aws_lb_target_group.backend.arn
  target_id        = aws_instance.app_server.private_ip
  port             = 8000
}

# Register EC2 IP target with Frontend Target Group (Port 80)
resource "aws_lb_target_group_attachment" "frontend" {
  target_group_arn = aws_lb_target_group.frontend.arn
  target_id        = aws_instance.app_server.private_ip
  port             = 80
}
