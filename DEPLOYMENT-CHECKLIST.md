# 🚀 Production Deployment Checklist for newcf3.cloudfuze.com

**Server:** newcf3.cloudfuze.com  
**IP Address:** 64.227.160.206  
**Last Updated:** 2025-01-29

---

## 📋 Pre-Deployment Checklist

### 1. DNS Configuration
- [ ] Verify `newcf3.cloudfuze.com` points to `64.227.160.206`
- [ ] Confirm DNS propagation is complete (use `nslookup` or `dig`)
- [ ] Ensure A record is configured correctly

### 2. Server Requirements
- [ ] Ubuntu 20.04+ or similar Linux distribution
- [ ] Minimum 2GB RAM
- [ ] Minimum 20GB disk space
- [ ] SSH access configured
- [ ] Sudo privileges available

### 3. MongoDB Setup
- [ ] MongoDB installed and running (local or remote)
- [ ] MongoDB accessible from the application
- [ ] Database: `slack2teams` created
- [ ] Collections ready:
  - `chat_histories`
  - `cloudfuze_vectorstore` (with 1511 documents)
- [ ] MongoDB connection string available

### 4. Environment Variables Preparation

Gather the following credentials before deployment:

#### Required Keys:
- [ ] `OPENAI_API_KEY` - OpenAI API key for GPT-4o-mini
- [ ] `MICROSOFT_CLIENT_ID` - Azure AD App Registration Client ID
- [ ] `MICROSOFT_CLIENT_SECRET` - Azure AD App Secret
- [ ] `MICROSOFT_TENANT` - Tenant (e.g., `cloudfuze.com`)
- [ ] `LANGFUSE_PUBLIC_KEY` - Langfuse public key for observability
- [ ] `LANGFUSE_SECRET_KEY` - Langfuse secret key

#### MongoDB Configuration:
- [ ] `MONGODB_URL` - MongoDB connection string (default: `mongodb://localhost:27017`)
- [ ] `MONGODB_DATABASE` - Database name (default: `slack2teams`)

### 5. Microsoft Azure AD Configuration
- [ ] App Registration created in Azure Portal
- [ ] Redirect URI configured: `https://newcf3.cloudfuze.com/auth/microsoft/callback`
- [ ] API permissions granted:
  - `User.Read`
  - `openid`
  - `profile`
  - `email`
- [ ] Certificates & secrets created
- [ ] Supported account types configured

### 6. SSL Certificate
- [ ] Email for Let's Encrypt: `admin@cloudfuze.com`
- [ ] Port 80 and 443 accessible
- [ ] DNS validation ready

---

## 🔧 Deployment Steps

### Step 1: Connect to Server
```bash
ssh user@64.227.160.206
# or
ssh user@newcf3.cloudfuze.com
```

### Step 2: Clone Repository
```bash
git clone <your-repo-url> /opt/slack2teams
cd /opt/slack2teams
```

### Step 3: Make Deployment Script Executable
```bash
chmod +x deploy-ubuntu.sh
```

### Step 4: Run Deployment Script
```bash
./deploy-ubuntu.sh
```

The script will automatically:
- ✅ Install Docker and Docker Compose
- ✅ Install Certbot for SSL
- ✅ Create necessary directories
- ✅ Setup environment file template
- ✅ Configure firewall
- ✅ Setup systemd service for auto-start
- ✅ Request SSL certificate
- ✅ Start application containers

### Step 5: Configure Environment Variables
```bash
cd /opt/slack2teams
nano .env.prod
```

Update with your actual values:
```env
# OpenAI API Key
OPENAI_API_KEY=sk-...

# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=your-client-id
MICROSOFT_CLIENT_SECRET=your-client-secret
MICROSOFT_TENANT=cloudfuze.com

# Langfuse Configuration
LANGFUSE_PUBLIC_KEY=pk-lf-...
LANGFUSE_SECRET_KEY=sk-lf-...
LANGFUSE_HOST=https://cloud.langfuse.com

# MongoDB Configuration
MONGODB_URL=mongodb://localhost:27017
MONGODB_DATABASE=slack2teams
MONGODB_CHAT_COLLECTION=chat_histories
MONGODB_VECTORSTORE_COLLECTION=cloudfuze_vectorstore

# Vectorstore Configuration
VECTORSTORE_BACKEND=mongodb
INITIALIZE_VECTORSTORE=false
```

### Step 6: Restart Services
```bash
docker-compose -f docker-compose.prod.yml --env-file .env.prod down
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d --build
```

### Step 7: Verify Deployment
```bash
# Check container status
docker-compose -f docker-compose.prod.yml ps

# Check logs
docker-compose -f docker-compose.prod.yml logs -f

# Test health endpoint
curl https://newcf3.cloudfuze.com/health
```

---

## ✅ Post-Deployment Verification

### 1. Application Access
- [ ] Visit `https://newcf3.cloudfuze.com`
- [ ] Login page loads correctly
- [ ] Microsoft OAuth login works
- [ ] Email domain restriction enforced (`@cloudfuze.com`)

### 2. Chatbot Functionality
- [ ] Ask CloudFuze-related question (should work)
- [ ] Ask general question (should be rejected gracefully)
- [ ] Verify dynamic rejection responses
- [ ] Test streaming responses
- [ ] Check feedback buttons (👍/👎)

### 3. MongoDB Connectivity
- [ ] Chat history is saved
- [ ] Previous conversations load correctly
- [ ] Vector search returns results
- [ ] Verify 1511 documents in vectorstore

### 4. SSL Certificate
- [ ] HTTPS works correctly
- [ ] Certificate is valid
- [ ] HTTP redirects to HTTPS
- [ ] No mixed content warnings

