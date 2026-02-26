# ============================================================
# IAM Roles for ECS
# Execution role: ECR pull, CloudWatch logs, Secrets Manager read
# Task role: Bedrock invoke (least privilege)
# ============================================================

# ── ECS Execution Role ─────────────────────────────
# Used by ECS agent to pull images, write logs, read secrets

resource "aws_iam_role" "ecs_execution" {
  name = "${local.prefix}-ecs-execution"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution_base" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

resource "aws_iam_role_policy" "ecs_execution_secrets" {
  name = "${local.prefix}-ecs-exec-secrets"
  role = aws_iam_role.ecs_execution.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Action = [
        "secretsmanager:GetSecretValue",
      ]
      Resource = [aws_secretsmanager_secret.bedrock_credentials.arn]
    }]
  })
}

# ── ECS Task Role ──────────────────────────────────
# Used by the running container — Bedrock access only

resource "aws_iam_role" "ecs_task" {
  name = "${local.prefix}-ecs-task"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect    = "Allow"
      Principal = { Service = "ecs-tasks.amazonaws.com" }
      Action    = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy" "ecs_task_bedrock" {
  name = "${local.prefix}-ecs-task-bedrock"
  role = aws_iam_role.ecs_task.name

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
          "bedrock:InvokeTool",
        ]
        Resource = [
          "arn:${local.partition}:bedrock:*::foundation-model/amazon.nova-2-lite-v1:0",
          "arn:${local.partition}:bedrock:${local.region}:${local.account_id}:inference-profile/us.amazon.nova-2-lite-v1:0",
          "arn:${local.partition}:bedrock:${local.region}:${local.account_id}:inference-profile/global.amazon.nova-2-lite-v1:0",
          "arn:${local.partition}:bedrock:*::foundation-model/amazon.nova-2-multimodal-embeddings-v1:0",
        ]
      },
      {
        Sid      = "BedrockInvokeToolWildcard"
        Effect   = "Allow"
        Action   = ["bedrock:InvokeTool"]
        Resource = "*"
      },
    ]
  })
}
