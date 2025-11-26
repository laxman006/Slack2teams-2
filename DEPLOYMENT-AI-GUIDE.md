# AI.CloudFuze.com Deployment Guide

Complete guide for deploying the CF_Chatbot-V1 branch to ai.cloudfuze.com (64.227.160.206) with full frontend and backend support.

---

## 🎯 Deployment Overview

- **Server IP**: 64.227.160.206
- **Domain**: ai.cloudfuze.com
- **Branch**: CF_Chatbot-V1
- **Components**: Next.js Frontend + FastAPI Backend + Nginx Reverse Proxy
- **Container Names**: 
  - `slack2teams-frontend-ai`
  - `slack2teams-backend-ai`
  - `slack2teams-nginx-ai`

---

## 📋 Prerequisites

### On Your Local Machine:
- Docker and Docker Compose installed
- Git configured with access to the repository
- SSH access to the server (root@64.227.160.206)
- Docker Hub account (laxman006) logged in

### On the Server:
- Ubuntu/Debian Linux
- Docker and Docker Compose installed
- Port 80 and 443 open
- SSL certificate for ai.cloudfuze.com (or will be created during deployment)

---

## 🚀 Quick Deployment (Automated)

### Option A: Using the Deployment Script

```bash
# 1. Make script executable
chmod +x deploy-ai.sh

# 2. Run the script
./deploy-ai.sh
```

The script will:
- Build the frontend Docker image locally with correct API URL
- Push the image to Docker Hub
- Setup the server
- Clone the repository
- Deploy all services

---

## 📝 Manual Deployment (Step-by-Step)

### Step 1: Prepare Local Environment

```bash
# Ensure you're on the correct branch
git checkout CF_Chatbot-V1
git pull origin CF_Chatbot-V1

# Check what needs to be committed
git status
```

### Step 2: Build and Push Frontend Image

```bash
# Navigate to frontend directory
cd frontend

# Build the Docker image with correct API URL
docker build -f Dockerfile.frontend -t laxman006/slack2teams-frontend:ai \
  --build-arg NEXT_PUBLIC_API_URL=https://ai.cloudfuze.com .

# Push to Docker Hub
docker push laxman006/slack2teams-frontend:ai

cd ..
```

### Step 3: Commit and Push Changes

```bash
# Add new files
git add nginx-ai.conf docker-compose.ai.yml deploy-ai.sh DEPLOYMENT-AI-GUIDE.md

# Commit changes
git commit -m "feat: add deployment configuration for ai.cloudfuze.com"

# Push to repository
git push origin CF_Chatbot-V1
```

### Step 4: Prepare the Server

```bash
# SSH into the server
ssh root@64.227.160.206

# Stop old services (if any)
cd /opt/slack2teams 2>/dev/null && docker-compose down || true
cd /opt/slack2teams-prod 2>/dev/null && docker-compose down || true

# Create project directory
mkdir -p /opt/slack2teams-ai
cd /opt/slack2teams-ai

# Install/update Docker
apt-get update
apt-get install -y docker.io docker-compose git curl certbot python3-certbot-nginx

# Ensure Docker is running
systemctl start docker
systemctl enable docker
```

### Step 5: Clone Repository

```bash
# Still on the server
cd /opt/slack2teams-ai

# Clone the repository (CF_Chatbot-V1 branch)
git clone -b CF_Chatbot-V1 https://github.com/laxman006/chatbot.git .

# Verify you're on the correct branch
git branch
```

### Step 6: Create Environment File

Create `.env.ai` file on the server:

```bash
# On the server
nano /opt/slack2teams-ai/.env.ai
```

Add the following content (replace with your actual values):

