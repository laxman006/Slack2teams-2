# Next.js Frontend Deployment Guide

Complete guide to deploy the Next.js frontend with Docker on `newcf3.cloudfuze.com`

## 📋 Overview

This deployment includes:
- **Frontend**: Next.js (React) running on port 3000
- **Backend**: FastAPI (Python) running on port 8002
- **Nginx**: Reverse proxy on ports 80/443
- **Docker Compose**: Orchestrating all services

## 🚀 Quick Start (On Server)

### 1. Push Changes from Local to GitHub

```powershell
# On your LOCAL machine (Windows)
cd C:\Users\LaxmanKadari\Desktop\v1-dev\chatbot

# Add all changes
git add .

# Commit changes
git commit -m "Add Next.js frontend Docker deployment"

# Push to CF_Chatbot-V1 branch
git push origin CF_Chatbot-V1
```

### 2. Pull Changes on Server

```bash
# SSH into server
ssh root@139.59.12.244

# Navigate to deployment directory
cd /opt/slack2teams-newcf3

# Pull latest changes
git pull origin CF_Chatbot-V1

# Verify new files exist
ls -la frontend/Dockerfile.frontend
ls -la deploy-with-frontend.sh
```

### 3. Deploy Everything

```bash
# Make deployment script executable
chmod +x deploy-with-frontend.sh

# Run deployment
./deploy-with-frontend.sh
```

## 📁 File Structure

```
/opt/slack2teams-newcf3/
├── frontend/
│   ├── Dockerfile.frontend          # ✅ NEW - Frontend Docker config
│   ├── .env.production              # ✅ Created by script
│   ├── next.config.js               # ✅ Updated for standalone
│   ├── src/
│   ├── public/
│   └── package.json
├── docker-compose.prod.yml          # ✅ Updated with frontend service
├── nginx-newcf3.conf                # ✅ Updated to proxy to frontend
├── .env.prod                        # ✅ Backend environment variables
├── Dockerfile.prod                  # Backend Dockerfile
└── deploy-with-frontend.sh          # ✅ NEW - Complete deployment script
```

## 🔧 What Changed

### 1. Frontend Dockerfile (`frontend/Dockerfile.frontend`)
- Multi-stage build (builder + runner)
- Uses Node.js 20 Alpine
- Builds Next.js in standalone mode
- Production-optimized (~100MB image)

### 2. Next.js Config (`frontend/next.config.js`)
- Added `output: 'standalone'` for Docker optimization
- Enables standalone server.js generation

### 3. Docker Compose (`docker-compose.prod.yml`)
- Added `frontend` service
- Frontend depends on backend
- Nginx depends on frontend + backend
- Environment variable: `NEXT_PUBLIC_API_URL`

### 4. Nginx Config (`nginx-newcf3.conf`)
- Proxies `/` to frontend:3000
- Proxies `/api/` to backend:8002
- Proxies `/chat/` to backend:8002
- Proxies `/auth/` to backend:8002
- Serves `/images/` statically

## 🌐 Request Flow

```
User Browser
    ↓
HTTPS (443) → Nginx
    ↓
    ├─→ / (Frontend) → Next.js Container (port 3000)
    ├─→ /api/* → Backend Container (port 8002)
    ├─→ /chat/* → Backend Container (port 8002)
    └─→ /auth/* → Backend Container (port 8002)
```

## 📊 Service Details

### Frontend Service
- **Container**: `slack2teams-frontend-prod`
- **Port**: 3000 (internal)
- **Build Time**: ~5-8 minutes
- **Image Size**: ~100MB
- **Technology**: Next.js 16, React 19

### Backend Service
- **Container**: `slack2teams-backend-prod`
- **Port**: 8002 (internal)
- **Build Time**: ~3-5 minutes
- **Image Size**: ~500MB
- **Technology**: Python 3.12, FastAPI

### Nginx Service
- **Container**: `slack2teams-nginx-prod`
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Role**: Reverse proxy + SSL termination

## 🔍 Verification Commands

### Check All Services
```bash
docker-compose -f docker-compose.prod.yml ps
```

Expected output:
```
NAME                          STATUS
slack2teams-frontend-prod     Up (healthy)
slack2teams-backend-prod      Up (healthy)
slack2teams-nginx-prod        Up (healthy)
```

### Check Frontend Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Check Backend Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f backend
```

### Test Frontend Directly
```bash
curl http://localhost:3000
```

### Test Backend Directly
```bash
curl http://localhost:8002/health
```

### Test Through Nginx
```bash
curl http://localhost/
curl http://localhost:8002/health
```

## 🐛 Troubleshooting

### Issue 1: Frontend Won't Start

**Symptoms:**
- Container exits immediately
- Logs show "Cannot find module 'server.js'"

**Solution:**
```bash
# Rebuild with no cache
docker-compose -f docker-compose.prod.yml build --no-cache frontend
docker-compose -f docker-compose.prod.yml up -d frontend
```

### Issue 2: Frontend Shows 502 Bad Gateway

**Symptoms:**
- Nginx returns 502 error
- Frontend container is running

**Solution:**
```bash
# Check frontend is actually listening on port 3000
docker exec slack2teams-frontend-prod netstat -tuln | grep 3000

