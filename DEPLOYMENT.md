# Deployment Guide: Google Cloud

This document outlines all steps needed to deploy the Event Management Platform to Google Cloud with GitHub CI/CD.

## Prerequisites

1. **Google Cloud Project**: Create one at [https://console.cloud.google.com](https://console.cloud.google.com)
2. **GitHub Account**: With access to this repository
3. **MongoDB Atlas Cluster**: Already set up with connection string
4. **Custom Domain** (Optional): For production deployment

## Step 1: Set Up Google Cloud Project

### 1.1 Enable Required APIs
```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable container.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable iamcredentials.googleapis.com
```

### 1.2 Create a Service Account
```bash
# Create service account
gcloud iam service-accounts create github-deployer \
  --display-name="GitHub Deployment Account"

# Grant necessary roles
gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:github-deployer@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/run.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:github-deployer@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/storage.admin"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:github-deployer@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/container.developer"

gcloud projects add-iam-policy-binding $GCP_PROJECT_ID \
  --member="serviceAccount:github-deployer@$GCP_PROJECT_ID.iam.gserviceaccount.com" \
  --role="roles/iam.serviceAccountUser"
```

### 1.3 Configure Workload Identity Federation (Keyless GitHub Auth)
```bash
# Set your GitHub repo details
export GITHUB_ORG="YOUR_GITHUB_ORG"
export GITHUB_REPO="mini-project"

# Create pool and provider
gcloud iam workload-identity-pools create github-pool \
  --project="$GCP_PROJECT_ID" \
  --location="global" \
  --display-name="GitHub Actions Pool"

gcloud iam workload-identity-pools providers create-oidc github-provider \
  --project="$GCP_PROJECT_ID" \
  --location="global" \
  --workload-identity-pool="github-pool" \
  --display-name="GitHub OIDC Provider" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.repository_owner=assertion.repository_owner,attribute.ref=assertion.ref" \
  --attribute-condition="assertion.repository_owner=='$GITHUB_ORG'"

# Allow only this repo to impersonate the deployment service account
gcloud iam service-accounts add-iam-policy-binding \
  github-deployer@$GCP_PROJECT_ID.iam.gserviceaccount.com \
  --project="$GCP_PROJECT_ID" \
  --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/projects/$(gcloud projects describe $GCP_PROJECT_ID --format='value(projectNumber)')/locations/global/workloadIdentityPools/github-pool/attribute.repository/$GITHUB_ORG/$GITHUB_REPO"
```

## Step 2: Configure GitHub Secrets

Add these secrets to your GitHub repository (Settings → Secrets and variables → Actions):

### Required Secrets:
```
GCP_PROJECT_ID              = your-gcp-project-id
GCP_WORKLOAD_IDENTITY_PROVIDER = projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider
GCP_SERVICE_ACCOUNT_EMAIL   = github-deployer@your-gcp-project-id.iam.gserviceaccount.com
MONGODB_URI                 = mongodb+srv://username:password@cluster.xxxxx.mongodb.net
MONGODB_DB_NAME             = FSDMiniProject
SECRET_KEY                  = (generate a secure random key: python -c "import secrets; print(secrets.token_hex(32))")
JWT_SECRET_KEY              = (generate a secure random key)
CORS_ORIGINS                = https://your-domain.com,https://api.your-domain.com
VITE_API_URL                = https://api.your-domain.com/api
```

### How to Add Secrets:
1. Go to your GitHub repository
2. Settings → Secrets and variables → Actions → New repository secret
3. Add each secret from above
4. Set `GCP_WORKLOAD_IDENTITY_PROVIDER` using:
  ```bash
  PROJECT_NUMBER=$(gcloud projects describe $GCP_PROJECT_ID --format='value(projectNumber)')
  echo "projects/$PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider"
  ```

## Step 3: Update Environment Files

### Backend `.env.gcloud` (for local testing)
```
FLASK_ENV=production
MONGODB_URI=<from secrets>
MONGODB_DB_NAME=FSDMiniProject
SECRET_KEY=<from secrets>
JWT_SECRET_KEY=<from secrets>
CORS_ORIGINS=https://your-domain.com
```

### Frontend `.env.production`
Already configured to use `VITE_API_URL` environment variable set during deployment.

## Step 4: Update Frontend CORS Configuration

The backend CORS is configured via the `CORS_ORIGINS` environment variable. For production, update it in the GitHub secrets.

## Step 5: Deploy Backend to Cloud Run

The backend will be automatically deployed on every push to `main` branch via GitHub Actions.

**Manual Deployment** (if needed):
```bash
cd backend
gcloud run deploy event-platform-backend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60 \
  --set-env-vars MONGODB_URI=$MONGODB_URI,MONGODB_DB_NAME=$MONGODB_DB_NAME,SECRET_KEY=$SECRET_KEY,JWT_SECRET_KEY=$JWT_SECRET_KEY,CORS_ORIGINS=$CORS_ORIGINS
```

Backend URL will be: `https://event-platform-backend-xxxxx.a.run.app`

## Step 6: Deploy Frontend to Cloud Run

The frontend will be automatically deployed on every push to `main` branch via GitHub Actions.

**Manual Deployment** (if needed):
```bash
cd frontend
gcloud run deploy event-platform-frontend \
  --source . \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --memory 256Mi \
  --cpu 1 \
  --set-env-vars VITE_API_URL=https://event-platform-backend-xxxxx.a.run.app/api
```

Frontend URL will be: `https://event-platform-frontend-xxxxx.a.run.app`

## Step 7: Set Up Custom Domain (Optional)

### Using Cloud Load Balancer with SSL Certificate:

```bash
# Create SSL certificate
gcloud compute ssl-certificates create my-cert \
  --certificate=/path/to/cert.crt \
  --private-key=/path/to/key.key

# Create backend service for API
gcloud compute backend-services create api-backend \
  --protocol=HTTPS \
  --health-checks=tcp-health-check

# Create backend service for frontend
gcloud compute backend-services create frontend-backend \
  --protocol=HTTPS \
  --health-checks=tcp-health-check

# Create URL map
gcloud compute url-maps create my-url-map \
  --default-service=frontend-backend

# Add route for API
gcloud compute url-maps add-path-rule my-url-map \
  --service=api-backend \
  --path-rule="/api/*"

# Create HTTPS load balancer
gcloud compute target-https-proxies create my-proxy \
  --url-map=my-url-map \
  --ssl-certificates=my-cert

gcloud compute forwarding-rules create my-https-rule \
  --global \
  --target-https-proxy=my-proxy \
  --address=EXTERNAL_IP \
  --ports=443
```

Then update DNS records to point your domain to the load balancer IP.

## Step 8: Database Access

MongoDB Atlas needs to allow connections from Cloud Run:

1. Go to MongoDB Atlas → Network Access
2. Add Cloud Run IP ranges or allow 0.0.0.0/0 (less secure)
3. Or create a static IP for Cloud Run and whitelist it

## Step 9: GitHub Actions Workflow

The CI/CD pipeline (`.github/workflows/deploy.yml`) will:

1. **On Pull Request**: Run tests and linting (no deployment)
2. **On Push to Main**: 
   - Run tests
   - Build Docker images
   - Push to Google Container Registry
   - Deploy to Cloud Run (backend and frontend)

### To Trigger Manual Deployment:
Push to the `main` branch or manually trigger the workflow in GitHub Actions tab.

## Monitoring & Logs

### View Backend Logs:
```bash
gcloud run logs read event-platform-backend --limit 100
gcloud run logs read event-platform-backend --limit 100 --follow
```

### View Frontend Logs:
```bash
gcloud run logs read event-platform-frontend --limit 100
```

### Metrics & Monitoring:
1. Go to Google Cloud Console
2. Cloud Run → Select service → Metrics tab
3. Monitor CPU, Memory, Request Count, Latency

## Cost Optimization

1. **Cloud Run**: Free tier includes 2M requests/month
2. **MongoDB Atlas**: Free tier with 512MB storage
3. **Set memory and CPU to minimum needed** (512Mi CPU for backend, 256Mi for frontend)
4. **Use auto-scaling settings**:
   ```bash
   gcloud run services update event-platform-backend \
     --min-instances 0 \
     --max-instances 100
   ```

## Rollback

To roll back to a previous deployment:
```bash
gcloud run services update-traffic event-platform-backend \
  --to-revisions REVISION_NAME=100
```

## Environment-Specific Configuration

### Staging (Optional)
To set up a staging environment, create another Cloud Run service and add a workflow trigger on push to `staging` branch.

## Troubleshooting

### Backend Connection Issues
- Check MongoDB URI in secrets matches your cluster
- Verify IP whitelist in MongoDB Atlas
- Check CORS_ORIGINS includes frontend URL

### Frontend API 404 Errors
- Verify `VITE_API_URL` secret is correct
- Check backend is running and accessible
- Test with: `curl https://your-backend-url/api/health`

### Deployment Failures
1. Check GitHub Actions logs for error details
2. Verify all secrets are set correctly
3. Ensure gcloud CLI has correct permissions

## Additional Resources

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Cloud Run Python Guide](https://cloud.google.com/run/docs/quickstarts/build-and-deploy/python)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