```env
# OpenAI Configuration
OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE

# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=your-client-id-here
MICROSOFT_CLIENT_SECRET=your-client-secret-here
MICROSOFT_TENANT=cloudfuze.com

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-your-key-here
LANGFUSE_SECRET_KEY=sk-lf-your-key-here
LANGFUSE_HOST=https://cloud.langfuse.com

# MongoDB Configuration
MONGODB_URL=mongodb+srv://user:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DATABASE=slack2teams
MONGODB_CHAT_COLLECTION=chat_histories
MONGODB_VECTORSTORE_COLLECTION=vectorstore

# Vectorstore Configuration
VECTORSTORE_BACKEND=mongodb
INITIALIZE_VECTORSTORE=false

# Data Sources
ENABLE_WEB_SOURCE=true
ENABLE_SHAREPOINT_SOURCE=true
ENABLE_OUTLOOK_SOURCE=true
ENABLE_PDF_SOURCE=false
ENABLE_EXCEL_SOURCE=false
ENABLE_DOC_SOURCE=false

# Web/Blog Configuration
WEB_SOURCE_URL=https://cloudfuze.com/wp-json/wp/v2/posts?per_page=100
WEB_START_PAGE=1
WEB_MAX_PAGES=100

# SharePoint Configuration
SHAREPOINT_SITE_URL=https://cloudfuzecom.sharepoint.com/sites/DOC360
SHAREPOINT_START_PAGE=
SHAREPOINT_MAX_DEPTH=999
SHAREPOINT_EXCLUDE_FILES=true

# Outlook Configuration
OUTLOOK_USER_EMAIL=presales@cloudfuze.com
OUTLOOK_FOLDER_NAME=inbox
OUTLOOK_MAX_EMAILS=10000
OUTLOOK_DATE_FILTER=last_6_months

# Chunking Configuration
CHUNK_TARGET_TOKENS=800
CHUNK_OVERLAP_TOKENS=200
CHUNK_MIN_TOKENS=150

# Deduplication
ENABLE_DEDUPLICATION=true
DEDUP_THRESHOLD=0.85

# Unstructured and OCR
ENABLE_UNSTRUCTURED=true
ENABLE_OCR=true
OCR_LANGUAGE=eng

# Graph Storage
GRAPH_DB_PATH=./data/graph_relations.db
ENABLE_GRAPH_STORAGE=true

# Reranker and Verifier
RERANKER_SHADOW=false
RERANKER_ENABLED=true
VERIFIER_ENABLED=true

# Python Settings
PYTHONUNBUFFERED=1
ENVIRONMENT=production
```

Save and exit (Ctrl+X, Y, Enter).

### Step 7: Setup SSL Certificate

```bash
# On the server
# Stop nginx if running
docker stop slack2teams-nginx-ai 2>/dev/null || true

# Get SSL certificate
certbot certonly --standalone -d ai.cloudfuze.com \
  --agree-tos --non-interactive --email admin@cloudfuze.com

# Verify certificate was created
ls -la /etc/letsencrypt/live/ai.cloudfuze.com/
```

### Step 8: Pull Frontend Image

```bash
# On the server
cd /opt/slack2teams-ai
docker pull laxman006/slack2teams-frontend:ai
```

### Step 9: Deploy Services

```bash
# On the server
cd /opt/slack2teams-ai

# Stop any existing services
docker-compose -f docker-compose.ai.yml down

# Start services with environment file
docker-compose -f docker-compose.ai.yml --env-file .env.ai up -d

# Wait for services to start
sleep 30

# Check service status
docker-compose -f docker-compose.ai.yml ps
```

### Step 10: Verify Deployment

```bash
# Check logs
docker logs slack2teams-frontend-ai --tail 50
docker logs slack2teams-backend-ai --tail 50
docker logs slack2teams-nginx-ai --tail 50

# Test backend health
curl http://localhost:8002/health

# Test frontend
curl http://localhost:3000/

# Test through nginx (local)
curl -I http://localhost/

# Test public URL
curl -I https://ai.cloudfuze.com/
```

---

## 🔍 Verification Checklist

### Service Health:
```bash
# All 3 containers should be running and healthy
docker-compose -f docker-compose.ai.yml ps

# Expected output:
# slack2teams-frontend-ai   Up (healthy)
# slack2teams-backend-ai    Up (healthy)
# slack2teams-nginx-ai      Up (healthy)
```

### Endpoint Tests:
```bash
# Backend health
curl https://ai.cloudfuze.com/api/health
# Expected: {"status":"healthy","message":"Server is running"}

# Auth config
curl https://ai.cloudfuze.com/auth/config
# Expected: JSON with Microsoft OAuth configuration

# Frontend
curl -I https://ai.cloudfuze.com/
# Expected: 200 OK with HTML content
```

### Browser Tests:
1. Visit: https://ai.cloudfuze.com/
2. Check if login page loads
3. Test Microsoft OAuth login
4. Test chat functionality

---

## 🔧 Common Issues and Solutions

### Issue 1: Environment Variables Not Loading

**Symptom:** Warning messages about unset variables

**Solution:**
```bash
# Always use --env-file flag
docker-compose -f docker-compose.ai.yml --env-file .env.ai up -d

# Verify env vars are loaded
docker exec slack2teams-backend-ai printenv | grep OPENAI_API_KEY
```

### Issue 2: Frontend Not Accessible

