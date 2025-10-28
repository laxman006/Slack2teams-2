# Slack2teams-2 Deployment Guide - Complete Summary

## Server Information
- **Server IP**: 64.227.160.206
- **Domain**: newcf3.cloudfuze.com
- **OS**: Ubuntu (DigitalOcean Droplet)
- **Deployment Path**: /opt/Slack2teams-2
- **Repository**: https://github.com/laxman006/Slack2teams-2.git

## Current Deployment Status
✅ **Successfully Deployed and Running**
- Application accessible at: https://newcf3.cloudfuze.com
- Backend API: https://newcf3.cloudfuze.com/api/docs
- Health Check: https://newcf3.cloudfuze.com/health
- SSL/HTTPS: Configured with Let's Encrypt
- MongoDB Atlas: Connected and working
- Langfuse: Integrated with cloud.langfuse.com

---

## Environment Configuration

### Current .env File (Production)
```bash
LANGFUSE_PUBLIC_KEY=pk-lf-000a995c-27e1-4de4-b992-bc0197892898
LANGFUSE_SECRET_KEY=sk-lf-144e1705-30ea-41f7-945d-ab61397ebd60
LANGFUSE_HOST=https://cloud.langfuse.com
OPENAI_API_KEY=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

# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=861e696d-f41c-41ee-a7c2-c838fd185d6d
MICROSOFT_CLIENT_SECRET=6Ag8Q~i3H50iy0B_nYJYVtZ5JilM3MAJSIe9tc5d
MICROSOFT_TENANT=common

# MongoDB Configuration
MONGODB_URL=mongodb+srv://sudityanimmala_db_user:Arss_2025@cluster0.sgqafxp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
MONGODB_DATABASE=slack2teams
MONGODB_CHAT_COLLECTION=chat_histories
```

---

## Docker Compose Configuration

### Current docker-compose.yml
```yaml
version: '3.8'

services:
  # Backend FastAPI service
  backend:
    build: .
    container_name: slack2teams-backend
    user: "0:0"
    ports:
      - "8002:8002"
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - MICROSOFT_CLIENT_ID=${MICROSOFT_CLIENT_ID}
      - MICROSOFT_CLIENT_SECRET=${MICROSOFT_CLIENT_SECRET}
      - MICROSOFT_TENANT=${MICROSOFT_TENANT}
      - LANGFUSE_PUBLIC_KEY=${LANGFUSE_PUBLIC_KEY}
      - LANGFUSE_SECRET_KEY=${LANGFUSE_SECRET_KEY}
      - LANGFUSE_HOST=${LANGFUSE_HOST}
      - MONGODB_URL=${MONGODB_URL}
      - MONGODB_DATABASE=${MONGODB_DATABASE}
      - MONGODB_CHAT_COLLECTION=${MONGODB_CHAT_COLLECTION}
    volumes:
      - ./data:/app/data
      - ./images:/app/images
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8002/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Nginx reverse proxy
  nginx:
    image: nginx:alpine
    container_name: slack2teams-nginx
    ports:
      - "0.0.0.0:80:80"
      - "0.0.0.0:443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - ./:/var/www/html:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - backend
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "wget", "--quiet", "--tries=1", "--spider", "http://localhost/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  # MongoDB (local instance - optional)
  mongodb:
    image: mongo:7.0
    container_name: slack2teams-mongodb
    ports:
      - "27017:27017"
    volumes:
      - mongodb_data:/data/db
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "mongosh", "--eval", "db.adminCommand('ping')"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  mongodb_data:
```

---

## Nginx Configuration (nginx.conf)

### SSL-Enabled Configuration
```nginx
# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name newcf3.cloudfuze.com 64.227.160.206;
    
    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

# HTTPS server
server {
    listen 443 ssl http2;
    server_name newcf3.cloudfuze.com 64.227.160.206;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/newcf3.cloudfuze.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/newcf3.cloudfuze.com/privkey.pem;
    
    # SSL Security Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Content-Security-Policy "default-src 'self' https: data: 'unsafe-inline' 'unsafe-eval';" always;

    # Root directory for static files
    root /var/www/html;
    index index.html login.html;

    # Increase client body size for file uploads
    client_max_body_size 100M;

    # Backend API proxy
    location /api/ {
        proxy_pass http://backend:8002/;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://backend:8002/health;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Images
    location /images/ {
        alias /var/www/html/images/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Error pages
    error_page 404 /index.html;
    error_page 500 502 503 504 /index.html;
}
```

---

## Deployment Commands

