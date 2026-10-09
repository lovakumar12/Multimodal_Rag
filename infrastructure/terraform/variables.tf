variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name prefix for AWS resources"
  type        = string
  default     = "multimodal-rag"
}

variable "environment" {
  description = "Deployment environment (production, staging, dev)"
  type        = string
  default     = "production"
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "CIDRs for public subnets across 2 AZs"
  type        = list(string)
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_subnet_cidrs" {
  description = "CIDRs for private subnets across 2 AZs"
  type        = list(string)
  default     = ["10.0.10.0/24", "10.0.11.0/24"]
}

variable "db_name" {
  description = "PostgreSQL database name"
  type        = string
  default     = "multimodal_rag"
}

variable "db_username" {
  description = "PostgreSQL master username"
  type        = string
  default     = "ragadmin"
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance class (e.g. db.t4g.medium or db.t4g.micro for dev)"
  type        = string
  default     = "db.t4g.medium"
}

variable "gemini_api_key" {
  description = "Google Gemini API Key for multimodal extraction and chat"
  type        = string
  sensitive   = true
  default     = ""
}

variable "openai_api_key" {
  description = "OpenAI API Key (optional fallback)"
  type        = string
  sensitive   = true
  default     = ""
}

variable "groq_api_key" {
  description = "Groq API Key for high-speed LLM generation"
  type        = string
  sensitive   = true
  default     = ""
}

variable "llm_provider" {
  description = "Primary LLM provider (groq, gemini, openai)"
  type        = string
  default     = "groq"
}

variable "llm_model" {
  description = "Primary LLM model name"
  type        = string
  default     = "openai/gpt-oss-120b"
}

variable "mongodb_uri" {
  description = "MongoDB URI connection string"
  type        = string
  sensitive   = true
  default     = ""
}

variable "backend_cpu" {
  description = "CPU units for backend Fargate task (1024 = 1 vCPU, 2048 = 2 vCPU)"
  type        = number
  default     = 2048
}

variable "backend_memory" {
  description = "Memory in MiB for backend Fargate task (4096 = 4GB)"
  type        = number
  default     = 4096
}

variable "backend_min_capacity" {
  description = "Minimum backend container task instances for autoscaling"
  type        = number
  default     = 2
}

variable "backend_max_capacity" {
  description = "Maximum backend container task instances for autoscaling"
  type        = number
  default     = 10
}

variable "frontend_cpu" {
  description = "CPU units for frontend task (512 = 0.5 vCPU)"
  type        = number
  default     = 512
}

variable "frontend_memory" {
  description = "Memory in MiB for frontend task (1024 = 1GB)"
  type        = number
  default     = 1024
}

variable "frontend_min_capacity" {
  description = "Minimum frontend container task instances for autoscaling"
  type        = number
  default     = 2
}

variable "frontend_max_capacity" {
  description = "Maximum frontend container task instances for autoscaling"
  type        = number
  default     = 8
}

variable "aws_account_id" {
  description = "AWS Account ID"
  type        = string
  default     = "175690104888"
}

variable "aws_access_key_id" {
  description = "AWS Access Key ID for compute instance ECR pull and S3 access"
  type        = string
  sensitive   = true
  default     = ""
}

variable "aws_secret_access_key" {
  description = "AWS Secret Access Key for compute instance ECR pull and S3 access"
  type        = string
  sensitive   = true
  default     = ""
}