**Symptom:** 502 Bad Gateway or connection refused

**Solution:**
```bash
# Check frontend logs
docker logs slack2teams-frontend-ai

# Restart frontend
docker-compose -f docker-compose.ai.yml restart frontend

# Check frontend health
docker exec slack2teams-frontend-ai wget --no-verbose --tries=1 --spider http://127.0.0.1:3000
```

### Issue 3: SSL Certificate Issues

**Symptom:** Certificate not found or expired

**Solution:**
```bash
# Renew certificate
certbot renew

# Or get new certificate
certbot certonly --standalone -d ai.cloudfuze.com --force-renew

# Restart nginx
docker-compose -f docker-compose.ai.yml restart nginx
```

### Issue 4: Backend Crashes

**Symptom:** Backend container keeps restarting

**Solution:**
```bash
# Check backend logs
docker logs slack2teams-backend-ai --tail 100

# Common causes:
# 1. Invalid API keys - check .env.ai
# 2. MongoDB connection issues - verify MONGODB_URL
# 3. Missing dependencies - rebuild: docker-compose build backend
```

### Issue 5: Port Already in Use

**Symptom:** Cannot start nginx (port 80/443 in use)

**Solution:**
```bash
# Check what's using the ports
netstat -tulpn | grep -E ':80|:443'

# Stop conflicting service
systemctl stop nginx  # if system nginx is running
# OR
docker ps  # find and stop conflicting container
```

---

## 📊 Monitoring and Maintenance

### View Logs:
```bash
# All services
docker-compose -f docker-compose.ai.yml logs -f

# Specific service
docker logs -f slack2teams-frontend-ai
docker logs -f slack2teams-backend-ai
docker logs -f slack2teams-nginx-ai
```

### Check Resource Usage:
```bash
# Container stats
docker stats

# Disk usage
df -h
docker system df
```

### Restart Services:
```bash
# Restart all
docker-compose -f docker-compose.ai.yml restart

# Restart specific service
docker-compose -f docker-compose.ai.yml restart frontend
docker-compose -f docker-compose.ai.yml restart backend
docker-compose -f docker-compose.ai.yml restart nginx
```

### Update Deployment:
```bash
# Pull latest code
cd /opt/slack2teams-ai
git pull origin CF_Chatbot-V1

# Pull latest images
docker-compose -f docker-compose.ai.yml pull

# Restart services
docker-compose -f docker-compose.ai.yml --env-file .env.ai up -d

# OR rebuild backend if code changed
docker-compose -f docker-compose.ai.yml build backend
docker-compose -f docker-compose.ai.yml --env-file .env.ai up -d
```

---

## 🔒 Microsoft App Registration

After deployment, add these redirect URLs to your Microsoft App Registration:

1. Go to Azure Portal → App Registrations
2. Select your app
3. Go to **Authentication** → **Platform configurations** → **Web**
4. Add these Redirect URIs:
   - `https://ai.cloudfuze.com/api/auth/callback`
   - `https://ai.cloudfuze.com/`

5. Save changes

---

## 📞 Support

If you encounter issues:

1. Check logs: `docker-compose -f docker-compose.ai.yml logs`
2. Verify environment variables: `docker exec slack2teams-backend-ai printenv`
3. Check service health: `docker-compose -f docker-compose.ai.yml ps`
4. Test endpoints individually using curl commands above

---

## 📝 Useful Commands Reference

```bash
# SSH to server
ssh root@64.227.160.206

# Navigate to project
cd /opt/slack2teams-ai

# View running containers
docker ps

# Stop all services
docker-compose -f docker-compose.ai.yml down

# Start all services
docker-compose -f docker-compose.ai.yml --env-file .env.ai up -d

# View logs (follow)
docker-compose -f docker-compose.ai.yml logs -f

# Restart a specific service
docker-compose -f docker-compose.ai.yml restart frontend

# Execute command in container
docker exec -it slack2teams-backend-ai bash

# Clean up unused Docker resources
docker system prune -a

# Check certificate expiry
certbot certificates
```

---

## 🎉 Success Criteria

Deployment is successful when:

- ✅ All 3 containers are running and healthy
- ✅ https://ai.cloudfuze.com/ loads the frontend
- ✅ https://ai.cloudfuze.com/api/health returns healthy status
- ✅ Microsoft OAuth login works
- ✅ Chat functionality works
- ✅ No error logs in any container

---

**Deployment Date:** _To be filled after deployment_  
**Deployed By:** _To be filled_  
**Version:** CF_Chatbot-V1

