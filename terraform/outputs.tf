# ============================================================
# Outputs — Core infrastructure, IAM, and deployment info
# ============================================================

# ── IAM Outputs ────────────────────────────────────────

output "aws_access_key_id" {
  description = "IAM access key for KODA app user"
  value       = aws_iam_access_key.koda_app.id
  sensitive   = false
}

output "aws_secret_access_key" {
  description = "IAM secret key for KODA app user"
  value       = aws_iam_access_key.koda_app.secret
  sensitive   = true
}

output "aws_region" {
  description = "AWS region for deployment"
  value       = var.aws_region
}

# ── Database & Storage Outputs ────────────────────────

output "dynamodb_table_name" {
  description = "DynamoDB session table name"
  value       = aws_dynamodb_table.sessions.name
}

output "s3_knowledge_base_bucket" {
  description = "S3 bucket for knowledge base and RAG"
  value       = aws_s3_bucket.knowledge_base.id
}

output "bedrock_kb_role_arn" {
  description = "IAM role ARN for Bedrock Knowledge Base"
  value       = aws_iam_role.bedrock_kb.arn
}

# ── Environment Configuration ──────────────────────────

output "env_file_content" {
  description = "Paste this into your .env file for local development"
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

# ── Application Access ─────────────────────────────────

output "alb_url" {
  description = "ALB DNS name (internal, for CloudFront origin)"
  value       = aws_lb.koda.dns_name
}

output "cloudfront_url" {
  description = "CloudFront distribution domain name (public access point)"
  value       = aws_cloudfront_distribution.koda.domain_name
}