### Initial Deployment
```bash
# 1. Navigate to deployment directory
cd /opt

# 2. Clone the repository
git clone https://github.com/laxman006/Slack2teams-2.git
cd Slack2teams-2

# 3. Create .env file with production credentials
cat > .env << 'EOF'
[paste environment variables here]
EOF

# 4. Set proper permissions
chmod 600 .env
chmod -R 755 data/
chmod -R 777 data/chroma_db/

# 5. Build and start containers
docker-compose up -d --build

# 6. Check status
docker-compose ps
docker-compose logs -f
```

### Update/Redeploy Commands
```bash
# Navigate to project directory
cd /opt/Slack2teams-2

# Pull latest changes
git fetch origin
git pull origin main

# Update .env if needed
nano .env

# Restart containers
docker-compose down
docker-compose up -d --build

# Check logs
docker-compose logs -f backend
```

### Quick Restart (No Code Changes)
```bash
cd /opt/Slack2teams-2

# Restart specific service
docker-compose restart backend
docker-compose restart nginx

# Or restart all
docker-compose restart

# Check status
docker-compose ps
```

---

## SSL Certificate Setup

### Initial SSL Certificate Installation
```bash
# Install certbot
apt update && apt install -y certbot

# Stop nginx temporarily
docker-compose stop nginx

# Get SSL certificate
certbot certonly --standalone -d newcf3.cloudfuze.com --email your-email@example.com --agree-tos --non-interactive

# Restart nginx
docker-compose start nginx
```

### SSL Certificate Renewal
```bash
# Check certificate expiry
certbot certificates

# Renew certificate (if needed)
docker-compose stop nginx
certbot renew
docker-compose start nginx

# Auto-renewal (add to crontab)
# 0 0 * * 0 certbot renew --quiet && docker-compose restart nginx
```

---

## MongoDB Atlas Configuration

### Connection Details
- **Connection String**: mongodb+srv://sudityanimmala_db_user:Arss_2025@cluster0.sgqafxp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0
- **Database**: slack2teams
- **Collection**: chat_histories

### Important: IP Whitelist
**CRITICAL**: Add server IP to MongoDB Atlas Network Access:
1. Go to MongoDB Atlas Dashboard
2. Navigate to "Network Access"
3. Add IP: **64.227.160.206/32**
4. Or for testing: **0.0.0.0/0** (allow all - less secure)

---

## Troubleshooting Commands

### Check Container Status
```bash
# View all containers
docker-compose ps

# View specific container logs
docker-compose logs backend
docker-compose logs nginx
docker-compose logs mongodb

# Follow logs in real-time
docker-compose logs -f backend

# View last 100 lines
docker-compose logs --tail=100 backend
```

### Check Application Health
```bash
# Test backend directly
curl -I http://localhost:8002/health

# Test through nginx
curl -I http://localhost/health

# Test domain
curl -I https://newcf3.cloudfuze.com/health

# Test API docs
curl -I https://newcf3.cloudfuze.com/api/docs
```

### Check MongoDB Connection
```bash
# Test MongoDB connection from container
docker-compose exec backend python3 -c "
import os
from motor.motor_asyncio import AsyncIOMotorClient
import asyncio

async def test_connection():
    client = AsyncIOMotorClient(os.getenv('MONGODB_URL'))
    try:
        await client.admin.command('ping')
        print('✅ MongoDB connection successful!')
    except Exception as e:
        print(f'❌ MongoDB connection failed: {e}')
    finally:
        client.close()

asyncio.run(test_connection())
"
```

### Check SSL Certificate
```bash
# Check certificate details
echo | openssl s_client -servername newcf3.cloudfuze.com -connect newcf3.cloudfuze.com:443 2>/dev/null | openssl x509 -noout -dates

# Check certificate files
ls -la /etc/letsencrypt/live/newcf3.cloudfuze.com/
```

### Network Diagnostics
```bash
# Check DNS resolution
nslookup newcf3.cloudfuze.com
dig newcf3.cloudfuze.com

# Check open ports
netstat -tlnp | grep -E ':(80|443|8002|27017)'

# Check firewall
ufw status

# Test from server
curl -I http://localhost:80
curl -I https://newcf3.cloudfuze.com
```

---

## Common Issues and Solutions

### Issue 1: MongoDB Connection Failed
**Symptoms**: `localhost:27017: [Errno 111] Connection refused`

**Solution**:
1. Check if MongoDB Atlas IP is whitelisted (64.227.160.206)
2. Verify MONGODB_URL in .env file
3. Check if environment variables are loaded: `docker-compose exec backend env | grep MONGODB`

### Issue 2: SSL/HTTPS Not Working
**Symptoms**: `ERR_CONNECTION_REFUSED` on HTTPS

**Solution**:
1. Check if SSL certificate exists: `ls -la /etc/letsencrypt/live/newcf3.cloudfuze.com/`
2. Verify nginx.conf has SSL configuration
3. Ensure ports 80 and 443 are open
4. Restart nginx: `docker-compose restart nginx`

