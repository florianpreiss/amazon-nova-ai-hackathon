# ============================================================
# ECR — Container image repository
# ============================================================

resource "aws_ecr_repository" "koda" {
  name                 = "${local.prefix}-app"
  image_tag_mutability = "IMMUTABLE"
  force_delete         = true # Allow cleanup during hackathon

  image_scanning_configuration {
    scan_on_push = true
  }

  encryption_configuration {
    encryption_type = "AES256"
  }

  tags = { Name = "${local.prefix}-ecr" }
}

# Lifecycle policy: keep only last 10 images
resource "aws_ecr_lifecycle_policy" "koda" {
  repository = aws_ecr_repository.koda.name

  policy = jsonencode({
    rules = [{
      rulePriority = 1
      description  = "Keep last 10 images"
      selection = {
        tagStatus   = "any"
        countType   = "imageCountMoreThan"
        countNumber = 10
      }
      action = { type = "expire" }
    }]
  })
}
