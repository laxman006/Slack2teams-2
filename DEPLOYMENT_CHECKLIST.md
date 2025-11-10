# Deployment Checklist for ai.cloudfuze.com

## ✅ Completed Pre-Deployment Tasks

### Domain Configuration
- [x] Updated nginx-prod.conf to use `ai.cloudfuze.com`
- [x] Updated SSL certificate paths for `ai.cloudfuze.com`
- [x] Updated index.html API base URL configuration
- [x] Updated deploy-ubuntu.sh deployment script
- [x] Updated restart_services scripts (both .bat and .sh)
- [x] Committed all changes to git

### Branch Status
- [x] Switched to `feature/conversation-relevance-checker` branch
- [x] Branch is up to date with remote
- [x] All changes committed

## 📋 Pre-Deployment Checklist

### DNS Configuration
- [ ] Verify DNS A record for `ai.cloudfuze.com` points to the correct IP address
- [ ] Wait for DNS propagation (can take up to 48 hours, typically 15-30 minutes)
- [ ] Test DNS resolution: `nslookup ai.cloudfuze.com`

### Environment Variables
- [ ] Create/update `.env.prod` file with production values:
  - [ ] OPENAI_API_KEY
  - [ ] MICROSOFT_CLIENT_ID
  - [ ] MICROSOFT_CLIENT_SECRET
  - [ ] MICROSOFT_TENANT
  - [ ] LANGFUSE_PUBLIC_KEY (optional)
  - [ ] LANGFUSE_SECRET_KEY (optional)

### Microsoft OAuth Configuration
- [ ] Update Microsoft App Registration redirect URIs:
  - [ ] Add `https://ai.cloudfuze.com/auth/microsoft/callback`
  - [ ] Add `https://ai.cloudfuze.com/index.html`
  - [ ] Remove old `newcf3.cloudfuze.com` URIs (if any)

### Server Preparation
- [ ] SSH access to production server confirmed
- [ ] Docker and Docker Compose installed on server
- [ ] Sufficient disk space available
- [ ] Firewall rules configured (ports 80, 443, 22)

## 🚀 Deployment Steps

### 1. Pull Latest Code
```bash
cd /opt/slack2teams
git fetch origin
git checkout feature/conversation-relevance-checker
git pull origin feature/conversation-relevance-checker
```

### 2. Update Environment Variables
```bash
nano .env.prod
# Update all required environment variables
```

### 3. Stop Existing Services
```bash
docker-compose -f docker-compose.prod.yml down
```

### 4. Build and Start Services
```bash
docker-compose -f docker-compose.prod.yml --env-file .env.prod up --build -d
```

### 5. Setup SSL Certificate (First time only)
```bash
# Stop nginx temporarily
docker-compose -f docker-compose.prod.yml stop nginx

# Get Let's Encrypt certificate
sudo certbot certonly --standalone -d ai.cloudfuze.com --non-interactive --agree-tos --email admin@cloudfuze.com

# Start nginx with SSL
docker-compose -f docker-compose.prod.yml up -d
```

### 6. Verify Deployment
- [ ] Check service status: `docker-compose -f docker-compose.prod.yml ps`
- [ ] Check logs: `docker-compose -f docker-compose.prod.yml logs -f`
- [ ] Test health endpoint: `curl https://ai.cloudfuze.com/health`
- [ ] Test login page: `https://ai.cloudfuze.com/login.html`
- [ ] Test chat functionality: `https://ai.cloudfuze.com/`

## 🔍 Post-Deployment Verification

### Functional Testing
- [ ] Login with Microsoft account works
- [ ] Chat interface loads properly
- [ ] Chat responses are generated correctly
- [ ] Feedback buttons work
- [ ] Copy message functionality works
- [ ] New chat functionality works
- [ ] Chat history persists across sessions

### Security Checks
- [ ] HTTPS is working (valid SSL certificate)
- [ ] HTTP redirects to HTTPS
- [ ] Only CloudFuze email domains can access
- [ ] Authentication tokens are validated
- [ ] CORS settings are correct

### Performance Checks
- [ ] Page load time is acceptable
- [ ] Chat response time is reasonable
- [ ] No console errors in browser
- [ ] No errors in server logs

## 🔧 Monitoring Setup

### Logs
```bash
# View real-time logs
docker-compose -f docker-compose.prod.yml logs -f

# View backend logs only
docker-compose -f docker-compose.prod.yml logs -f backend

# View nginx logs only
docker-compose -f docker-compose.prod.yml logs -f nginx
```

### Health Checks
- Backend health: `https://ai.cloudfuze.com/health`
- API docs: `https://ai.cloudfuze.com/api/docs`

## 🆘 Rollback Plan

If deployment fails:
```bash
# Stop current deployment
docker-compose -f docker-compose.prod.yml down

# Switch to previous stable branch
git checkout main  # or previous stable branch

# Rebuild and restart
docker-compose -f docker-compose.prod.yml --env-file .env.prod up --build -d
```

## 📝 Additional Notes

### Key Changes in This Deployment
- Domain changed from `newcf3.cloudfuze.com` to `ai.cloudfuze.com`
- Using `feature/conversation-relevance-checker` branch
- Conversation relevance checker feature included

### Important Files
- Nginx config: `nginx-prod.conf`
- Docker config: `docker-compose.prod.yml`
- Environment: `.env.prod`
- Frontend: `index.html`
- Deployment script: `deploy-ubuntu.sh`

### Support Contacts
- DevOps: [Add contact]
- Backend Dev: [Add contact]
- Product Owner: [Add contact]

---

**Deployment Date:** _____________________
**Deployed By:** _____________________
**Sign-off:** _____________________

