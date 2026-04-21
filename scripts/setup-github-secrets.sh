#!/bin/bash

# Setup GitHub Secrets for Google Cloud Deployment
# This script helps you add all required secrets to your GitHub repository

set -e

echo "=========================================="
echo "GitHub Secrets Setup for GCP Deployment"
echo "=========================================="
echo ""

# Check if GitHub CLI is installed
if ! command -v gh &> /dev/null; then
    echo "❌ GitHub CLI is not installed. Please install it first:"
    echo "   brew install gh  (on macOS)"
    echo "   https://cli.github.com/ (for other systems)"
    exit 1
fi

# Get repository info
REPO=$(gh repo view --json nameWithOwner --jq '.nameWithOwner')
echo "📍 Repository: $REPO"
echo ""

# Function to read input and set secret
set_secret() {
    local secret_name=$1
    local prompt=$2
    local is_file=$3
    
    echo -n "$prompt: "
    
    if [ "$is_file" = "true" ]; then
        echo -n "(path to file) "
    fi
    
    read -r value
    
    if [ "$is_file" = "true" ]; then
        if [ ! -f "$value" ]; then
            echo "❌ File not found: $value"
            return 1
        fi
        value=$(cat "$value")
    fi
    
    # Set the secret
    echo "$value" | gh secret set "$secret_name" --repo "$REPO"
    echo "✅ Secret '$secret_name' set successfully"
}

echo "Please provide the following information:"
echo ""

set_secret "GCP_PROJECT_ID" "GCP Project ID" false
echo ""

set_secret "GCP_WORKLOAD_IDENTITY_PROVIDER" "Workload Identity Provider resource (projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/POOL/providers/PROVIDER)" false
echo ""

set_secret "GCP_SERVICE_ACCOUNT_EMAIL" "Deployment service account email (github-deployer@PROJECT_ID.iam.gserviceaccount.com)" false
echo ""

set_secret "MONGODB_URI" "MongoDB Atlas connection URI (mongodb+srv://...)" false
echo ""

set_secret "MONGODB_DB_NAME" "MongoDB database name (default: FSDMiniProject)" false
echo ""

echo -n "Generate random SECRET_KEY? (y/n): "
read -r generate_secret
if [ "$generate_secret" = "y" ]; then
    secret_key=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo "$secret_key" | gh secret set "SECRET_KEY" --repo "$REPO"
    echo "✅ Secret 'SECRET_KEY' generated and set"
else
    set_secret "SECRET_KEY" "SECRET_KEY (generate with: python3 -c \"import secrets; print(secrets.token_hex(32))\")" false
fi
echo ""

echo -n "Generate random JWT_SECRET_KEY? (y/n): "
read -r generate_jwt
if [ "$generate_jwt" = "y" ]; then
    jwt_key=$(python3 -c "import secrets; print(secrets.token_hex(32))")
    echo "$jwt_key" | gh secret set "JWT_SECRET_KEY" --repo "$REPO"
    echo "✅ Secret 'JWT_SECRET_KEY' generated and set"
else
    set_secret "JWT_SECRET_KEY" "JWT_SECRET_KEY (generate with: python3 -c \"import secrets; print(secrets.token_hex(32))\")" false
fi
echo ""

set_secret "CORS_ORIGINS" "CORS_ORIGINS (e.g., https://your-domain.com,https://api.your-domain.com)" false
echo ""

set_secret "VITE_API_URL" "Frontend API URL (e.g., https://api.your-domain.com/api)" false
echo ""

echo ""
echo "=========================================="
echo "✅ All secrets have been set successfully!"
echo "=========================================="
echo ""
echo "You can now:"
echo "1. Push your code to GitHub main branch"
echo "2. The workflow will automatically deploy to Google Cloud"
echo "3. Monitor progress in GitHub Actions tab"
echo ""
echo "To verify secrets were set:"
echo "   gh secret list --repo $REPO"
