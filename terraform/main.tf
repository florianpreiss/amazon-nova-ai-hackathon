# ============================================================
# main.tf — Root module (minimal - resources in separate files)
# ============================================================
# This file is kept mostly minimal for Terraform module structure.
# All resources are organized into purpose-specific files:
#
# - terraform.tf       : Provider and version requirements
# - variables.tf       : Input variables
# - locals.tf          : Data sources and local values
# - iam.tf             : IAM roles, policies, users
# - dynamodb.tf        : DynamoDB tables
# - s3.tf              : S3 buckets
# - cloudwatch.tf      : CloudWatch logs
# - outputs.tf         : Outputs
#
# See terraform.tf for provider configuration
# See locals.tf for data sources and locals
# See variables.tf for input variables
