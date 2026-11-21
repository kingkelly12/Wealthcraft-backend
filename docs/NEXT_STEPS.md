# ✅ AWS Tools Setup Complete!

## Installation Status

✅ **AWS CLI**: v2.32.31 (installed via snap)  
✅ **SAM CLI**: v1.132.0  
✅ **PATH**: Fixed - `/snap/bin` added to PATH

---

## 🎯 Next Steps to Deploy

### Step 1: Configure AWS Credentials

You need to set up your AWS credentials before deploying. Run:

```bash
aws configure
```

You'll be prompted for:
1. **AWS Access Key ID**: Get this from AWS Console → IAM → Users → Your User → Security Credentials → Create Access Key
2. **AWS Secret Access Key**: Shown when you create the access key (save it!)
3. **Default region**: `us-east-1` (recommended) or your preferred region
4. **Default output format**: `json`

**🎓 How to get AWS credentials:**
1. Go to https://console.aws.amazon.com/iam/
2. Click "Users" in the left sidebar
3. Click your username (or create a new user)
4. Go to "Security credentials" tab
5. Click "Create access key"
6. Choose "Command Line Interface (CLI)"
7. Copy the Access Key ID and Secret Access Key

---

### Step 2: Prepare Environment Variables

You'll need these values during deployment. Gather them now:

#### From Supabase:
```bash
# 1. DATABASE_URL (from Supabase → Settings → Database → Connection String → URI)
# Use the POOLER connection (port 6543), not direct connection
# Example: postgresql://postgres.xxxxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres

# 2. SUPABASE_JWT_SECRET (from Supabase → Settings → API → JWT Settings → JWT Secret)
```

#### Generate Flask Secret Key:
```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

#### CORS Origins:
```bash
# For development: *
# For production: https://yourdomain.com,https://app.yourdomain.com
```

---

### Step 3: Deploy to Lambda

Once you have AWS credentials configured, run:

```bash
cd ~/Devops/wealthcraft-legacy-sim/my_flask_app
./deploy.sh
```

**During deployment, you'll be prompted for:**
1. Stack name: `wealthcraft-api` (or your choice)
2. AWS Region: `us-east-1` (or match your Supabase region)
3. Parameter DatabaseURL: [paste your Supabase connection string]
4. Parameter SupabaseJWTSecret: [paste from Supabase]
5. Parameter SecretKey: [paste generated secret]
6. Parameter CorsOrigins: `*` (for now)
7. Confirm changes: `Y`
8. Allow IAM role creation: `Y`
9. Save to samconfig.toml: `Y`

**⏱️ Deployment takes 2-5 minutes**

---

### Step 4: Get Your API URL

After deployment completes, look for:
```
Outputs
--------
Key: ApiURL
Value: https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/Prod/
```

**Copy this URL** - you'll need it for your mobile app!

---

### Step 5: Test Your Deployment

```bash
# Test health endpoint
curl https://YOUR_API_URL/health

# Expected response:
# {"status":"healthy","message":"WealthCraft API is running"}
```

---

### Step 6: Update Mobile App

In your mobile app, update the API base URL:

```typescript
// Find this in your mobile app config
const API_BASE_URL = 'https://xxxxxxxxxx.execute-api.us-east-1.amazonaws.com/Prod';
```

---

## 🐛 Troubleshooting

### If `aws configure` fails:
- Make sure you've created an IAM user with programmatic access
- Ensure the user has `AdministratorAccess` policy (or at minimum: Lambda, API Gateway, CloudFormation, IAM permissions)

### If deployment fails with "Unable to import module":
```bash
sam build --use-container
sam deploy
```

### If you get database connection errors:
- Verify DATABASE_URL uses the **pooler** (port 6543), not direct connection (port 5432)
- Check that your Supabase database allows connections from `0.0.0.0/0`

---

## 📚 Full Documentation

For detailed information, see:
- [LAMBDA_DEPLOYMENT_GUIDE.md](file:///home/kelly_koome/Devops/wealthcraft-legacy-sim/my_flask_app/LAMBDA_DEPLOYMENT_GUIDE.md)
- [LAMBDA_QUICK_REFERENCE.md](file:///home/kelly_koome/Devops/wealthcraft-legacy-sim/my_flask_app/LAMBDA_QUICK_REFERENCE.md)

---

## 💰 Cost Reminder

- **Free tier**: 1,000,000 requests/month
- **Your expected cost**: $0.00 (if under 1M requests)
- **Monitor**: AWS Console → Billing Dashboard

---

**You're ready to deploy! 🚀**

Start with: `aws configure`
