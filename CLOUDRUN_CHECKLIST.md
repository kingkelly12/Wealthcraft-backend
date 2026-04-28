# ✅ Cloud Run Deployment Checklist

Use this checklist to track your progress as you deploy to Cloud Run.

## Phase 1: Setup (Prerequisites)

- [ ] **Install Docker Desktop**
  - Download from https://www.docker.com/products/docker-desktop
  - Test with: `docker --version`

- [ ] **Install Google Cloud CLI**
  - Follow: https://cloud.google.com/sdk/docs/install
  - Test with: `gcloud --version`

- [ ] **Have a Google Cloud Project**
  - Create at https://console.cloud.google.com/projectcreate
  - Enable billing (Cloud Run free tier, but billing required)
  - Get your Project ID

## Phase 2: Docker Setup

- [ ] **Verify Dockerfile exists**
  - File: `./Dockerfile` (in repo root)
  - Command: `ls -la Dockerfile`

- [ ] **Verify .dockerignore exists**
  - File: `./.dockerignore`
  - Prevents unnecessary files from being copied to image

- [ ] **Verify .env.example exists**
  - File: `./.env.example`
  - Template for your secrets

- [ ] **Create .env file locally**
  - Command: `cp .env.example .env`
  - Edit with your actual secrets
  - ⚠️ Add `.env` to `.gitignore` (should be there already!)

- [ ] **Test Docker build locally**
  - Command: `docker build -t wealthcraft-backend:latest .`
  - Should complete without errors
  - Takes ~2-3 minutes first time (caches dependencies after)

- [ ] **Test Docker run locally**
  - Command: `docker run -p 8080:8080 --env-file .env wealthcraft-backend:latest`
  - Wait 3-5 seconds for server to start
  - In another terminal: `curl http://localhost:8080/health`
  - Should see: `{"status": "healthy"...}`
  - Stop with: `Ctrl+C`

## Phase 3: Google Cloud Setup

- [ ] **Authenticate with Google**
  - Command: `gcloud auth login`
  - Opens browser, sign in with your Google account

- [ ] **Set your Project ID**
  - Command: `gcloud config set project YOUR_PROJECT_ID`
  - Replace `YOUR_PROJECT_ID` with your actual project ID
  - Verify: `gcloud config get-value project`

- [ ] **Enable Required APIs**
  - Command from CLOUDRUN_DEPLOYMENT_GUIDE.md step 2c
  - This takes 1-2 minutes

- [ ] **Configure Docker for GCR**
  - Command: `gcloud auth configure-docker gcr.io`
  - Allows Docker to push to Google Container Registry

## Phase 4: Store Secrets in Google Cloud

- [ ] **Create secrets in Secret Manager**
  - Command from CLOUDRUN_DEPLOYMENT_GUIDE.md step 5
  - Create one secret for each environment variable
  - From `.env` file: DATABASE_URL, SUPABASE_URLs, API keys, etc.
  - Example: `echo -n "value" | gcloud secrets create SECRET_NAME --data-file=-`

- [ ] **Verify secrets created**
  - Command: `gcloud secrets list`
  - Should see all your secrets listed

## Phase 5: Push to Google Container Registry

- [ ] **Tag Docker image for GCR**
  - Command: `docker tag wealthcraft-backend:latest gcr.io/YOUR_PROJECT_ID/wealthcraft-backend:latest`

- [ ] **Push image to GCR**
  - Command: `docker push gcr.io/YOUR_PROJECT_ID/wealthcraft-backend:latest`
  - Should see: "Pushed gcr.io/..."
  - Takes 1-5 minutes (depends on image size and internet)

- [ ] **Verify image in GCR**
  - Command: `gcloud container images list`
  - Should see: `gcr.io/YOUR_PROJECT_ID/wealthcraft-backend`

## Phase 6: Deploy to Cloud Run

- [ ] **Deploy service**
  - Command from CLOUDRUN_DEPLOYMENT_GUIDE.md step 6
  - Or use: `./deploy.sh deploy` (if you set `export GCP_PROJECT_ID=...`)
  - Takes 1-2 minutes

- [ ] **Get your public URL**
  - Command: `gcloud run services describe wealthcraft-backend --region us-central1`
  - Look for: `status.url`
  - This is your public API endpoint!

- [ ] **Test your deployed API**
  - Command: `curl https://YOUR_CLOUD_RUN_URL/health`
  - Should see: `{"status": "healthy"...}`

- [ ] **Test another endpoint**
  - Try: `curl https://YOUR_CLOUD_RUN_URL/`
  - Should see your root endpoint response

## Phase 7: Monitoring

- [ ] **View logs**
  - Command: `gcloud run logs read wealthcraft-backend --limit 50 --follow`
  - This streams live logs from your deployed app

- [ ] **View metrics in Cloud Console**
  - Go to: https://console.cloud.google.com/run
  - Click your service name
  - View: CPU, Memory, Requests, Errors

- [ ] **Check billing**
  - Go to: https://console.cloud.google.com/billing
  - Your usage should be in the free tier

## Phase 8: Updates (After Making Code Changes)

When you modify code:

- [ ] **Rebuild image locally**
  - Command: `docker build -t wealthcraft-backend:v2 .`

- [ ] **Tag and push**
  - Tag: `docker tag wealthcraft-backend:v2 gcr.io/YOUR_PROJECT_ID/wealthcraft-backend:v2`
  - Push: `docker push gcr.io/YOUR_PROJECT_ID/wealthcraft-backend:v2`

- [ ] **Deploy new version**
  - Command: `gcloud run deploy wealthcraft-backend --image gcr.io/YOUR_PROJECT_ID/wealthcraft-backend:v2 --region us-central1`

---

## Quick Commands Reference

```bash
# Setup
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud services enable run.googleapis.com containerregistry.googleapis.com cloudbuild.googleapis.com secretmanager.googleapis.com
gcloud auth configure-docker gcr.io

# Local testing
docker build -t wealthcraft-backend:latest .
docker run -p 8080:8080 --env-file .env wealthcraft-backend:latest

# Push to GCR
docker tag wealthcraft-backend:latest gcr.io/YOUR_PROJECT_ID/wealthcraft-backend:latest
docker push gcr.io/YOUR_PROJECT_ID/wealthcraft-backend:latest

# Deploy
gcloud run deploy wealthcraft-backend \
  --image gcr.io/YOUR_PROJECT_ID/wealthcraft-backend:latest \
  --platform managed --region us-central1 \
  --memory 512Mi --allow-unauthenticated

# Monitor
gcloud run logs read wealthcraft-backend --limit 50 --follow
gcloud run services describe wealthcraft-backend --region us-central1
```

---

## Troubleshooting

**"Docker: command not found"**
→ Docker Desktop not installed. Download from https://www.docker.com/products/docker-desktop

**"gcloud: command not found"**
→ Google Cloud CLI not installed. Follow: https://cloud.google.com/sdk/docs/install

**"Service Accounts"**
→ If you get permission errors, you may need to enable logging service account

**"Image too large"**
→ Make sure .dockerignore is correctly set up
→ Typical size should be 150-300MB

**Can't connect to Docker daemon**
→ Docker Desktop is not running. Start it first!

---

## When You're Done 🎉

1. ✅ You have a Cloud Run service running your Flask app
2. ✅ You have a public API endpoint
3. ✅ You can monitor logs and metrics
4. ✅ You can update your app by pushing new Docker images
5. ✅ You're using Google Cloud's managed serverless platform

Next learning goals:
- Set up CI/CD to auto-deploy when you push to GitHub
- Add custom domain name
- Scale up if you get more users
- Add database backups
