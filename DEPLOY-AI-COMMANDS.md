# Quick Deployment Commands for ai.cloudfuze.com

## 📝 Pre-Deployment (Local Machine)

### 1. Commit Current Changes
```bash
# Check status
git status

# Add all new files
git add nginx-ai.conf docker-compose.ai.yml deploy-ai.sh DEPLOYMENT-AI-GUIDE.md DEPLOY-AI-COMMANDS.md docker-compose.prod.yml

# Commit
git commit -m "feat: add deployment configuration for ai.cloudfuze.com with frontend support"

# Push to repository
git push origin CF_Chatbot-V1
```

### 2. Build and Push Frontend Image
```bash
# Navigate to frontend
cd frontend

# Build with correct API URL
docker build -f Dockerfile.frontend -t laxman006/slack2teams-frontend:ai \
  --build-arg NEXT_PUBLIC_API_URL=https://ai.cloudfuze.com .

# Login to Docker Hub (if not already logged in)
docker login

# Push image
docker push laxman006/slack2teams-frontend:ai

# Return to root
cd ..
```

---

## 🚀 Server Deployment Commands

### SSH to Server
```bash
ssh root@64.227.160.206
```

### Complete Server Setup (Run All)
```bash
# Stop old services
cd /opt/slack2teams 2>/dev/null && docker-compose down || true
cd /opt/slack2teams-prod 2>/dev/null && docker-compose down || true

# Create and navigate to project directory
mkdir -p /opt/slack2teams-ai
cd /opt/slack2teams-ai

# Update system and install dependencies
apt-get update
apt-get install -y docker.io docker-compose git curl certbot python3-certbot-nginx

# Start Docker
systemctl start docker
systemctl enable docker

# Clone repository
git clone -b CF_Chatbot-V1 https://github.com/laxman006/chatbot.git .

# Pull latest changes
git pull origin CF_Chatbot-V1

# Create .env.ai file (use nano or vi)
nano .env.ai
# Paste your environment variables here, then save (Ctrl+X, Y, Enter)

# Get SSL certificate
certbot certonly --standalone -d ai.cloudfuze.com \
  --agree-tos --non-interactive --email admin@cloudfuze.com

# Pull frontend image
docker pull laxman006/slack2teams-frontend:ai

# Deploy services
docker-compose -f docker-compose.ai.yml --env-file .env.ai up -d

# Wait for services to start
sleep 30

# Check status
docker-compose -f docker-compose.ai.yml ps
```

---

## 🔍 Verification Commands

```bash
# Check all container status
docker-compose -f docker-compose.ai.yml ps

# Check logs
docker logs slack2teams-frontend-ai --tail 50
docker logs slack2teams-backend-ai --tail 50
docker logs slack2teams-nginx-ai --tail 20

# Test backend locally
curl http://localhost:8002/health

# Test frontend locally
curl http://localhost:3000/

# Test nginx locally
curl -I http://localhost/

# Test public URL
curl -I https://ai.cloudfuze.com/
curl https://ai.cloudfuze.com/api/health
```

---

## 🔧 Common Management Commands

### Restart Services
```bash
cd /opt/slack2teams-ai

# Restart all
docker-compose -f docker-compose.ai.yml restart

# Restart specific service
docker-compose -f docker-compose.ai.yml restart frontend
docker-compose -f docker-compose.ai.yml restart backend
docker-compose -f docker-compose.ai.yml restart nginx
```

### View Logs
```bash
# All services (follow)
docker-compose -f docker-compose.ai.yml logs -f

# Specific service (follow)
docker logs -f slack2teams-frontend-ai
docker logs -f slack2teams-backend-ai

# Last N lines
docker logs slack2teams-backend-ai --tail 100
```

### Update Deployment
```bash
cd /opt/slack2teams-ai

# Pull latest code
git pull origin CF_Chatbot-V1

# Pull latest images
docker-compose -f docker-compose.ai.yml pull

# Restart with new code/images
docker-compose -f docker-compose.ai.yml --env-file .env.ai up -d

# If backend code changed, rebuild:
docker-compose -f docker-compose.ai.yml build backend
docker-compose -f docker-compose.ai.yml --env-file .env.ai up -d
```

### Stop Services
```bash
cd /opt/slack2teams-ai
docker-compose -f docker-compose.ai.yml down
```

### Clean Docker Resources
```bash
# Remove stopped containers, unused networks, dangling images
docker system prune

# Remove everything including volumes (BE CAREFUL!)
docker system prune -a --volumes
```

---

## 📊 Monitoring Commands

```bash
# Real-time container stats
docker stats

# Check disk usage
df -h
docker system df

# Check memory
free -h

# Check running processes
docker-compose -f docker-compose.ai.yml top

# Check environment variables in container
docker exec slack2teams-backend-ai printenv | grep -E "OPENAI|MICROSOFT"
```

