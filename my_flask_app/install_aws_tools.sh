#!/bin/bash

# 🚀 AWS Tools Installation Script for WSL/Linux
# This script installs AWS CLI and AWS SAM CLI on your WSL environment

set -e  # Exit on error

echo "========================================="
echo "🔧 Installing AWS Tools for Lambda"
echo "========================================="
echo ""

# 🎓 STEP 1: Install AWS CLI
echo "📦 Step 1: Installing AWS CLI..."
echo ""

if command -v aws &> /dev/null; then
    echo "✅ AWS CLI already installed: $(aws --version)"
else
    echo "Installing AWS CLI v2..."
    cd /tmp
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip -q awscliv2.zip
    sudo ./aws/install
    rm -rf aws awscliv2.zip
    echo "✅ AWS CLI installed successfully!"
fi

echo ""

# 🎓 STEP 2: Install AWS SAM CLI
echo "📦 Step 2: Installing AWS SAM CLI..."
echo ""

if command -v sam &> /dev/null; then
    echo "✅ SAM CLI already installed: $(sam --version)"
else
    echo "Installing SAM CLI via pip..."
    
    # Check if pip is installed
    if ! command -v pip3 &> /dev/null; then
        echo "Installing pip3..."
        sudo apt-get update
        sudo apt-get install -y python3-pip
    fi
    
    # Install SAM CLI
    pip3 install --user aws-sam-cli
    
    # Add to PATH if not already there
    if ! grep -q '.local/bin' ~/.bashrc; then
        echo 'export PATH=$HOME/.local/bin:$PATH' >> ~/.bashrc
        export PATH=$HOME/.local/bin:$PATH
    fi
    
    echo "✅ SAM CLI installed successfully!"
    echo "⚠️  Please run: source ~/.bashrc (or restart your terminal)"
fi

echo ""
echo "========================================="
echo "✅ Installation Complete!"
echo "========================================="
echo ""
echo "📋 Verify installations:"
echo "  aws --version"
echo "  sam --version"
echo ""
echo "📝 Next Steps:"
echo "  1. Configure AWS credentials: aws configure"
echo "  2. Deploy your Lambda function: ./deploy.sh"
echo ""
