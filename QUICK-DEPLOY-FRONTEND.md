# 🚀 Quick Deploy Commands - Next.js Frontend

## Step-by-Step Commands to Run on Server

### 1️⃣ Push Changes from Local (Windows)

```powershell
# Run on your LOCAL machine
cd C:\Users\LaxmanKadari\Desktop\v1-dev\chatbot

git add .
git commit -m "Add Next.js frontend deployment"
git push origin CF_Chatbot-V1
```

### 2️⃣ SSH into Server

```bash
ssh root@139.59.12.244
```

### 3️⃣ Navigate to Deployment Directory

```bash
cd /opt/slack2teams-newcf3
```

### 4️⃣ Pull Latest Code

```bash
git pull origin CF_Chatbot-V1
```

### 5️⃣ Verify New Files

```bash
# Check these files exist:
ls -la frontend/Dockerfile.frontend
ls -la deploy-with-frontend.sh
ls -la FRONTEND-DEPLOYMENT-GUIDE.md
```

### 6️⃣ Make Deployment Script Executable

```bash
chmod +x deploy-with-frontend.sh
```

### 7️⃣ Run Complete Deployment

```bash
./deploy-with-frontend.sh
```

This will:
- ✅ Stop existing containers
- ✅ Build frontend Docker image (~5-8 min)
- ✅ Build backend Docker image (~3-5 min)
- ✅ Start all services (frontend, backend, nginx)
- ✅ Run health checks
- ✅ Show service status

### 8️⃣ Monitor Deployment

```bash
# Watch all logs in real-time
docker-compose -f docker-compose.prod.yml logs -f

# Or watch specific services:
docker-compose -f docker-compose.prod.yml logs -f frontend
docker-compose -f docker-compose.prod.yml logs -f backend
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### 9️⃣ Verify Services are Running

```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Expected output:
# slack2teams-frontend-prod    Up (healthy)
# slack2teams-backend-prod     Up (healthy)
# slack2teams-nginx-prod       Up (healthy)
```

### 🔟 Test the Application

```bash
# Test frontend directly
curl http://localhost:3000

# Test backend health
curl http://localhost:8002/health

# Test through nginx
curl http://localhost/

# Test from outside
curl https://newcf3.cloudfuze.com/
```

---

## 📊 Quick Status Check

```bash
# One-liner to check everything
docker ps --filter "name=slack2teams" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
```

---

## 🔧 Quick Fixes

### If frontend fails to build:
```bash
docker-compose -f docker-compose.prod.yml build --no-cache frontend
docker-compose -f docker-compose.prod.yml up -d frontend
```

### If backend fails:
```bash
docker-compose -f docker-compose.prod.yml logs backend
docker-compose -f docker-compose.prod.yml restart backend
```

### If nginx shows errors:
```bash
docker-compose -f docker-compose.prod.yml logs nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Complete restart:
```bash
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

---

## 🎯 Success Indicators

✅ **All services healthy**:
```bash
docker-compose -f docker-compose.prod.yml ps
# All show "Up (healthy)"
```

✅ **Frontend responding**:
```bash
curl -I http://localhost:3000
# HTTP/1.1 200 OK
```

✅ **Backend responding**:
```bash
curl http://localhost:8002/health
# {"status":"healthy"}
```

✅ **Nginx proxying correctly**:
```bash
curl -I https://newcf3.cloudfuze.com/
# HTTP/1.1 200 OK
```

✅ **Can access login page**:
Open browser: `https://newcf3.cloudfuze.com/login`

---

## ⏱️ Expected Timeline

1. **Pull code**: 10 seconds
2. **Frontend build**: 5-8 minutes (first time)
3. **Backend build**: 3-5 minutes (first time)
4. **Services start**: 30-60 seconds
5. **Health checks**: 30 seconds

**Total first deployment**: ~10-15 minutes
**Subsequent deployments**: ~2-3 minutes (cached)

---

## 🆘 Emergency Commands

### View live logs:
```bash
docker-compose -f docker-compose.prod.yml logs -f --tail=100
```

### Stop everything:
```bash
docker-compose -f docker-compose.prod.yml down
```

### Remove all containers and rebuild:
```bash
docker-compose -f docker-compose.prod.yml down
docker system prune -f
docker-compose -f docker-compose.prod.yml up --build -d
```

### Check disk space:
```bash
df -h
docker system df
```

---

## 📞 What to Check if Something Fails

1. **Check logs**: `docker-compose -f docker-compose.prod.yml logs [service-name]`
2. **Check status**: `docker-compose -f docker-compose.prod.yml ps`
3. **Check .env.prod exists**: `ls -la .env.prod`
4. **Check disk space**: `df -h`
5. **Check memory**: `free -h`
6. **Check Docker**: `docker info`

---

**Remember**: The deployment script (`deploy-with-frontend.sh`) does everything automatically! 🎉

