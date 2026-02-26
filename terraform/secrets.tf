# ============================================================
# Secrets Manager — Bedrock credentials for ECS tasks
# No credentials in environment variables or container images
# ============================================================

resource "aws_secretsmanager_secret" "bedrock_credentials" {
  name                    = "${local.prefix}-bedrock-credentials"
  description             = "AWS credentials for KODA ECS tasks to access Bedrock"
  recovery_window_in_days = 0 # Immediate delete during hackathon

  tags = { Name = "${local.prefix}-bedrock-credentials" }
}

resource "aws_secretsmanager_secret_version" "bedrock_credentials" {
  secret_id = aws_secretsmanager_secret.bedrock_credentials.id
  secret_string = jsonencode({
    access_key = aws_iam_access_key.koda_app.id
    secret_key = aws_iam_access_key.koda_app.secret
  })
}
