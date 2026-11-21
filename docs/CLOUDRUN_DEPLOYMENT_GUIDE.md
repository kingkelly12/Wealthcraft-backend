# 🚀 Google Cloud Run Deployment Guide
## Wealthcraft Backend

This guide walks you through deploying your Flask app to Google Cloud Run step-by-step.

---

## Prerequisites

### What You Need
- ✅ Google Cloud Project (with billing enabled)
- ✅ Docker Desktop installed locally
- ✅ Google Cloud CLI (`gcloud`)
- ✅ A Docker Hub account OR use Google Artifact Registry (built into GCP)

### Billing Note
- Cloud Run has a generous **free tier**: 2 million requests/month
- You only pay for the time your container is actually running
- First container instance is free (up to 180,000 vCPU-seconds/month)

---

## Step 1: Install Google Cloud CLI

### On Linux/MacOS:
```bash
# Download the installer
curl https://sdk.cloud.google.com | bash

# Restart terminal to apply PATH changes
exec -l $SHELL

# Verify installation
gcloud --version
```

### On Windows (WSL2):
```bash
# Same as above - runs in WSL
curl https://sdk.cloud.google.com | bash
exec -l $SHELL
gcloud --version
```

---

## Step 2: Initialize Google Cloud Project

### 2a. Authenticate with Google
```bash
gcloud auth login
```
This opens a browser to sign in with your Google account. Then:
- Select your Google Cloud Project
- Grant permissions

### 2b. Set Your Project
```bash
# List all your projects
gcloud projects list

# Set the active project (replace YOUR_PROJECT_ID)
gcloud config set project YOUR_PROJECT_ID

# Verify it's set
gcloud config get-value project
```

### 2c. Enable Required APIs
Cloud Run needs these APIs enabled:
```bash
# Enable Cloud Run API
gcloud services enable run.googleapis.com

# Enable Container Registry (we'll push Docker images here)
gcloud services enable containerregistry.googleapis.com

# Enable Cloud Build (to build Docker images on GCP instead of locally)
gcloud services enable cloudbuild.googleapis.com

# Enable Secret Manager (to store secrets like API keys)
gcloud services enable secretmanager.googleapis.com
```

### 2d. Configure Docker Authentication
Docker needs permission to push images to Google's registry:
```bash
# Configure Docker to use gcloud as credential helper
gcloud auth configure-docker gcr.io
```

---

## Step 3: Test Docker Build Locally

Before deploying to Cloud Run, test your Docker image locally:

```bash
# Build the image (from the root directory of Wealthcraft-backend)
docker build -t wealthcraft-backend:latest .

# Run it locally to test
docker run -p 8080:8080 \
  -e FLASK_CONFIG=production \
  -e SUPABASE_URL="your_supabase_url" \
  -e SUPABASE_KEY="your_supabase_key" \
  -e SUPABASE_SERVICE_ROLE_KEY="your_service_role_key" \
  -e SUPABASE_JWT_SECRET="your_jwt_secret" \
  -e GOOGLE_WEB_CLIENT_ID="your_google_client_id" \
  -e GEMINI_API_KEY="your_gemini_key" \
  -e SECRET_KEY="some_random_secret" \
  -e DATABASE_URL="your_postgres_url" \
  wealthcraft-backend:latest

# Test the health endpoint in another terminal
curl http://localhost:8080/health

# You should see: {"status": "healthy", "message": "Adulting API is running"}
```

If this works locally, your Docker setup is correct! ✅

---

## Step 4: Push Docker Image to Google Container Registry

This is where your Docker image lives in the cloud:

```bash
# Tag your image with GCR format
# Format: gcr.io/PROJECT_ID/IMAGE_NAME:TAG
docker tag wealthcraft-backend:latest gcr.io/YOUR_PROJECT_ID/wealthcraft-backend:latest

# Push to Google Container Registry
docker push gcr.io/YOUR_PROJECT_ID/wealthcraft-backend:latest

# Verify it pushed
gcloud container images list
```

---

## Step 5: Store Secrets in Google Secret Manager

Instead of passing secrets on the command line, use Secret Manager:

```bash
# Create a secret for your database URL
echo -n "your_database_url" | gcloud secrets create DATABASE_URL --data-file=-

# Create a secret for Supabase URL
echo -n "your_supabase_url" | gcloud secrets create SUPABASE_URL --data-file=-

# Create other secrets (repeat for each)
echo -n "your_service_role_key" | gcloud secrets create SUPABASE_SERVICE_ROLE_KEY --data-file=-
echo -n "your_jwt_secret" | gcloud secrets create SUPABASE_JWT_SECRET --data-file=-
echo -n "your_google_client_id" | gcloud secrets create GOOGLE_WEB_CLIENT_ID --data-file=-
echo -n "your_gemini_key" | gcloud secrets create GEMINI_API_KEY --data-file=-
echo -n "your_random_secret" | gcloud secrets create SECRET_KEY --data-file=-

# List all secrets
gcloud secrets list
```

