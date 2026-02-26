# ============================================================
# Additional variables for ECS deployment
# (extends the existing variables in main.tf)
# ============================================================

# ============================================================
# Variables — Configuration for KODA infrastructure
# ============================================================

variable "aws_region" {
  description = "AWS region for deployment"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "koda"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be dev, staging, or prod."
  }
}

variable "session_ttl_seconds" {
  description = "DynamoDB TTL for session expiration (seconds)"
  type        = number
  default     = 1800 # 30 minutes
  validation {
    condition     = var.session_ttl_seconds > 0
    error_message = "Session TTL must be positive."
  }
}

variable "container_cpu" {
  description = "ECS task CPU units (256 = 0.25 vCPU)"
  type        = number
  default     = 512 # 0.5 vCPU
}

variable "container_memory" {
  description = "ECS task memory in MB"
  type        = number
  default     = 1024 # 1 GB
}

variable "container_port" {
  description = "Port exposed by Streamlit container"
  type        = number
  default     = 8501
}

variable "desired_count" {
  description = "Number of ECS tasks to run"
  type        = number
  default     = 1
}

variable "enable_logging" {
  description = "Enable CloudWatch Container Insights"
  type        = bool
  default     = true
}

variable "log_retention_days" {
  description = "CloudWatch log retention in days"
  type        = number
  default     = 7
}

variable "acm_certificate_arn" {
  description = "ACM certificate ARN for HTTPS on ALB. Set to empty string to skip HTTPS listener."
  type        = string
  default     = ""
}

variable "tags" {
  description = "Additional tags for all resources"
  type        = map(string)
  default     = {}
}
