# ============================================================
# s3.tf — S3 buckets for KODA
# ============================================================

# ============================================================
# Knowledge Base Bucket (for RAG)
# ============================================================

resource "aws_s3_bucket" "knowledge_base" {
  bucket = "${local.prefix}-knowledge-base-${local.account_id}"
  tags   = local.common_tags
}

# ── Versioning ────────────────────────────────────────

resource "aws_s3_bucket_versioning" "knowledge_base" {
  bucket = aws_s3_bucket.knowledge_base.id

  versioning_configuration {
    status = "Enabled"
  }
}

# ── Encryption ────────────────────────────────────────

resource "aws_s3_bucket_server_side_encryption_configuration" "knowledge_base" {
  bucket = aws_s3_bucket.knowledge_base.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ── Block Public Access ────────────────────────────────

resource "aws_s3_bucket_public_access_block" "knowledge_base" {
  bucket = aws_s3_bucket.knowledge_base.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# ── Lifecycle Policy ───────────────────────────────────

resource "aws_s3_bucket_lifecycle_configuration" "knowledge_base" {
  bucket = aws_s3_bucket.knowledge_base.id

  rule {
    id     = "delete-old-versions"
    status = "Enabled"

    noncurrent_version_expiration {
      noncurrent_days = 30
    }
  }
}