### 5. Monitoring & Logs
- [ ] Langfuse traces are being logged
- [ ] Check Langfuse dashboard: `https://cloud.langfuse.com`
- [ ] Application logs are accessible
- [ ] No critical errors in logs

### 6. Performance
- [ ] Response time < 3 seconds
- [ ] Streaming works smoothly
- [ ] No memory leaks
- [ ] CPU usage is normal

---

## 🔍 Testing Checklist

### Functional Tests
- [ ] **Authentication:** Microsoft login works
- [ ] **Chat:** Send message and receive response
- [ ] **Streaming:** Real-time response streaming works
- [ ] **History:** Previous chats load correctly
- [ ] **New Chat:** Clear button resets conversation
- [ ] **Rejection:** General questions are rejected gracefully
- [ ] **Feedback:** Thumbs up/down buttons work
- [ ] **Copy:** Copy button works for responses

### CloudFuze-Specific Tests
- [ ] "What is CloudFuze?" - Should answer from vectorstore
- [ ] "How does Slack to Teams migration work?" - Detailed answer
- [ ] "What is Python?" - Should be rejected
- [ ] "Tell me about AI" - Should be rejected with dynamic message
- [ ] Verify contact link appears in rejections

### Security Tests
- [ ] Non-CloudFuze emails are rejected
- [ ] HTTPS enforced
- [ ] CORS configured correctly
- [ ] No sensitive data in logs
- [ ] Environment variables secure

---

## 📦 Important Files & Locations

### Application
- **Directory:** `/opt/slack2teams`
- **Environment:** `/opt/slack2teams/.env.prod`
- **Logs:** `/opt/slack2teams/logs/`
- **Data:** `/opt/slack2teams/data/`

### Nginx
- **Config:** `/etc/nginx/sites-available/slack2teams`
- **Logs:** `/var/log/nginx/`
- **SSL Certs:** `/etc/letsencrypt/live/newcf3.cloudfuze.com/`

### Docker
- **Compose File:** `docker-compose.prod.yml`
- **Containers:** `slack2teams-backend-prod`, `slack2teams-nginx-prod`

### Systemd
- **Service:** `/etc/systemd/system/slack2teams.service`

---

## 🛠️ Management Commands

### Docker Compose
```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker-compose.prod.yml down

# Restart services
docker-compose -f docker-compose.prod.yml restart

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# View specific service logs
docker-compose -f docker-compose.prod.yml logs -f backend

# Rebuild and restart
docker-compose -f docker-compose.prod.yml up -d --build
```

### Systemd Service
```bash
# Start service
sudo systemctl start slack2teams

# Stop service
sudo systemctl stop slack2teams

# Restart service
sudo systemctl restart slack2teams

# Check status
sudo systemctl status slack2teams

# Enable auto-start
sudo systemctl enable slack2teams
```

### SSL Certificate Renewal
```bash
# Renew certificate (automatic with certbot)
sudo certbot renew

# Test renewal
sudo certbot renew --dry-run
```

### Monitoring
```bash
# Check disk space
df -h

# Check memory usage
free -h

# Check Docker stats
docker stats

# Check MongoDB connection
mongo mongodb://localhost:27017/slack2teams --eval "db.stats()"
```

---

## 🔧 Troubleshooting

### Issue: Application not accessible
**Solution:**
```bash
# Check if containers are running
docker-compose -f docker-compose.prod.yml ps

# Check logs for errors
docker-compose -f docker-compose.prod.yml logs

# Verify firewall
sudo ufw status

# Test backend directly
curl http://localhost:8002/health
```

### Issue: SSL certificate issues
**Solution:**
```bash
# Check certificate status
sudo certbot certificates

# Renew manually
sudo certbot renew --force-renewal

# Check nginx config
sudo nginx -t
sudo systemctl restart nginx
```

### Issue: MongoDB connection failed
**Solution:**
```bash
# Check MongoDB status
sudo systemctl status mongod

# Check MongoDB logs
sudo tail -f /var/log/mongodb/mongod.log

# Verify connection string in .env.prod
cat /opt/slack2teams/.env.prod | grep MONGODB_URL
```

### Issue: Microsoft OAuth not working
**Solution:**
1. Verify redirect URI in Azure Portal
2. Check client ID and secret in `.env.prod`
3. Ensure `MICROSOFT_TENANT` is correct
4. Check browser console for errors

---

## 📞 Support & Documentation

- **Application Logs:** `docker-compose -f docker-compose.prod.yml logs -f`
- **Langfuse Dashboard:** https://cloud.langfuse.com
- **MongoDB Logs:** `/var/log/mongodb/mongod.log`
- **Nginx Logs:** `/var/log/nginx/`

---

## ✨ Post-Deployment Notes

### Backup Strategy
- [ ] Setup automated MongoDB backups
- [ ] Backup vectorstore regularly
- [ ] Keep environment file secure

### Monitoring Setup
- [ ] Configure uptime monitoring
- [ ] Setup alerts for downtime
- [ ] Monitor Langfuse traces
- [ ] Track error rates

### Maintenance
- [ ] Schedule weekly health checks
- [ ] Review logs regularly
- [ ] Update dependencies monthly
- [ ] Renew SSL certificate (automatic)

---

## 🎉 Deployment Complete!

**Access Points:**
- **Application:** https://newcf3.cloudfuze.com
- **API Docs:** https://newcf3.cloudfuze.com/docs
- **Health Check:** https://newcf3.cloudfuze.com/health

**Next Steps:**
1. ✅ Test all functionality
2. ✅ Monitor for 24 hours
3. ✅ Document any issues
4. ✅ Train users on the new system

---

**Deployment Date:** _________________  
**Deployed By:** _________________  
**Verified By:** _________________

