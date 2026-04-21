# Deployment Checklist - Google Cloud with GitHub CI/CD

## Pre-Deployment Setup

- [ ] **Google Cloud Project Created**
  - Project ID: ________________
  - Region: us-central1 (recommended)

- [ ] **APIs Enabled**
  - [ ] Cloud Run API
  - [ ] Cloud Build API
  - [ ] Container Registry API
  - [ ] Cloud Resource Manager API

- [ ] **Service Account Created and Configured**
  - [ ] Service account `github-deployer` created
  - [ ] Roles assigned: run.admin, storage.admin, container.developer, iam.serviceAccountUser
  - [ ] Workload Identity Federation configured (pool + OIDC provider)
  - [ ] `roles/iam.workloadIdentityUser` binding added for your GitHub repo

- [ ] **MongoDB Atlas**
  - [ ] Cluster created and running
  - [ ] Connection string obtained: `mongodb+srv://...`
  - [ ] Username and password created
  - [ ] Database name: `FSDMiniProject`

## Code Changes

### Backend (`/backend/`)
- [ ] `Dockerfile` created
- [ ] `requirements.txt` updated with `gunicorn==23.0.0`
- [ ] `.gcloudignore` created
- [ ] `run.py` updated to support production mode

### Frontend (`/frontend/`)
- [ ] `Dockerfile` created
- [ ] `.gcloudignore` created
- [ ] `.env.production` created with correct API URL placeholder
- [ ] `src/api/client.js` supports `VITE_API_URL` (already configured)

### Root Project
- [ ] `.github/workflows/deploy.yml` created
- [ ] `DEPLOYMENT.md` created (this guide)
- [ ] `docker-compose.yml` created for local testing

## GitHub Configuration

- [ ] **Repository Settings**
  - [ ] GitHub token generated (if needed for advanced setup)
  - [ ] Protected branch rules set for `main` branch

- [ ] **Secrets Added** (Settings → Secrets and variables → Actions)
  - [ ] `GCP_PROJECT_ID` = your-project-id
  - [ ] `GCP_WORKLOAD_IDENTITY_PROVIDER` = projects/PROJECT_NUMBER/locations/global/workloadIdentityPools/github-pool/providers/github-provider
  - [ ] `GCP_SERVICE_ACCOUNT_EMAIL` = github-deployer@your-project-id.iam.gserviceaccount.com
  - [ ] `MONGODB_URI` = mongodb+srv://user:pass@cluster...
  - [ ] `MONGODB_DB_NAME` = FSDMiniProject
  - [ ] `SECRET_KEY` = (generate with: `python -c "import secrets; print(secrets.token_hex(32))"`)
  - [ ] `JWT_SECRET_KEY` = (generate same way)
  - [ ] `CORS_ORIGINS` = https://your-domain.com
  - [ ] `VITE_API_URL` = https://api.your-domain.com/api (or backend Cloud Run URL)

## Pre-Deployment Testing

- [ ] **Local Testing with Docker Compose**
  ```bash
  docker-compose up --build
  ```
  - [ ] Frontend accessible at http://localhost:3000
  - [ ] Backend accessible at http://localhost:5000
  - [ ] API health check: `curl http://localhost:5000/api/health`
  - [ ] Can register/login/create events without errors

- [ ] **Backend Docker Build**
  ```bash
  cd backend && docker build -t event-platform-backend:test .
  ```
  - [ ] Image builds without errors
  - [ ] Image runs locally: `docker run -p 5000:8080 event-platform-backend:test`

- [ ] **Frontend Docker Build**
  ```bash
  cd frontend && docker build -t event-platform-frontend:test .
  ```
  - [ ] Image builds without errors
  - [ ] Image runs locally: `docker run -p 3000:3000 event-platform-frontend:test`

## Initial Deployment

- [ ] **GitHub Actions Workflow Triggered**
  - [ ] Push to `main` branch triggers workflow
  - [ ] Workflow runs without errors in GitHub Actions tab
  - [ ] Check logs for any failures

- [ ] **Backend Deployment**
  - [ ] Image pushed to Google Container Registry (gcr.io)
  - [ ] Backend deployed to Cloud Run
  - [ ] Cloud Run service URL: `https://event-platform-backend-xxxxx.a.run.app`
  - [ ] Health check passes: `curl https://event-platform-backend-xxxxx.a.run.app/api/health`

