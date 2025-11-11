# Deployment Ready for ai.cloudfuze.com

## 🎯 Configuration Complete

Your Slack2Teams application is now configured for deployment to:
- **Domain**: ai.cloudfuze.com
- **IP Address**: 64.227.160.206

## 📝 Files Updated

The following files have been updated with the new domain and IP:

1. **deploy-ubuntu.sh** - Main deployment script
2. **nginx-prod.conf** - Nginx reverse proxy configuration
3. **docker-compose.prod.yml** - Production Docker Compose configuration
4. **index.html** - Frontend API configuration
5. **restart_services.sh** - Service restart script
6. **restart_services.bat** - Windows service restart script

## ✅ Pre-Deployment Checklist

Before running the deployment, ensure:

1. **DNS Configuration**
   - [ ] Point `ai.cloudfuze.com` DNS A record to `64.227.160.206`
   - [ ] Wait for DNS propagation (can take 5-60 minutes)
   - [ ] Verify with: `nslookup ai.cloudfuze.com`

2. **Environment Variables**
   - [ ] Prepare your production API keys and secrets
   - [ ] Have your OpenAI API key ready
   - [ ] Have your Microsoft OAuth credentials ready (Client ID, Secret, Tenant)
   - [ ] Prepare MongoDB connection details (if using MongoDB)

3. **Server Access**
   - [ ] SSH access to the Ubuntu server at 64.227.160.206
   - [ ] User with sudo privileges (non-root)
   - [ ] SSH key or password authentication

## 🚀 Deployment Steps

### 1. Copy Files to Server

```bash
# From your local machine
scp -r . user@64.227.160.206:/home/user/slack2teams
```

### 2. SSH into Server

```bash
ssh user@64.227.160.206
cd /home/user/slack2teams
```

### 3. Make Deployment Script Executable

```bash
chmod +x deploy-ubuntu.sh
```

### 4. Run Deployment Script

```bash
./deploy-ubuntu.sh
```

The script will:
- ✅ Update system packages
- ✅ Install Docker and Docker Compose
- ✅ Install Certbot for SSL certificates
- ✅ Copy application files to `/opt/slack2teams`
- ✅ Create production environment file (`.env.prod`)
- ✅ Build and start Docker containers
- ✅ Set up SSL certificate with Let's Encrypt
- ✅ Configure Nginx as reverse proxy
- ✅ Set up firewall rules
- ✅ Create systemd service for auto-start

### 5. Configure Environment Variables

After the script runs, edit the production environment file:

```bash
sudo nano /opt/slack2teams/.env.prod
```

Update these values:
```env
# OpenAI API Key
OPENAI_API_KEY=your_actual_openai_api_key

# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=your_actual_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_actual_microsoft_client_secret
MICROSOFT_TENANT=your_actual_microsoft_tenant

# Langfuse Configuration (Optional)
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=http://langfuse:3000

# NextAuth Secret (if using Langfuse)
NEXTAUTH_SECRET=your_nextauth_secret

# MongoDB Configuration
MONGODB_URL=your_mongodb_connection_string
MONGODB_DATABASE=slack2teams
```

### 6. Restart Services

```bash
cd /opt/slack2teams
docker-compose -f docker-compose.prod.yml restart
```

## 🌐 Access Your Application

After successful deployment, your application will be available at:

- **Main App**: https://ai.cloudfuze.com
- **API Docs**: https://ai.cloudfuze.com/api/docs
- **Health Check**: https://ai.cloudfuze.com/health

## 🔧 Management Commands

### View Logs
```bash
cd /opt/slack2teams
docker-compose -f docker-compose.prod.yml logs -f
```

### Restart Services
```bash
cd /opt/slack2teams
docker-compose -f docker-compose.prod.yml restart
```

### Stop Services
```bash
cd /opt/slack2teams
docker-compose -f docker-compose.prod.yml down
```

### Start Services
```bash
cd /opt/slack2teams
docker-compose -f docker-compose.prod.yml up -d
```

### Check Service Status
```bash
sudo systemctl status slack2teams
```

### View Nginx Logs
```bash
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log
```

## 🔒 SSL Certificate

The deployment script will automatically obtain and configure SSL certificates from Let's Encrypt. The certificates will:
- ✅ Auto-renew before expiration
- ✅ Redirect HTTP to HTTPS
- ✅ Use modern TLS protocols (TLSv1.2, TLSv1.3)

## 🐛 Troubleshooting

### Issue: SSL Certificate Fails
```bash
# Manually obtain certificate
sudo certbot certonly --standalone -d ai.cloudfuze.com --email admin@cloudfuze.com
```

### Issue: Docker Containers Not Starting
```bash
# Check logs
docker-compose -f docker-compose.prod.yml logs

# Rebuild containers
docker-compose -f docker-compose.prod.yml up --build -d
```

### Issue: Port Already in Use
```bash
# Check what's using port 80/443
sudo lsof -i :80
sudo lsof -i :443

# Kill process if needed
sudo kill -9 <PID>
```

## 📞 Support

For issues or questions:
- Check application logs: `docker-compose -f docker-compose.prod.yml logs`
- Check Nginx logs: `sudo tail -f /var/log/nginx/error.log`
- Verify DNS: `nslookup ai.cloudfuze.com`
- Test connectivity: `curl -I https://ai.cloudfuze.com`

---

**Ready to Deploy!** 🚀

All configurations are set for ai.cloudfuze.com at 64.227.160.206.