---

## 🔒 SSL Certificate Management

```bash
# Check certificate status
certbot certificates

# Renew certificate
certbot renew

# Force renew
certbot renew --force-renewal

# After renewal, restart nginx
docker-compose -f docker-compose.ai.yml restart nginx
```

---

## 🐛 Troubleshooting Commands

### Check Service Health
```bash
# Enter container
docker exec -it slack2teams-backend-ai bash

# Check if service is responding
docker exec slack2teams-backend-ai curl http://localhost:8002/health
docker exec slack2teams-frontend-ai wget --spider http://127.0.0.1:3000
```

### Check Network
```bash
# List networks
docker network ls

# Inspect network
docker network inspect slack2teams-ai_app-network

# Check if containers can communicate
docker exec slack2teams-nginx-ai ping frontend
docker exec slack2teams-nginx-ai curl http://backend:8002/health
```

### Check Ports
```bash
# Check what's listening on ports
netstat -tulpn | grep -E ':80|:443|:3000|:8002'

# Check if port is accessible externally
curl -I http://64.227.160.206/
curl -I https://ai.cloudfuze.com/
```

---

## 🔄 Full Reset and Redeploy

```bash
# Stop and remove everything
cd /opt/slack2teams-ai
docker-compose -f docker-compose.ai.yml down -v

# Pull latest code
git pull origin CF_Chatbot-V1

# Pull latest images
docker pull laxman006/slack2teams-frontend:ai
docker-compose -f docker-compose.ai.yml pull

# Rebuild backend (if needed)
docker-compose -f docker-compose.ai.yml build backend --no-cache

# Start fresh
docker-compose -f docker-compose.ai.yml --env-file .env.ai up -d

# Monitor startup
docker-compose -f docker-compose.ai.yml logs -f
```

---

## 📱 Quick Health Check Script

Save this as `health-check.sh` on the server:

```bash
#!/bin/bash
echo "=== Container Status ==="
docker-compose -f /opt/slack2teams-ai/docker-compose.ai.yml ps

echo -e "\n=== Backend Health ==="
curl -s http://localhost:8002/health | jq . || curl -s http://localhost:8002/health

echo -e "\n=== Frontend Status ==="
docker logs slack2teams-frontend-ai --tail 3 2>&1 | grep -E "Ready|Local|Network"

echo -e "\n=== Public URL Test ==="
curl -I https://ai.cloudfuze.com/ 2>&1 | grep -E "HTTP|200|301|302"

echo -e "\n=== API Health ==="
curl -s https://ai.cloudfuze.com/api/health

echo -e "\n=== Auth Config ==="
curl -s https://ai.cloudfuze.com/auth/config | jq .client_id || echo "Auth endpoint not responding"
```

Make it executable and run:
```bash
chmod +x health-check.sh
./health-check.sh
```

---

## 🎯 One-Line Commands

```bash
# Quick restart
cd /opt/slack2teams-ai && docker-compose -f docker-compose.ai.yml restart && sleep 10 && docker-compose -f docker-compose.ai.yml ps

# Quick status check
docker-compose -f /opt/slack2teams-ai/docker-compose.ai.yml ps && curl -s http://localhost:8002/health

# View all logs
docker-compose -f /opt/slack2teams-ai/docker-compose.ai.yml logs --tail 20

# Quick redeploy
cd /opt/slack2teams-ai && git pull && docker-compose -f docker-compose.ai.yml pull && docker-compose -f docker-compose.ai.yml --env-file .env.ai up -d
```

---

## 📞 Emergency Commands

### Service Won't Start
```bash
# Check detailed logs
docker-compose -f docker-compose.ai.yml logs backend | tail -100

# Try starting in foreground to see errors
docker-compose -f docker-compose.ai.yml up backend

# Check if .env.ai exists and is readable
cat .env.ai | head -5
```

### Out of Memory
```bash
# Check memory
free -h

# Check which container is using most memory
docker stats --no-stream

# Restart specific container
docker-compose -f docker-compose.ai.yml restart backend
```

### Port Conflicts
```bash
# Find what's using port 80/443
netstat -tulpn | grep ':80'
lsof -i :80

# Stop conflicting service
systemctl stop nginx  # if system nginx
docker stop <conflicting-container-id>
```

---

**Quick Reference Card:**
- Project Dir: `/opt/slack2teams-ai`
- Compose File: `docker-compose.ai.yml`
- Env File: `.env.ai`
- Frontend Image: `laxman006/slack2teams-frontend:ai`
- Domain: `https://ai.cloudfuze.com`
- Server: `root@64.227.160.206`