- [ ] **Frontend Deployment**
  - [ ] Image pushed to Google Container Registry
  - [ ] Frontend deployed to Cloud Run
  - [ ] Cloud Run service URL: `https://event-platform-frontend-xxxxx.a.run.app`
  - [ ] Frontend loads in browser without errors

## Post-Deployment Verification

- [ ] **Backend API Tests**
  - [ ] Health check: `curl https://event-platform-backend-xxxxx.a.run.app/api/health`
  - [ ] Auth endpoint: `POST /api/auth/register` works
  - [ ] Events endpoint: `GET /api/events` returns data
  - [ ] Registration flow: Create event → Register for event → Success

- [ ] **Frontend Tests**
  - [ ] Landing page loads
  - [ ] Login page functional
  - [ ] Can register new account
  - [ ] Can view events
  - [ ] Can register for event
  - [ ] API calls use correct backend URL (check browser Network tab)
  - [ ] No CORS errors in browser console

- [ ] **Database Connectivity**
  - [ ] MongoDB Atlas whitelist includes Cloud Run IP or 0.0.0.0/0
  - [ ] Data persists after refresh
  - [ ] Admin functions work (if applicable)

- [ ] **Logs and Monitoring**
  - [ ] Backend logs accessible: `gcloud run logs read event-platform-backend --limit 10`
  - [ ] Frontend logs accessible: `gcloud run logs read event-platform-frontend --limit 10`
  - [ ] No error messages in logs

## Security Checklist

- [ ] **Environment Variables**
  - [ ] SECRET_KEY is strong (32+ characters)
  - [ ] JWT_SECRET_KEY is strong
  - [ ] MongoDB credentials never hardcoded
  - [ ] No service account JSON key is used (OIDC/WIF only)

- [ ] **CORS Configuration**
  - [ ] CORS_ORIGINS only includes your domain(s)
  - [ ] Wildcard (*) not used in production

- [ ] **Database Access**
  - [ ] MongoDB IP whitelist configured (preferably specific IPs)
  - [ ] Database credentials use strong password
  - [ ] Read-only database user created (if needed)

- [ ] **API Security**
  - [ ] JWT tokens properly validated on backend
  - [ ] Protected routes require authentication
  - [ ] Rate limiting considered (optional but recommended)

## Domain Setup (Optional)

- [ ] **Custom Domain**
  - [ ] Domain registered and DNS provider configured
  - [ ] SSL certificate obtained/created
  - [ ] Cloud Load Balancer configured (if using custom domain)
  - [ ] DNS A record points to load balancer IP
  - [ ] SSL/TLS certificate installed in Cloud Load Balancer

- [ ] **Frontend `.env.production` Updated**
  - [ ] `VITE_API_URL` points to backend (either Cloud Run or custom API domain)
  - [ ] No localhost URLs in production

## Ongoing Operations

- [ ] **Monitoring Setup**
  - [ ] Cloud Run metrics dashboard created
  - [ ] Alerts configured for:
    - [ ] High error rate (>5%)
    - [ ] High latency (>5s)
    - [ ] High memory usage (>90%)

- [ ] **Backup Strategy**
  - [ ] MongoDB Atlas automated backups enabled
  - [ ] Backup retention policy set (7+ days recommended)

- [ ] **Update Process Documented**
  - [ ] Team knows to push to `main` to trigger auto-deployment
  - [ ] Rollback procedure documented
  - [ ] Change log maintained

- [ ] **Performance Optimization**
  - [ ] Cloud Run min instances set appropriately
  - [ ] Cloud Run max instances set appropriately
  - [ ] Frontend caching headers configured (if using CDN)

## Troubleshooting Notes

Record any issues encountered and their solutions:

```
Issue: ________________
Solution: ________________

Issue: ________________
Solution: ________________
```

## Sign-Off

- [ ] Deployment lead: ________________ Date: ________
- [ ] QA verification: ________________ Date: ________
- [ ] Production ready: ✅

---

**Next Steps:**
1. Follow DEPLOYMENT.md for detailed step-by-step guide
2. Keep this checklist updated as you proceed
3. Document any deviations from this process
