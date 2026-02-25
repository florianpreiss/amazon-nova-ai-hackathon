#!/bin/bash
# Authenticate via SAML and export credentials for KODA
set -euo pipefail

PROFILE="${AWS_PROFILE:-koda}"

echo "🔐 Authenticating with saml2aws (profile: $PROFILE)..."
saml2aws login --profile "$PROFILE" --skip-prompt

echo ""
echo "🔍 Verifying credentials..."
IDENTITY=$(aws sts get-caller-identity --profile "$PROFILE" --output text)
echo "   $IDENTITY"

echo ""
echo "✅ Credentials valid. Usage:"
echo "   export AWS_PROFILE=$PROFILE"
echo "   python scripts/verify_setup.py"
echo "   streamlit run frontend/app.py"
