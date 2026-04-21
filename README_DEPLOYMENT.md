# Event Management Platform - Deployment Guide

This document provides an overview of deployment options for the Event Management Platform.

## Quick Links

- **[30-Minute Quick Start](DEPLOYMENT_SUMMARY.md)** - Get deployed in 30 minutes ⚡
- **[Complete Deployment Guide](DEPLOYMENT.md)** - Detailed step-by-step instructions 📖
- **[Deployment Checklist](DEPLOYMENT_CHECKLIST.md)** - Pre and post-deployment checklist ✓

## Deployment Options

### 1. Google Cloud (Recommended) ⭐

**Best for**: Production deployments, auto-scaling, global reach

**Stack**:
- Backend: Cloud Run (Flask with gunicorn)
- Frontend: Cloud Run (React/Vite)
- Database: MongoDB Atlas (fully managed)
- CI/CD: GitHub Actions

**Cost**: ~$0-5/month (includes free tier)

**Setup time**: 30 minutes

**Benefits**:
- Fully serverless, no infrastructure to manage
- Auto-scaling from 0-100 instances
- Pay per request
- Global CDN available
- Easy custom domain setup

**Get started**: [See DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)

---

### 2. Local Development with Docker

**Best for**: Development, testing before deployment

**Stack**:
- Backend: Flask with gunicorn
- Frontend: Node.js development server
- Database: MongoDB Atlas (same as production)

**Setup**:
```bash
# Start services
docker-compose up --build

# Access
Frontend: http://localhost:3000
Backend: http://localhost:5000
```

**File**: `docker-compose.yml`

---

### 3. Traditional VPS Deployment (Alternative)

**Best for**: Budget-conscious, full control needed

**Options**:
- DigitalOcean, Linode, AWS EC2, Heroku

**Stack**:
- Backend: Gunicorn + Nginx/Apache reverse proxy
- Frontend: Static files served via Nginx
- Database: MongoDB Atlas
- Deployment: Manual or with tools like Capistrano

**Cost**: $5-20/month

---

## Architecture Diagram

```
GitHub Repository
    │
    ├─ Push to main branch
    │
    ▼
GitHub Actions (CI/CD)
    │
    ├─ Run Tests
    ├─ Build Docker Images
    ├─ Push to Google Container Registry
    │
    ▼
Google Cloud Run
    │
    ├─ Backend Service (Flask)
    │   └─ Auto-scales 0-100 instances
    │
    ├─ Frontend Service (React)
    │   └─ Auto-scales 0-10 instances
    │
    ▼
MongoDB Atlas (Database)
    │
    └─ Fully managed cloud database
```

## Environment Variables

Both frontend and backend use environment variables for configuration:

### Backend (`.env` or GitHub Secrets)
```
FLASK_ENV=production
MONGODB_URI=mongodb+srv://user:pass@cluster...
MONGODB_DB_NAME=FSDMiniProject
SECRET_KEY=<random-32-char-key>
JWT_SECRET_KEY=<random-32-char-key>
CORS_ORIGINS=https://your-domain.com
```

### Frontend (`.env.production`)
```
VITE_API_URL=https://api.your-domain.com/api
```

## Security Considerations

1. **Never commit secrets** - Use environment variables and GitHub Secrets
2. **CORS configuration** - Only allow your domain(s)
3. **HTTPS only** - All production URLs must use HTTPS
4. **Database access** - MongoDB IP whitelist should be restrictive
5. **API authentication** - JWT tokens for protected endpoints

## Monitoring & Logging

### Google Cloud Console
- View real-time logs
- Monitor CPU, memory, requests
- Set up alerts

### Terminal
```bash
# View backend logs
gcloud run logs read event-platform-backend --limit 100

# View frontend logs
gcloud run logs read event-platform-frontend --limit 100

# Follow logs in real-time
gcloud run logs read event-platform-backend --follow
```

## Continuous Deployment Workflow

1. **Develop locally**
   ```bash
   docker-compose up
   ```

2. **Commit and push**
   ```bash
   git add .
   git commit -m "Your changes"
   git push origin main
   ```

3. **GitHub Actions deploys automatically**
   - Check progress in GitHub Actions tab
   - Deployment completes in 3-5 minutes

4. **Live on Google Cloud**
   - Backend: `https://event-platform-backend-xxxxx.a.run.app`
   - Frontend: `https://event-platform-frontend-xxxxx.a.run.app`

## Rollback Process

If deployment breaks, rollback is simple:

```bash
# View previous deployments
gcloud run revisions list --service=event-platform-backend

# Switch to previous version
gcloud run services update-traffic event-platform-backend \
  --to-revisions PREVIOUS_REVISION=100
```

## Cost Breakdown

### Free Tier (usually sufficient)
- Cloud Run: 2M requests/month
- MongoDB Atlas: 512MB storage
- Cloud Build: 120 build minutes/month

### Paid Usage (if you exceed)
- Cloud Run: $0.00001667 per request
- Storage: Minimal for small datasets
- Network egress: ~$0.12/GB

**Typical monthly cost**: $0-5

## Scaling

Cloud Run automatically scales based on demand:

- **Min instances**: 0 (scales down when idle)
- **Max instances**: 100 (default, configurable)
- **Concurrency**: 80 (requests per instance)

Adjust with:
```bash
gcloud run services update event-platform-backend \
  --min-instances 1 \
  --max-instances 100
```

## Custom Domain Setup

1. Register domain
2. Get SSL certificate
3. Set up Cloud Load Balancer
4. Add DNS A record
5. Update CORS_ORIGINS in secrets

See [DEPLOYMENT.md](DEPLOYMENT.md#step-7-set-up-custom-domain-optional) for details.

## Files Used for Deployment

```
.github/
  └─ workflows/
      └─ deploy.yml          # CI/CD pipeline

backend/
  ├─ Dockerfile             # Container configuration
  ├─ .gcloudignore          # Files to exclude
  ├─ requirements.txt       # Python dependencies
  └─ run.py                 # Entry point (updated)

frontend/
  ├─ Dockerfile             # Container configuration
  ├─ .gcloudignore          # Files to exclude
  └─ .env.production        # Production config

scripts/
  └─ setup-github-secrets.sh # Helper script

docker-compose.yml          # Local development
DEPLOYMENT_SUMMARY.md       # Quick start (THIS FILE)
DEPLOYMENT.md               # Complete guide
DEPLOYMENT_CHECKLIST.md     # Checklist
```

## Troubleshooting

### Backend won't start
```bash
# Check logs for MongoDB error
gcloud run logs read event-platform-backend --limit 50

# Verify MONGODB_URI is correct
# Verify MongoDB IP whitelist includes Cloud Run
```

### Frontend shows blank page
```bash
# Check browser console for API errors
# Verify VITE_API_URL points to correct backend
# Check CORS is configured correctly
```

### Deployment fails in GitHub Actions
```bash
# Check GitHub Actions logs
# Verify all secrets are set correctly
# Ensure Dockerfile builds locally
```

## Getting Help

1. **Check logs first** - Most issues visible in logs
2. **Review DEPLOYMENT.md** - Covers common issues
3. **GitHub Actions tab** - See deployment progress and errors
4. **Google Cloud Console** - View service status and metrics

## Next Steps

1. **Choose deployment method** (Google Cloud recommended)
2. **Follow deployment guide** (30 minutes)
3. **Test in staging** (optional)
4. **Deploy to production**
5. **Setup monitoring** (optional but recommended)
6. **Setup custom domain** (optional)

---

**Ready to deploy? Start with [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) for a quick 30-minute setup!**
