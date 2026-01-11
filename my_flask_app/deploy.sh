#!/bin/bash

# 🚀 WealthCraft Lambda Deployment Script
# This script automates the deployment of your Flask API to AWS Lambda

set -e  # Exit immediately if any command fails

echo "========================================="
echo "🚀 WealthCraft Lambda Deployment"
echo "========================================="
echo ""

# 🎓 STEP 1: Validate AWS credentials
echo "📋 Step 1: Validating AWS credentials..."
if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ ERROR: AWS credentials not configured!"
    echo ""
    echo "Please configure AWS CLI first:"
    echo "  1. Install AWS CLI: https://aws.amazon.com/cli/"
    echo "  2. Run: aws configure"
    echo "  3. Enter your AWS Access Key ID and Secret Access Key"
    echo ""
    exit 1
fi

AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=$(aws configure get region || echo "us-east-1")
echo "✅ Authenticated as AWS Account: $AWS_ACCOUNT"
echo "✅ Deploying to region: $AWS_REGION"
echo ""

# 🎓 STEP 2: Build the SAM application
echo "📦 Step 2: Building SAM application..."
echo "This will:"
echo "  - Install Python dependencies from requirements.txt"
echo "  - Create deployment package in .aws-sam/ directory"
echo "  - Exclude files listed in .samignore"
echo ""

sam build

if [ $? -ne 0 ]; then
    echo "❌ Build failed! Check the error messages above."
    exit 1
fi

echo "✅ Build successful!"
echo ""

# 🎓 STEP 3: Deploy to AWS
echo "☁️  Step 3: Deploying to AWS Lambda..."
echo ""

# Check if this is first deployment (no samconfig.toml exists)
if [ ! -f samconfig.toml ]; then
    echo "🎯 First-time deployment detected!"
    echo "You will be prompted for configuration parameters."
    echo "These will be saved to samconfig.toml for future deployments."
    echo ""
    
    # Guided deployment (interactive)
    sam deploy --guided
else
    echo "🎯 Using existing configuration from samconfig.toml"
    echo "To change parameters, delete samconfig.toml and run again."
    echo ""
    
    # Non-interactive deployment using saved config
    sam deploy
fi

if [ $? -ne 0 ]; then
    echo "❌ Deployment failed! Check the error messages above."
    exit 1
fi

echo ""
echo "========================================="
echo "✅ Deployment Complete!"
echo "========================================="
echo ""
echo "📝 Next Steps:"
echo "  1. Copy the API URL from the outputs above"
echo "  2. Update your mobile app to use the new Lambda URL"
echo "  3. Test your endpoints: curl <API_URL>/health"
echo "  4. Monitor logs: sam logs -n WealthCraftAPI --tail"
echo ""
echo "💰 Cost Monitoring:"
echo "  - Check AWS billing dashboard"
echo "  - Expected: \$0.00 for <1M requests/month"
echo ""
