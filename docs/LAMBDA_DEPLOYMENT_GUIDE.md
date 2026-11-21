# AWS Lambda Deployment Guide

## 🎯 Overview

This guide walks you through deploying your WealthCraft Flask backend to AWS Lambda for **$0 hosting costs** (up to 1 million requests/month).

---

## 📋 Prerequisites

### 1. AWS Account Setup
- [ ] Create AWS account at https://aws.amazon.com
- [ ] Note your AWS Access Key ID and Secret Access Key
  - Go to IAM → Users → Your User → Security Credentials → Create Access Key

### 2. Install AWS CLI

#### Windows (PowerShell or Command Prompt)
```powershell
# Download and run the MSI installer
# Visit: https://awscli.amazonaws.com/AWSCLIV2.msi
# Or download directly:
curl https://awscli.amazonaws.com/AWSCLIV2.msi -o AWSCLIV2.msi
msiexec.exe /i AWSCLIV2.msi

# Verify installation (restart terminal after install)
aws --version
```

#### macOS
```bash
brew install awscli
```

#### Linux
```bash
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install
```

### 3. Configure AWS Credentials
```bash
aws configure
```

You'll be prompted for:
- **AWS Access Key ID**: Your access key from IAM
- **AWS Secret Access Key**: Your secret key from IAM
- **Default region**: `us-east-1` (or your preferred region)
- **Default output format**: `json`

### 4. Install AWS SAM CLI

#### Windows (PowerShell or Command Prompt)
```powershell
# Download and run the MSI installer
# Visit: https://github.com/aws/aws-sam-cli/releases/latest/download/AWS_SAM_CLI_64_PY3.msi
# Or download directly:
curl -L https://github.com/aws/aws-sam-cli/releases/latest/download/AWS_SAM_CLI_64_PY3.msi -o AWS_SAM_CLI.msi
msiexec.exe /i AWS_SAM_CLI.msi

# Verify installation (restart terminal after install)
sam --version
```

#### macOS
```bash
brew install aws-sam-cli
```

#### Linux
```bash
pip install aws-sam-cli
```

Verify installation:
```bash
sam --version
# Should output: SAM CLI, version 1.x.x
```

---

## 🧪 Local Testing (Before Deploying)

### Step 1: Install Dependencies
```bash
cd my_flask_app
pip install -r requirements.txt
```

### Step 2: Test Lambda Function Locally
```bash
# Start local API Gateway emulator
sam local start-api

# In another terminal, test endpoints
curl http://localhost:3000/health
curl http://localhost:3000/api/profile/me -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

**🎓 What's happening?**
- SAM creates a local Docker container running your Lambda function
- Simulates API Gateway routing
- Uses your `.env` file for environment variables

### Step 3: Invoke Lambda Function Directly
```bash
# Test the Lambda handler with a sample event
sam local invoke WealthCraftAPI --event test-event.json
```

Create `test-event.json`:
```json
{
  "httpMethod": "GET",
  "path": "/health",
  "headers": {},
  "body": null
}
```

---

## 🚀 Deployment to AWS

### First-Time Deployment

#### Windows (Git Bash or WSL)
```bash
# Option 1: Use Git Bash (comes with Git for Windows)
./deploy.sh

# Option 2: Use WSL (Windows Subsystem for Linux)
./deploy.sh

# Option 3: Run SAM commands directly in PowerShell
sam build
sam deploy --guided
```

**Note for Windows users**: The `deploy.sh` script is a bash script. If you don't have Git Bash or WSL, you can run the SAM commands directly (Option 3 above).

#### macOS / Linux
```bash
./deploy.sh
```

You'll be prompted for:

1. **Stack Name**: `wealthcraft-api` (or your choice)
2. **AWS Region**: `us-east-1` (or your choice)
3. **Parameter DatabaseURL**: Your Supabase connection string
   ```
   postgresql://postgres.xxxxx:password@aws-0-us-east-1.pooler.supabase.com:6543/postgres
   ```
4. **Parameter SupabaseJWTSecret**: From Supabase → Settings → API → JWT Secret
5. **Parameter SecretKey**: Generate with `python -c "import secrets; print(secrets.token_hex(32))"`
6. **Parameter CorsOrigins**: `*` (for development) or your mobile app domain
7. **Confirm changes before deploy**: `Y`
8. **Allow SAM CLI IAM role creation**: `Y`
9. **Save arguments to samconfig.toml**: `Y`

**⏱️ Deployment time**: 2-5 minutes

### Subsequent Deployments

After first deployment, simply run:
```bash
./deploy.sh
```

SAM will use saved parameters from `samconfig.toml`.

---

## ✅ Verification

### 1. Get Your API URL
After deployment, look for:
```
Outputs
--------
Key: ApiURL
Value: https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/Prod/
```

### 2. Test Health Endpoint
```bash
curl https://YOUR_API_URL/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "WealthCraft API is running"
}
```

### 3. Test Authenticated Endpoint
```bash
# Get a JWT token from your mobile app or Supabase
curl https://YOUR_API_URL/api/profile/me \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 4. Monitor Logs
```bash
# Tail live logs
sam logs -n WealthCraftAPI --tail

# View recent logs
sam logs -n WealthCraftAPI --start-time '10min ago'
```

