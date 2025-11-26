# 🚀 AI.CloudFuze.com Deployment - Ready to Deploy!

## ✅ What's Been Prepared

I've created a **complete deployment setup** for deploying your CF_Chatbot-V1 branch to **ai.cloudfuze.com** (64.227.160.206) with full frontend and backend support.

### 📦 New Files Created:

1. **nginx-ai.conf** - Nginx configuration for ai.cloudfuze.com with frontend routing
2. **docker-compose.ai.yml** - Docker Compose configuration for ai.cloudfuze.com
3. **deploy-ai.sh** - Automated deployment script
4. **DEPLOYMENT-AI-GUIDE.md** - Complete step-by-step deployment guide
5. **DEPLOY-AI-COMMANDS.md** - Quick reference commands
6. **README-AI-DEPLOYMENT.md** - This file!

### 🔄 Updated Files:

- **docker-compose.prod.yml** - Fixed nginx config reference and added networking

---

## 🎯 Quick Start - 3 Options

### Option 1: Automated Script (Recommended) ⚡

```bash
# 1. Commit and push changes
git add .
git commit -m "feat: add ai.cloudfuze.com deployment configuration"
git push origin CF_Chatbot-V1

# 2. Build and push frontend
cd frontend
docker build -f Dockerfile.frontend -t laxman006/slack2teams-frontend:ai \
  --build-arg NEXT_PUBLIC_API_URL=https://ai.cloudfuze.com .
docker push laxman006/slack2teams-frontend:ai
cd ..

# 3. Run automated deployment
chmod +x deploy-ai.sh
./deploy-ai.sh
```

### Option 2: Manual Deployment (Step-by-Step) 📝

Follow the detailed guide in **DEPLOYMENT-AI-GUIDE.md**

### Option 3: Quick Commands 🔥

Use the command reference in **DEPLOY-AI-COMMANDS.md**

---

## 📋 Pre-Deployment Checklist

Before deploying, ensure you have:

- [ ] Git repository access
- [ ] Docker Hub credentials (laxman006)
- [ ] SSH access to server (root@64.227.160.206)
- [ ] API Keys ready:
  - OpenAI API Key
  - Microsoft OAuth (Client ID, Secret, Tenant)
  - Langfuse Keys
  - MongoDB Connection String
- [ ] Domain DNS pointing to 64.227.160.206

---

## 🚀 Deployment Steps Overview

### Step 1: Local Preparation
```bash
# Commit changes
git add nginx-ai.conf docker-compose.ai.yml deploy-ai.sh *.md docker-compose.prod.yml
git commit -m "feat: add ai.cloudfuze.com deployment with frontend"
git push origin CF_Chatbot-V1
```

### Step 2: Build Frontend Image
```bash
cd frontend
docker build -f Dockerfile.frontend -t laxman006/slack2teams-frontend:ai \
  --build-arg NEXT_PUBLIC_API_URL=https://ai.cloudfuze.com .
docker push laxman006/slack2teams-frontend:ai
cd ..
```

### Step 3: Server Setup
```bash
ssh root@64.227.160.206
mkdir -p /opt/slack2teams-ai
cd /opt/slack2teams-ai
git clone -b CF_Chatbot-V1 https://github.com/laxman006/chatbot.git .
```

### Step 4: Configure Environment
```bash
# Create .env.ai file with your API keys
nano /opt/slack2teams-ai/.env.ai
```

### Step 5: Setup SSL
```bash
certbot certonly --standalone -d ai.cloudfuze.com \
  --agree-tos --non-interactive --email admin@cloudfuze.com
```

### Step 6: Deploy
```bash
cd /opt/slack2teams-ai
docker pull laxman006/slack2teams-frontend:ai
docker-compose -f docker-compose.ai.yml --env-file .env.ai up -d
```

### Step 7: Verify
```bash
# Check status
docker-compose -f docker-compose.ai.yml ps

# Test endpoints
curl https://ai.cloudfuze.com/api/health
curl -I https://ai.cloudfuze.com/
```

---

## 🔍 What Gets Deployed

### Services:
1. **Frontend** (Next.js)
   - Container: `slack2teams-frontend-ai`
   - Port: 3000 (internal)
   - Image: `laxman006/slack2teams-frontend:ai`
   - API URL: `https://ai.cloudfuze.com`

2. **Backend** (FastAPI)
   - Container: `slack2teams-backend-ai`
   - Port: 8002 (internal)
   - Built from: `Dockerfile.prod`

3. **Nginx** (Reverse Proxy)
   - Container: `slack2teams-nginx-ai`
   - Ports: 80, 443
   - Config: `nginx-ai.conf`
   - SSL: `/etc/letsencrypt/live/ai.cloudfuze.com/`

