# ============================================================
# GitHub Actions OIDC — Keyless authentication with AWS
#
# GitHub Actions assumes an IAM role via OIDC instead of
# storing long-lived AWS credentials as GitHub Secrets.
# This is the AWS-recommended security best practice.
#
# Reference: https://docs.github.com/en/actions/security-for-github-actions/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services
# ============================================================

variable "github_org" {
  description = "GitHub organization or username"
  type        = string
  default     = "florianpreiss"
}

variable "github_repo" {
  description = "GitHub repository name"
  type        = string
  default     = "amazon-nova-ai-hackathon"
}

# ── OIDC Identity Provider ─────────────────────────

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = ["ffffffffffffffffffffffffffffffffffffffff"] # AWS manages GitHub's thumbprint

  tags = { Name = "${local.prefix}-github-oidc" }
}

# ── IAM Role for GitHub Actions ────────────────────
# Can ONLY be assumed by GitHub Actions from YOUR repo

resource "aws_iam_role" "github_actions" {
  name = "${local.prefix}-github-actions"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Federated = aws_iam_openid_connect_provider.github.arn
      }
      Action = "sts:AssumeRoleWithWebIdentity"
      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }
        StringLike = {
          # Allow from main branch and any PR
          "token.actions.githubusercontent.com:sub" = "repo:${var.github_org}/${var.github_repo}:*"
        }
      }
    }]
  })

  max_session_duration = 3600 # 1 hour max

  tags = { Name = "${local.prefix}-github-actions-role" }
}

# ── ECR permissions (push/pull images) ─────────────

resource "aws_iam_role_policy" "github_ecr" {
  name = "${local.prefix}-github-ecr"
  role = aws_iam_role.github_actions.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid      = "ECRAuth"
        Effect   = "Allow"
        Action   = ["ecr:GetAuthorizationToken"]
        Resource = "*"
      },
      {
        Sid    = "ECRPush"
        Effect = "Allow"
        Action = [
          "ecr:BatchCheckLayerAvailability",
          "ecr:GetDownloadUrlForLayer",
          "ecr:BatchGetImage",
          "ecr:PutImage",
          "ecr:InitiateLayerUpload",
          "ecr:UploadLayerPart",
          "ecr:CompleteLayerUpload",
        ]
        Resource = [aws_ecr_repository.koda.arn]
      },
    ]
  })
}

# ── ECS permissions (deploy new task) ──────────────

resource "aws_iam_role_policy" "github_ecs" {
  name = "${local.prefix}-github-ecs"
  role = aws_iam_role.github_actions.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ECSUpdate"
        Effect = "Allow"
        Action = [
          "ecs:UpdateService",
          "ecs:DescribeServices",
          "ecs:DescribeTaskDefinition",
          "ecs:RegisterTaskDefinition",
          "ecs:ListTasks",
          "ecs:DescribeTasks",
        ]
        Resource = "*"
        Condition = {
          ArnEquals = {
            "ecs:cluster" = aws_ecs_cluster.koda.arn
          }
        }
      },
      {
        Sid      = "ECSRegisterTask"
        Effect   = "Allow"
        Action   = ["ecs:RegisterTaskDefinition", "ecs:DescribeTaskDefinition"]
        Resource = "*"
      },
      {
        Sid    = "PassRole"
        Effect = "Allow"
        Action = ["iam:PassRole"]
        Resource = [
          aws_iam_role.ecs_execution.arn,
          aws_iam_role.ecs_task.arn,
        ]
      },
    ]
  })
}

# ── Output the role ARN (needed in GitHub Actions) ─

output "github_actions_role_arn" {
  description = "Add this as a GitHub Actions variable: AWS_ROLE_TO_ASSUME"
  value       = aws_iam_role.github_actions.arn
}