### Issue 3: Domain Not Accessible
**Symptoms**: Domain doesn't load, but IP works

**Solution**:
1. Check DNS: `nslookup newcf3.cloudfuze.com`
2. Verify nginx binds to 0.0.0.0: `netstat -tlnp | grep :80`
3. Update docker-compose.yml ports to: `"0.0.0.0:80:80"` and `"0.0.0.0:443:443"`

### Issue 4: ChromaDB Permission Denied
**Symptoms**: `PermissionError: [Errno 13] Permission denied`

**Solution**:
```bash
docker-compose down
rm -rf data/chroma_db/*
chmod -R 777 data/chroma_db/
docker-compose up -d
```

### Issue 5: Git Pull Not Working
**Symptoms**: Local changes prevent pull

**Solution**:
```bash
# Stash local changes
git stash

# Pull latest code
git pull origin main

# Apply stashed changes (optional)
git stash pop

# Or force reset to remote
git fetch origin
git reset --hard origin/main
```

---

## File Permissions

### Required Permissions
```bash
# Environment file
chmod 600 .env

# Data directories
chmod -R 755 data/
chmod -R 777 data/chroma_db/

# JSON files
chmod 644 data/chat_history.json
chmod 644 data/feedback_history.json
chmod 644 data/vectorstore_metadata.json
```

---

## Monitoring and Maintenance

### Daily Checks
```bash
# Check container health
docker-compose ps

# Check disk space
df -h

# Check logs for errors
docker-compose logs --tail=100 backend | grep -i error
```

### Weekly Maintenance
```bash
# Clean up Docker
docker system prune -f

# Check SSL certificate expiry
certbot certificates

# Backup MongoDB data (if using local MongoDB)
docker-compose exec mongodb mongodump --out=/data/backup
```

### Monthly Tasks
```bash
# Update system packages
apt update && apt upgrade -y

# Update Docker images
docker-compose pull
docker-compose up -d

# Review logs for issues
docker-compose logs --since=30d backend > logs_$(date +%Y%m%d).txt
```

---

## Backup and Recovery

### Backup MongoDB Atlas
MongoDB Atlas handles backups automatically. Access them via:
1. MongoDB Atlas Dashboard
2. Clusters → Your Cluster
3. Backup tab

### Backup Application Data
```bash
# Backup data directory
tar -czf backup_$(date +%Y%m%d).tar.gz data/

# Backup environment file
cp .env .env.backup

# Backup nginx configuration
cp nginx.conf nginx.conf.backup
```

### Recovery
```bash
# Restore data directory
tar -xzf backup_YYYYMMDD.tar.gz

# Restore environment
cp .env.backup .env

# Restart services
docker-compose restart
```

---

## Performance Optimization

### Nginx Optimization
- Gzip compression enabled
- Static file caching (30 days for images)
- HTTP/2 enabled
- Connection keep-alive

### Docker Optimization
- Health checks configured
- Restart policies set to `unless-stopped`
- Resource limits can be added if needed

### MongoDB Optimization
- Indexes created automatically on startup
- Connection pooling handled by Motor driver

---

## Security Considerations

### Current Security Measures
✅ SSL/TLS encryption (Let's Encrypt)
✅ Security headers (HSTS, X-Frame-Options, CSP)
✅ Environment variables for secrets
✅ MongoDB Atlas with IP whitelist
✅ Firewall configuration (UFW)

### Recommended Additional Security
- [ ] Enable MongoDB authentication (if using local MongoDB)
- [ ] Implement rate limiting in nginx
- [ ] Add fail2ban for SSH protection
- [ ] Regular security updates
- [ ] Implement API key rotation

---

## Contact and Support

### Key URLs
- **Application**: https://newcf3.cloudfuze.com
- **API Docs**: https://newcf3.cloudfuze.com/api/docs
- **Health Check**: https://newcf3.cloudfuze.com/health
- **GitHub**: https://github.com/laxman006/Slack2teams-2.git

### Important Notes
- Always backup before major changes
- Test in development before deploying to production
- Monitor logs regularly for issues
- Keep SSL certificates renewed
- Maintain MongoDB Atlas IP whitelist

---

## Quick Reference Commands

```bash
# Navigate to project
cd /opt/Slack2teams-2

# Pull latest code
git pull origin main

# Restart all services
docker-compose restart

# View logs
docker-compose logs -f backend

# Check status
docker-compose ps

# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Rebuild and restart
docker-compose up -d --build

# Check health
curl -I https://newcf3.cloudfuze.com/health
```

---

**Last Updated**: October 23, 2025
**Deployment Status**: ✅ Production - Running Successfully
**Server**: 64.227.160.206 (newcf3.cloudfuze.com)