### Network Architecture:
```
Internet (HTTPS/443)
    ↓
Nginx Reverse Proxy
    ↓
    ├─→ / → Next.js Frontend (port 3000)
    ├─→ /api/ → FastAPI Backend (port 8002)
    ├─→ /chat/ → FastAPI Backend (port 8002)
    └─→ /auth/ → FastAPI Backend (port 8002)
```

---

## 📊 Post-Deployment Tasks

### 1. Test All Endpoints
```bash
# Frontend
curl -I https://ai.cloudfuze.com/

# Backend Health
curl https://ai.cloudfuze.com/api/health

# Auth Config
curl https://ai.cloudfuze.com/auth/config
```

### 2. Update Microsoft App Registration
Add these redirect URLs:
- `https://ai.cloudfuze.com/api/auth/callback`
- `https://ai.cloudfuze.com/`

### 3. Test in Browser
1. Visit https://ai.cloudfuze.com/
2. Test Microsoft Login
3. Test Chat functionality

### 4. Monitor Logs
```bash
docker-compose -f docker-compose.ai.yml logs -f
```

---

## 🆘 Troubleshooting

### Common Issues:

**Environment Variables Not Loading:**
```bash
# Always use --env-file flag
docker-compose -f docker-compose.ai.yml --env-file .env.ai up -d
```

**Frontend 502 Error:**
```bash
# Check frontend logs
docker logs slack2teams-frontend-ai
# Restart frontend
docker-compose -f docker-compose.ai.yml restart frontend
```

**Backend Crash:**
```bash
# Check logs for errors
docker logs slack2teams-backend-ai --tail 100
# Verify env vars
docker exec slack2teams-backend-ai printenv | grep OPENAI
```

**SSL Certificate Issues:**
```bash
# Renew certificate
certbot renew
# Restart nginx
docker-compose -f docker-compose.ai.yml restart nginx
```

---

## 📞 Need Help?

1. **Full Guide**: See `DEPLOYMENT-AI-GUIDE.md`
2. **Commands**: See `DEPLOY-AI-COMMANDS.md`
3. **Check Logs**: `docker-compose -f docker-compose.ai.yml logs -f`
4. **Health Check**: `curl https://ai.cloudfuze.com/api/health`

---

## 🎉 Success Indicators

Deployment is successful when:

✅ All 3 containers show (healthy) status  
✅ `https://ai.cloudfuze.com/` loads the login page  
✅ `https://ai.cloudfuze.com/api/health` returns `{"status":"healthy"}`  
✅ Microsoft OAuth login works  
✅ Chat interface is accessible and functional  

---

## 📝 Environment Variables Required

Create `.env.ai` on the server with these variables:

```env
# Required
OPENAI_API_KEY=sk-proj-...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
MICROSOFT_TENANT=cloudfuze.com
MONGODB_URL=mongodb+srv://...
MONGODB_DATABASE=slack2teams
MONGODB_CHAT_COLLECTION=chat_histories

# Optional but Recommended
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# Feature Flags
ENABLE_WEB_SOURCE=true
ENABLE_SHAREPOINT_SOURCE=true
ENABLE_OUTLOOK_SOURCE=true

# See .env.ai.template for complete list
```

---

## 🔄 Update Procedure

To update the deployment:

```bash
# On server
cd /opt/slack2teams-ai
git pull origin CF_Chatbot-V1
docker-compose -f docker-compose.ai.yml pull
docker-compose -f docker-compose.ai.yml --env-file .env.ai up -d
```

---

## 📚 Documentation Files

- **README-AI-DEPLOYMENT.md** (this file) - Overview and quick start
- **DEPLOYMENT-AI-GUIDE.md** - Comprehensive step-by-step guide
- **DEPLOY-AI-COMMANDS.md** - Quick reference commands
- **deploy-ai.sh** - Automated deployment script

---

## 🎯 Next Steps

1. ⬜ Commit and push the new deployment files
2. ⬜ Build and push frontend Docker image
3. ⬜ SSH to server and create project directory
4. ⬜ Create .env.ai file with API keys
5. ⬜ Setup SSL certificate
6. ⬜ Deploy services
7. ⬜ Verify deployment
8. ⬜ Update Microsoft App Registration
9. ⬜ Test in browser

**Ready to deploy? Start with Step 1 above!** 🚀

---

**Prepared for:** ai.cloudfuze.com (64.227.160.206)  
**Branch:** CF_Chatbot-V1  
**Date:** November 26, 2025