---

## Step 6: Deploy to Cloud Run

This is the exciting part! 🎉

```bash
gcloud run deploy wealthcraft-backend \
  --image gcr.io/YOUR_PROJECT_ID/wealthcraft-backend:latest \
  --platform managed \
  --region us-central1 \
  --memory 512Mi \
  --cpu 1 \
  --timeout 120 \
  --allow-unauthenticated \
  --set-env-vars "FLASK_CONFIG=production" \
  --set-secrets "DATABASE_URL=DATABASE_URL:latest,SUPABASE_URL=SUPABASE_URL:latest,SUPABASE_SERVICE_ROLE_KEY=SUPABASE_SERVICE_ROLE_KEY:latest,SUPABASE_JWT_SECRET=SUPABASE_JWT_SECRET:latest,GOOGLE_WEB_CLIENT_ID=GOOGLE_WEB_CLIENT_ID:latest,GEMINI_API_KEY=GEMINI_API_KEY:latest,SECRET_KEY=SECRET_KEY:latest" \
  --max-instances 10
```

**Parameters Explained**:
- `--image`: The Docker image from GCR
- `--platform managed`: Serverless Cloud Run (recommended for beginners)
- `--region us-central1`: Closest region to your users
- `--memory 512Mi`: Start with 512MB RAM (adjust up if needed)
- `--cpu 1`: 1 CPU core (standard for most APIs)
- `--timeout 120`: Requests timeout after 120 seconds
- `--allow-unauthenticated`: Anyone can call your API (change if you need auth)
- `--max-instances 10`: Max 10 concurrent containers (adjust based on load)

---

## Step 7: Verify Your Deployment

```bash
# Get the service URL (this is your public API endpoint!)
gcloud run services describe wealthcraft-backend --region us-central1

# Or just list all services
gcloud run services list

# Test the health endpoint with your public URL
curl https://YOUR_CLOUD_RUN_URL/health

# You should see: {"status": "healthy", "message": "Adulting API is running"}
```

---

## Monitoring & Logs

### View Real-Time Logs
```bash
# Stream logs from Cloud Run
gcloud run logs read wealthcraft-backend --limit 100 --follow --region us-central1
```

### Check Metrics in Cloud Console
1. Go to [Cloud Run Console](https://console.cloud.google.com/run)
2. Click your service name
3. View CPU, Memory, Request Rate, Error Rate

---

## Update Your Deployment

When you make code changes:

```bash
# 1. Build the image locally
docker build -t wealthcraft-backend:v2 .

# 2. Tag it
docker tag wealthcraft-backend:v2 gcr.io/YOUR_PROJECT_ID/wealthcraft-backend:v2

# 3. Push to GCR
docker push gcr.io/YOUR_PROJECT_ID/wealthcraft-backend:v2

# 4. Deploy the new version
gcloud run deploy wealthcraft-backend \
  --image gcr.io/YOUR_PROJECT_ID/wealthcraft-backend:v2 \
  --region us-central1
```

Or use Cloud Build to automate this:
```bash
gcloud run deploy wealthcraft-backend \
  --source . \
  --platform managed \
  --region us-central1
```

---

## Troubleshooting

### "Container failed to start"
→ Check logs: `gcloud run logs read wealthcraft-backend --limit 50`

### "Cold start is slow"
→ Cloud Run instances sleep after 15 minutes of inactivity. First request after will be slow.
→ Solution: Use Cloud Scheduler to ping `/health` every 5 minutes

### "Out of memory"
→ Increase `--memory` flag (256Mi → 512Mi → 1Gi)
→ Check if database queries are leaking memory

### "All requests returning 403"
→ You probably set `--no-allow-unauthenticated` by mistake
→ Re-deploy with `--allow-unauthenticated`

---

## Next Steps

1. ✅ Set up monitoring & alerts in Cloud Console
2. ✅ Configure a custom domain (Cloud Run → Settings → Custom Domains)
3. ✅ Set up CI/CD pipeline using Cloud Build or GitHub Actions
4. ✅ Add database backup strategy for Supabase
5. ✅ Implement request logging and error tracking

---

## Cost Estimation

For a typical junior dev project:

| Resource | Usage | Cost |
|----------|-------|------|
| Cloud Run | 1M requests/month | **FREE** (within free tier) |
| Container Registry | 1GB storage | ~$0.10/GB = **$0.10** |
| Cloud Logs | 50GB logs/month | **FREE** (first 50GB) |
| Secrets Storage | 6 secrets | ~$0.06/secret = **~$0.40** |
| **Total** | | **~$0.50/month** |

That's basically free for learning! 🎉

---

Helpful Links:
- [Cloud Run Docs](https://cloud.google.com/run/docs)
- [Cloud Run Console](https://console.cloud.google.com/run)
- [Cloud Run Pricing](https://cloud.google.com/run/pricing)
- [Docker Best Practices](https://docs.docker.com/develop/dev-best-practices/)
