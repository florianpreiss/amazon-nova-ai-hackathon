# ============================================================
# locals.tf — Data sources and local values
# ============================================================

# ── AWS account and partition info ─────────────────────

data "aws_caller_identity" "current" {}
data "aws_partition" "current" {}
data "aws_region" "current" {}

# ── Computed local values ──────────────────────────────

locals {
  account_id = data.aws_caller_identity.current.account_id
  partition  = data.aws_partition.current.partition
  region     = var.aws_region
  prefix     = "${var.project_name}-${var.environment}"

  # Common tags applied to all resources
  common_tags = merge(
    var.tags,
    {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  )
}
