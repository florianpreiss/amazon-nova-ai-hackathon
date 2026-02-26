# ============================================================
# cloudwatch.tf — CloudWatch logging for KODA
# ============================================================

resource "aws_cloudwatch_log_group" "koda" {
  name              = "/aws/koda/${var.environment}"
  retention_in_days = var.log_retention_days
  tags              = local.common_tags

  lifecycle {
    prevent_destroy = false
  }
}
