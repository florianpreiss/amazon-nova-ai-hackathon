#!/bin/bash
# ============================================================
# KODA — One-time deployment setup
# Run this ONCE to create all AWS infrastructure and configure
# GitHub Actions for automated deployments.
#
# After this, every push to main auto-deploys to ECS.
# ============================================================

set -euo pipefail

echo "=============================================="
echo "KODA — Deployment Setup"
echo "=============================================="

# ── Step 1: Check prerequisites ────────────────────

echo ""
echo "Step 1: Checking prerequisites..."

command -v terraform >/dev/null 2>&1 || { echo "❌ Terraform not found. Install: brew install terraform"; exit 1; }
command -v aws >/dev/null 2>&1 || { echo "❌ AWS CLI not found. Install: brew install awscli"; exit 1; }
command -v gh >/dev/null 2>&1 || { echo "⚠️  GitHub CLI not found (optional). Install: brew install gh"; }

echo "✅ Prerequisites OK"

# ── Step 2: Verify AWS credentials ─────────────────

echo ""
echo "Step 2: Verifying AWS credentials..."

# Use the koda profile (set by aws_login.sh / saml2aws)
export AWS_PROFILE="${AWS_PROFILE:-koda}"
echo "  Using AWS profile: $AWS_PROFILE"

if ! ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text 2>&1); then
  echo "❌ AWS credentials not found for profile '$AWS_PROFILE'."
  echo "   Run first: ./scripts/aws_login.sh"
  exit 1
fi
echo "✅ AWS Account: $ACCOUNT_ID"

# ── Step 3: Apply Terraform ────────────────────────

echo ""
echo "Step 3: Creating AWS infrastructure..."
echo "(This creates VPC, ECS, ALB, CloudFront, ECR, WAF, OIDC...)"
echo ""

cd terraform
terraform init
terraform apply -auto-approve

# ── Step 4: Get outputs ────────────────────────────

echo ""
echo "Step 4: Collecting deployment info..."

ROLE_ARN=$(terraform output -raw github_actions_role_arn)
ECR_URL=$(terraform output -raw ecr_repository_url)
CLOUDFRONT_URL=$(terraform output -raw cloudfront_url)

echo "  GitHub Actions Role: $ROLE_ARN"
echo "  ECR Repository:     $ECR_URL"
echo "  CloudFront URL:     $CLOUDFRONT_URL"

cd ..

# ── Step 5: Configure GitHub repository variable ───

echo ""
echo "Step 5: Configuring GitHub Actions..."
echo ""
echo "You need to add this as a GitHub Actions variable:"
echo ""
echo "  Variable name:  AWS_ROLE_TO_ASSUME"
echo "  Variable value: $ROLE_ARN"
echo ""
echo "Go to: https://github.com/florianpreiss/amazon-nova-ai-hackathon/settings/variables/actions"
echo "Click 'New repository variable' and paste the values above."
echo ""

# Try to set it automatically via GitHub CLI
if command -v gh >/dev/null 2>&1; then
  read -p "Set this automatically with GitHub CLI? (y/n) " -n 1 -r
  echo
  if [[ $REPLY =~ ^[Yy]$ ]]; then
    gh variable set AWS_ROLE_TO_ASSUME --body "$ROLE_ARN"
    echo "✅ GitHub variable set automatically"
  fi
fi

# ── Step 6: Summary ────────────────────────────────

echo ""
echo "=============================================="
echo "✅ Setup complete!"
echo "=============================================="
echo ""
echo "What happens now:"
echo "  1. Push any change to main"
echo "  2. GitHub Actions builds the Docker image"
echo "  3. Pushes it to ECR: $ECR_URL"
echo "  4. Deploys to ECS Fargate"
echo "  5. Available at: $CLOUDFRONT_URL"
echo ""
echo "To trigger a deploy right now:"
echo "  git commit --allow-empty -m 'chore: trigger deploy'"
echo "  git push origin main"
echo ""
echo "Or manually in GitHub → Actions → Deploy → Run workflow"
echo "=============================================="
