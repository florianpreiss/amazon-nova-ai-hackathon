# ============================================================
# KODA — Terraform Infrastructure
# AWS resources for the KODA multi-agent system
# ============================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.40.0"
    }
  }
}

# ── Variables ──────────────────────────────────────────

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
  description = "Deployment environment"
  type        = string
  default     = "dev"
}

variable "session_ttl_seconds" {
  description = "DynamoDB TTL for session expiration (seconds)"
  type        = number
  default     = 1800 # 30 minutes
}

# ── Provider ───────────────────────────────────────────

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

# ── Data sources ───────────────────────────────────────

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}

locals {
  account_id = data.aws_caller_identity.current.account_id
  partition  = data.aws_partition.current.partition
  region     = data.aws_region.current.name
  prefix     = "${var.project_name}-${var.environment}"
}

# ============================================================
# 1. IAM — Service role for KODA application
# ============================================================

resource "aws_iam_user" "koda_app" {
  name = "${local.prefix}-app-user"
}

resource "aws_iam_access_key" "koda_app" {
  user = aws_iam_user.koda_app.name
}

# ── Bedrock inference permissions ──────────────────────

resource "aws_iam_user_policy" "bedrock_invoke" {
  name = "${local.prefix}-bedrock-invoke"
  user = aws_iam_user.koda_app.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "BedrockInvoke"
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
          "bedrock:InvokeModelWithResponseStream",
          "bedrock:Converse",
          "bedrock:ConverseStream",
        ]
        Resource = [
          # Nova 2 Lite (US and Global CRIS)
          "arn:${local.partition}:bedrock:*::foundation-model/amazon.nova-2-lite-v1:0",
          "arn:${local.partition}:bedrock:${local.region}:${local.account_id}:inference-profile/us.amazon.nova-2-lite-v1:0",
          "arn:${local.partition}:bedrock:${local.region}:${local.account_id}:inference-profile/global.amazon.nova-2-lite-v1:0",
          # Nova Multimodal Embeddings
          "arn:${local.partition}:bedrock:*::foundation-model/amazon.nova-2-multimodal-embeddings-v1:0",
        ]
      },
      {
        Sid    = "BedrockInvokeTool"
        Effect = "Allow"
        Action = [
          "bedrock:InvokeTool",
        ]
        Resource = "*"
        Comment  = "Required for Code Interpreter and Web Grounding built-in tools"
      },
      {
        Sid    = "BedrockListModels"
        Effect = "Allow"
        Action = [
          "bedrock:ListFoundationModels",
          "bedrock:GetFoundationModel",
        ]
        Resource = "*"
      },
    ]
  })
}

# ── AWS Marketplace permissions (one-time model enablement) ──

resource "aws_iam_user_policy" "marketplace" {
  name = "${local.prefix}-marketplace"
  user = aws_iam_user.koda_app.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "MarketplaceModelAccess"
        Effect = "Allow"
        Action = [
          "aws-marketplace:ViewSubscriptions",
          "aws-marketplace:Subscribe",
          "aws-marketplace:Unsubscribe",
        ]
        Resource = "*"
      },
    ]
  })
}

# ============================================================
# 2. DynamoDB — Ephemeral session storage (optional)
# ============================================================
# In-memory sessions work for dev/demo. DynamoDB adds:
# - Persistence across restarts
# - Multi-instance support
# - Auto-expiry via TTL (zero-trace privacy)

resource "aws_dynamodb_table" "sessions" {
  name         = "${local.prefix}-sessions"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "session_id"

  attribute {
    name = "session_id"
    type = "S"
  }

  ttl {
    attribute_name = "expires_at"
    enabled        = true
  }

  point_in_time_recovery {
    enabled = false # No recovery needed — ephemeral by design
  }
}

# ============================================================
# 3. S3 — Knowledge base storage (for RAG, if implemented)
# ============================================================

resource "aws_s3_bucket" "knowledge_base" {
  bucket = "${local.prefix}-knowledge-base-${local.account_id}"
}

resource "aws_s3_bucket_versioning" "knowledge_base" {
  bucket = aws_s3_bucket.knowledge_base.id
  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "knowledge_base" {
  bucket = aws_s3_bucket.knowledge_base.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "knowledge_base" {
  bucket                  = aws_s3_bucket.knowledge_base.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ============================================================
# 4. IAM role for Bedrock Knowledge Base (for RAG)
# ============================================================

resource "aws_iam_role" "bedrock_kb" {
  name = "${local.prefix}-bedrock-kb-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "bedrock.amazonaws.com"
        }
        Action = "sts:AssumeRole"
        Condition = {
          StringEquals = {
            "aws:SourceAccount" = local.account_id
          }
        }
      },
    ]
  })
}

resource "aws_iam_role_policy" "bedrock_kb_s3" {
  name = "${local.prefix}-bedrock-kb-s3"
  role = aws_iam_role.bedrock_kb.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:ListBucket",
        ]
        Resource = [
          aws_s3_bucket.knowledge_base.arn,
          "${aws_s3_bucket.knowledge_base.arn}/*",
        ]
      },
    ]
  })
}

resource "aws_iam_role_policy" "bedrock_kb_embeddings" {
  name = "${local.prefix}-bedrock-kb-embeddings"
  role = aws_iam_role.bedrock_kb.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "bedrock:InvokeModel",
        ]
        Resource = [
          "arn:${local.partition}:bedrock:*::foundation-model/amazon.nova-2-multimodal-embeddings-v1:0",
        ]
      },
    ]
  })
}

# ============================================================
# 5. CloudWatch — Logging
# ============================================================

resource "aws_cloudwatch_log_group" "koda" {
  name              = "/koda/${var.environment}"
  retention_in_days = 7 # Minimal retention — privacy by design
}

# ============================================================
# Outputs
# ============================================================

output "aws_access_key_id" {
  description = "Access key for .env file"
  value       = aws_iam_access_key.koda_app.id
  sensitive   = false
}

output "aws_secret_access_key" {
  description = "Secret key for .env file (sensitive)"
  value       = aws_iam_access_key.koda_app.secret
  sensitive   = true
}

output "aws_region" {
  value = var.aws_region
}

output "dynamodb_table_name" {
  value = aws_dynamodb_table.sessions.name
}

output "s3_knowledge_base_bucket" {
  value = aws_s3_bucket.knowledge_base.id
}

output "bedrock_kb_role_arn" {
  value = aws_iam_role.bedrock_kb.arn
}

output "env_file_content" {
  description = "Paste this into your .env file"
  sensitive   = true
  value       = <<-EOT
    AWS_REGION=${var.aws_region}
    AWS_ACCESS_KEY_ID=${aws_iam_access_key.koda_app.id}
    AWS_SECRET_ACCESS_KEY=${aws_iam_access_key.koda_app.secret}
    NOVA_MODEL_ID=us.amazon.nova-2-lite-v1:0
    NOVA_EMBEDDINGS_MODEL_ID=amazon.nova-2-multimodal-embeddings-v1:0
    DYNAMODB_TABLE=${aws_dynamodb_table.sessions.name}
    S3_KNOWLEDGE_BASE=${aws_s3_bucket.knowledge_base.id}
    SESSION_TIMEOUT_MINUTES=30
  EOT
}
