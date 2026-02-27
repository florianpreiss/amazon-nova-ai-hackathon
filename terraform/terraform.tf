# ============================================================
# terraform.tf — Provider and version requirements
# ============================================================

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.40.0"
    }
  }

  # Uncomment for remote state (e.g., S3 + DynamoDB)
  # backend "s3" {
  #   bucket         = "koda-terraform-state"
  #   key            = "prod/terraform.tfstate"
  #   region         = "us-east-1"
  #   encrypt        = true
  #   dynamodb_table = "terraform-locks"
  # }
}

provider "aws" {
  region = var.aws_region

  # Ignore all tags injected by account-level tag policies.
  # The account policy injects Project, Environment, ManagedBy, CreatedAt, CreatedBy
  # at resource creation time. If we also set these in default_tags Terraform sees
  # them as "new elements" during apply and fails with "inconsistent final plan".
  # Solution: do not use default_tags; rely on the account tag policy instead.
  ignore_tags {
    key_prefixes = ["aws:"]
    keys         = ["CreatedAt", "CreatedBy", "Project", "Environment", "ManagedBy"]
  }
}