---

## 🔄 Updating Your Mobile App

Update your mobile app's API base URL:

```typescript
// Before (App Runner)
const API_BASE_URL = 'https://your-app-runner-url.us-east-1.awsapprunner.com';

// After (Lambda)
const API_BASE_URL = 'https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/Prod';
```

---

## 📊 Monitoring & Debugging

### CloudWatch Logs
```bash
# View logs in AWS Console
# CloudWatch → Log groups → /aws/lambda/wealthcraft-api-WealthCraftAPI-xxxxx
```

### Lambda Metrics
```bash
# View in AWS Console
# Lambda → Functions → wealthcraft-api-WealthCraftAPI-xxxxx → Monitoring
```

Key metrics to watch:
- **Invocations**: Total requests
- **Duration**: Average response time
- **Errors**: Failed requests
- **Throttles**: Rate-limited requests

### Cold Start Monitoring
```bash
# Check cold start times in CloudWatch Logs
# Look for "INIT_START" and "INIT_DURATION" entries
```

**🎓 Typical cold start**: 1-3 seconds for first request after idle

---

## 💰 Cost Monitoring

### Free Tier Limits (Forever)
- ✅ **1,000,000 requests/month**
- ✅ **400,000 GB-seconds compute/month**

### Calculate Your Usage
```
Requests/month: 50,000 users × 10 requests/day × 30 days = 15M requests
```

**⚠️ This exceeds free tier!** But at $0.20 per 1M requests:
```
Cost = (15M - 1M) × $0.20 / 1M = $2.80/month
```

Still cheaper than App Runner ($5-10/month minimum).

### View Costs
```bash
# AWS Console → Billing Dashboard → Cost Explorer
# Filter by service: Lambda
```

---

## 🐛 Troubleshooting

### Issue: "Unable to import module 'lambda_handler'"
**Cause**: Missing dependencies in deployment package

**Fix**:
```bash
# Ensure requirements.txt includes all dependencies
pip freeze > requirements.txt
sam build --use-container  # Build in Docker (matches Lambda environment)
sam deploy
```

### Issue: Database connection timeout
**Cause**: Lambda can't reach Supabase (security group/VPC issue)

**Fix**:
- Ensure Supabase allows connections from `0.0.0.0/0` (or AWS IP ranges)
- Check `DATABASE_URL` uses pooler (port 6543), not direct connection (port 5432)

### Issue: Cold starts too slow (>5 seconds)
**Cause**: Large deployment package or many dependencies

**Fix**:
```bash
# 1. Reduce package size
# Add unnecessary files to .samignore

# 2. Increase memory (more CPU allocated)
# In template.yaml, change MemorySize: 512 → 1024

# 3. Keep Lambda warm (optional, costs ~$0.50/month)
# Add CloudWatch Events rule to ping /health every 5 minutes
```

### Issue: "Rate exceeded" errors
**Cause**: Hitting Lambda concurrency limits (1000 concurrent executions)

**Fix**:
```bash
# Request limit increase via AWS Support
# Or optimize cold start times to reduce concurrent executions
```

---

## 🔐 Security Best Practices

### 1. Never Commit Secrets
```bash
# Ensure .env is in .gitignore
echo ".env" >> .gitignore
```

### 2. Use Parameter Store (Optional)
For extra security, store secrets in AWS Systems Manager Parameter Store:
```bash
aws ssm put-parameter \
  --name /wealthcraft/database-url \
  --value "postgresql://..." \
  --type SecureString
```

Update `template.yaml`:
```yaml
Environment:
  Variables:
    DATABASE_URL: '{{resolve:ssm:/wealthcraft/database-url}}'
```

### 3. Restrict CORS Origins
In production, replace `*` with your actual domains:
```yaml
Parameters:
  CorsOrigins:
    Default: "https://app.wealthcraft.com,https://mobile.wealthcraft.com"
```

---

## 🎓 Understanding the Architecture

```
Mobile App
    ↓ HTTPS Request
API Gateway (https://xxx.execute-api.us-east-1.amazonaws.com/Prod/)
    ↓ Lambda Event
Lambda Function (WealthCraftAPI)
    ↓ apig-wsgi translates to WSGI
Flask App (app/__init__.py)
    ↓ SQLAlchemy
Supabase PostgreSQL Database
```

**Key Differences from App Runner:**
- **App Runner**: Always-on server (like Gunicorn)
- **Lambda**: Event-driven, scales to zero when idle

---

## 📚 Next Steps

- [ ] Deploy to AWS Lambda
- [ ] Update mobile app with new API URL
- [ ] Test all endpoints
- [ ] Set up CloudWatch alarms for errors
- [ ] (Optional) Set up CI/CD with GitHub Actions
- [ ] (Optional) Add custom domain with Route 53

---

## 🆘 Need Help?

- **AWS SAM Docs**: https://docs.aws.amazon.com/serverless-application-model/
- **Lambda Pricing**: https://aws.amazon.com/lambda/pricing/
- **Supabase Connection Pooling**: https://supabase.com/docs/guides/database/connecting-to-postgres#connection-pool
