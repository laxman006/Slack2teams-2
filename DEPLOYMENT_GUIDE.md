# Deployment Guide for CF_Chatbot_Dev

This guide explains how to deploy the CF_Chatbot_Dev code to different environments.

## Deployment Environments

1. **newcf3.cloudfuze.com** - Development/Testing environment (deploy first)
2. **ai.cloudfuze.com** - Production environment (deploy after testing)

## Prerequisites

- Ubuntu server (20.04 or later recommended)
- SSH access to the server
- Domain DNS configured to point to the server IP
- API keys and credentials ready

## Deployment Steps

### Step 1: Deploy to newcf3.cloudfuze.com (Development)

1. **SSH into the server:**
   ```bash
   ssh user@newcf3.cloudfuze.com
   ```

2. **Clone or pull the latest code:**
   ```bash
   cd /opt
   git clone <repository-url> slack2teams-newcf3
   # OR if already exists:
   cd slack2teams-newcf3
   git pull origin CF_Chatbot_Dev
   ```

3. **Navigate to the project directory:**
   ```bash
   cd slack2teams-newcf3
   ```

4. **Make the deployment script executable:**
   ```bash
   chmod +x deploy-newcf3.sh
   ```

5. **Run the deployment script:**
   ```bash
   ./deploy-newcf3.sh
   ```

6. **Configure environment variables:**
   - Edit `.env.prod` file with your actual API keys and credentials
   - Required variables:
     - `OPENAI_API_KEY`
     - `MICROSOFT_CLIENT_ID`
     - `MICROSOFT_CLIENT_SECRET`
     - `MICROSOFT_TENANT`
     - `MONGODB_URL`
     - `LANGFUSE_PUBLIC_KEY` (optional)
     - `LANGFUSE_SECRET_KEY` (optional)

7. **Restart services after updating .env.prod:**
   ```bash
   cd /opt/slack2teams-newcf3
   docker-compose -f docker-compose.prod.yml --env-file .env.prod down
   docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
   ```

8. **Verify deployment:**
   - Check health endpoint: `https://newcf3.cloudfuze.com/health`
   - Test the application functionality
   - Review logs: `docker-compose -f docker-compose.prod.yml logs -f`

### Step 2: Test on newcf3.cloudfuze.com

Before deploying to production, thoroughly test:
- [ ] Application loads correctly
- [ ] Authentication works
- [ ] Chat functionality works
- [ ] API endpoints respond correctly
- [ ] SSL certificate is valid
- [ ] All features work as expected

### Step 3: Deploy to ai.cloudfuze.com (Production)

Once testing on newcf3.cloudfuze.com is complete:

1. **SSH into the production server:**
   ```bash
   ssh user@ai.cloudfuze.com
   ```

2. **Clone or pull the latest code:**
   ```bash
   cd /opt
   git clone <repository-url> slack2teams
   # OR if already exists:
   cd slack2teams
   git pull origin CF_Chatbot_Dev
   ```

3. **Navigate to the project directory:**
   ```bash
   cd slack2teams
   ```

4. **Make the deployment script executable:**
   ```bash
   chmod +x deploy-ubuntu.sh
   ```

5. **Run the deployment script:**
   ```bash
   ./deploy-ubuntu.sh
   ```

6. **Configure environment variables:**
   - Edit `.env.prod` file with production API keys and credentials
   - Use production-grade credentials (different from dev if needed)

7. **Restart services after updating .env.prod:**
   ```bash
   cd /opt/slack2teams
   docker-compose -f docker-compose.prod.yml --env-file .env.prod down
   docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
   ```

8. **Verify production deployment:**
   - Check health endpoint: `https://ai.cloudfuze.com/health`
   - Test the application functionality
   - Monitor logs: `docker-compose -f docker-compose.prod.yml logs -f`

## Management Commands

### View Logs
```bash
# For newcf3.cloudfuze.com
cd /opt/slack2teams-newcf3
docker-compose -f docker-compose.prod.yml logs -f

# For ai.cloudfuze.com
cd /opt/slack2teams
docker-compose -f docker-compose.prod.yml logs -f
```

### Restart Services
```bash
# For newcf3.cloudfuze.com
cd /opt/slack2teams-newcf3
docker-compose -f docker-compose.prod.yml restart

# For ai.cloudfuze.com
cd /opt/slack2teams
docker-compose -f docker-compose.prod.yml restart
```

### Stop Services
```bash
# For newcf3.cloudfuze.com
cd /opt/slack2teams-newcf3
docker-compose -f docker-compose.prod.yml down

# For ai.cloudfuze.com
cd /opt/slack2teams
docker-compose -f docker-compose.prod.yml down
```

### Start Services
```bash
# For newcf3.cloudfuze.com
cd /opt/slack2teams-newcf3
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# For ai.cloudfuze.com
cd /opt/slack2teams
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

### Check Service Status
```bash
# For newcf3.cloudfuze.com
sudo systemctl status slack2teams-newcf3

# For ai.cloudfuze.com
sudo systemctl status slack2teams
```

## Troubleshooting

### SSL Certificate Issues
If SSL certificate setup fails:
1. Ensure DNS is properly configured
2. Check that ports 80 and 443 are open
3. Run certbot manually: `sudo certbot certonly --standalone -d <domain>`

### Service Won't Start
1. Check logs: `docker-compose -f docker-compose.prod.yml logs`
2. Verify .env.prod file has all required variables
3. Check Docker status: `sudo systemctl status docker`
4. Verify disk space: `df -h`

### Application Not Accessible
1. Check firewall: `sudo ufw status`
2. Verify nginx is running: `sudo systemctl status nginx`
3. Check nginx configuration: `sudo nginx -t`
4. Review nginx logs: `sudo tail -f /var/log/nginx/error.log`

### Backend Health Check Fails
1. Check backend logs: `docker-compose -f docker-compose.prod.yml logs backend`
2. Verify MongoDB connection (if using MongoDB)
3. Check environment variables are correct
4. Ensure data directory has proper permissions

## File Structure

```
/opt/slack2teams-newcf3/          # Development environment
├── .env.prod                      # Environment variables
├── docker-compose.prod.yml        # Docker Compose configuration
├── nginx-newcf3.conf              # Nginx configuration
├── deploy-newcf3.sh               # Deployment script
└── ...                            # Application files

/opt/slack2teams/                  # Production environment
├── .env.prod                      # Environment variables
├── docker-compose.prod.yml        # Docker Compose configuration
├── nginx-prod.conf                # Nginx configuration
├── deploy-ubuntu.sh               # Deployment script
└── ...                            # Application files
```

## Important Notes

1. **Always test on newcf3.cloudfuze.com first** before deploying to production
2. **Use different API keys** for dev and production if possible
3. **Backup data** before major deployments
4. **Monitor logs** after deployment to catch any issues early
5. **SSL certificates** are automatically renewed by certbot, but monitor renewal status

## Support

For issues or questions:
- Check application logs
- Review Docker container status
- Verify environment variables
- Check nginx and system logs

