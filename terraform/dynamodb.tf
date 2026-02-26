# ============================================================
# dynamodb.tf — DynamoDB tables for KODA
# ============================================================

# ============================================================
# Sessions Table — Ephemeral session storage
# ============================================================
# In-memory sessions work for dev/demo. DynamoDB adds:
# - Persistence across restarts
# - Multi-instance support
# - Auto-expiry via TTL (zero-trace privacy)

resource "aws_dynamodb_table" "sessions" {
  name             = "${local.prefix}-sessions"
  billing_mode     = "PAY_PER_REQUEST"
  hash_key         = "session_id"
  stream_enabled   = true
  stream_view_type = "NEW_AND_OLD_IMAGES"
  tags             = local.common_tags

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

  lifecycle {
    prevent_destroy = false # Safe to destroy in dev
  }
}
