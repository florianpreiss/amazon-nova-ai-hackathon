# ============================================================
# iam.tf — IAM roles, policies, and users for KODA
# ============================================================

# ============================================================
# KODA Application User
# ============================================================

resource "aws_iam_user" "koda_app" {
  name = "${local.prefix}-app-user"
  tags = local.common_tags
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
          "arn:${local.partition}:bedrock:*::foundation-model/amazon.nova-2-lite-v1:0",
          "arn:${local.partition}:bedrock:${local.region}:${local.account_id}:inference-profile/us.amazon.nova-2-lite-v1:0",
          "arn:${local.partition}:bedrock:${local.region}:${local.account_id}:inference-profile/global.amazon.nova-2-lite-v1:0",
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

# ── AWS Marketplace permissions ────────────────────────

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
# Bedrock Knowledge Base Role (for RAG)
# ============================================================

resource "aws_iam_role" "bedrock_kb" {
  name = "${local.prefix}-bedrock-kb-role"
  tags = local.common_tags

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

# ── S3 access for Knowledge Base ───────────────────────

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

# ── Bedrock embeddings access ──────────────────────────

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