# Check nginx can reach frontend
docker exec slack2teams-nginx-prod ping frontend

# Restart frontend
docker-compose -f docker-compose.prod.yml restart frontend
```

### Issue 3: API Calls Fail from Frontend

**Symptoms:**
- Frontend loads but API calls return 404 or CORS errors

**Solution:**
```bash
# Check NEXT_PUBLIC_API_URL is set correctly
docker exec slack2teams-frontend-prod env | grep NEXT_PUBLIC

# Should show: NEXT_PUBLIC_API_URL=https://newcf3.cloudfuze.com

# If wrong, rebuild frontend:
docker-compose -f docker-compose.prod.yml build frontend
docker-compose -f docker-compose.prod.yml up -d frontend
```

### Issue 4: Static Assets Not Loading

**Symptoms:**
- Page loads but images, CSS missing
- Console shows 404 for `/_next/static/*`

**Solution:**
```bash
# Check nginx is proxying _next correctly
docker-compose -f docker-compose.prod.yml logs nginx | grep "_next"

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

## 🔄 Update/Redeploy Workflow

### Code Changes in Frontend
```bash
cd /opt/slack2teams-newcf3

# Pull latest code
git pull origin CF_Chatbot-V1

# Rebuild only frontend
docker-compose -f docker-compose.prod.yml build frontend
docker-compose -f docker-compose.prod.yml up -d frontend

# Check logs
docker-compose -f docker-compose.prod.yml logs -f frontend
```

### Code Changes in Backend
```bash
# Pull latest code
git pull origin CF_Chatbot-V1

# Rebuild only backend
docker-compose -f docker-compose.prod.yml build backend
docker-compose -f docker-compose.prod.yml up -d backend
```

### Config Changes (nginx, .env)
```bash
# Pull latest code
git pull origin CF_Chatbot-V1

# Restart affected service
docker-compose -f docker-compose.prod.yml restart nginx
# OR
docker-compose -f docker-compose.prod.yml restart backend
```

### Complete Rebuild (All Services)
```bash
# Pull latest
git pull origin CF_Chatbot-V1

# Stop everything
docker-compose -f docker-compose.prod.yml down

# Rebuild everything
docker-compose -f docker-compose.prod.yml up --build -d

# Monitor logs
docker-compose -f docker-compose.prod.yml logs -f
```

## 📈 Performance Optimization

### Frontend Build Optimization
- Uses standalone output (~50% smaller than default)
- Multi-stage build (build artifacts not in final image)
- Node modules optimized with `npm ci --only=production`

### Nginx Caching
- Static assets cached for 1 year
- `_next/static` cached for 1 year
- Dynamic content not cached

### Container Resources
Current: Using default Docker resources

To limit (add to docker-compose.prod.yml):
```yaml
frontend:
  deploy:
    resources:
      limits:
        cpus: '1.0'
        memory: 512M
      reservations:
        cpus: '0.5'
        memory: 256M
```

## 🔐 Environment Variables

### Frontend (.env.production)
```bash
NEXT_PUBLIC_API_URL=https://newcf3.cloudfuze.com
```

### Backend (.env.prod)
```bash
OPENAI_API_KEY=...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
# ... (all other backend vars)
```

## 📝 Notes

1. **First deployment takes longer** (~10-15 minutes) due to:
   - NPM package installation
   - Next.js build
   - Python package installation
   - Image layers download

2. **Subsequent deployments are faster** (~2-3 minutes) due to:
   - Docker layer caching
   - Cached dependencies

3. **Frontend builds at deploy time**, not at image build time
   - This allows environment variables to be injected
   - `NEXT_PUBLIC_*` vars are embedded in the JS bundle

4. **Production mode** means:
   - No hot reload
   - Optimized bundles
   - Compressed assets
   - No source maps (unless configured)

## ✅ Success Checklist

- [ ] All 3 containers running and healthy
- [ ] Frontend accessible at `https://newcf3.cloudfuze.com`
- [ ] Login page loads correctly
- [ ] Can login with Microsoft account
- [ ] Chat interface loads after login
- [ ] Can send messages and receive responses
- [ ] Images and styles load correctly
- [ ] No console errors in browser
- [ ] Backend `/health` endpoint responds
- [ ] SSL certificate valid

## 🆘 Emergency Rollback

If deployment fails completely:

```bash
# Stop everything
docker-compose -f docker-compose.prod.yml down

# Use static HTML fallback (remove frontend service temporarily)
# Edit docker-compose.prod.yml and comment out frontend service

# Update nginx to serve static files
cp nginx-prod.conf.backup nginx-prod.conf  # If you have a backup

# Restart with just backend + nginx
docker-compose -f docker-compose.prod.yml up -d nginx backend
```

## 📧 Support

If you encounter issues not covered here:
1. Check all service logs
2. Verify environment variables
3. Check Docker/system resources
4. Review nginx error logs
5. Test components individually

---

**Deployment Date**: November 24, 2025  
**Version**: Next.js Frontend with Docker  
**Environment**: newcf3.cloudfuze.com (Development)

