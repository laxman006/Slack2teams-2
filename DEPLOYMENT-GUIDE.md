# 🚀 Slack2Teams Production Deployment Guide

## Server Information
- **Domain**: newcf3.cloudfuze.com
- **IP Address**: 64.227.160.206
- **OS**: Ubuntu (20.04+ recommended)

## Quick Deployment Commands

### 1. Connect to Your Ubuntu Server

```bash
ssh root@64.227.160.206
# or
ssh your-username@64.227.160.206
```

### 2. Clone and Deploy

```bash
# Clone your repository (replace with your actual repo URL)
git clone https://github.com/your-username/slack2teams.git
cd slack2teams

# Make deployment script executable
chmod +x deploy-ubuntu.sh

# Run the deployment script
./deploy-ubuntu.sh
```

### 3. Configure Environment Variables

```bash
# Edit the production environment file
nano .env.prod

# Add your actual API keys:
OPENAI_API_KEY=sk-proj-your-actual-openai-key-here
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret
MICROSOFT_TENANT=your-microsoft-tenant
```

### 4. Restart Services

```bash
# Restart with new environment variables
docker-compose -f docker-compose.prod.yml --env-file .env.prod down
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
```

## Manual Deployment Steps

If you prefer manual deployment:

### Step 1: Update System

```bash
sudo apt update && sudo apt upgrade -y
```

### Step 2: Install Docker

```bash
# Install Docker
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

### Step 3: Install Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### Step 4: Setup Application

```bash
# Create application directory
sudo mkdir -p /opt/slack2teams
sudo chown $USER:$USER /opt/slack2teams
cd /opt/slack2teams

# Copy your application files here
# (Upload your project files to this directory)
```

### Step 5: Configure Environment

```bash
# Create production environment file
cat > .env.prod << EOF
OPENAI_API_KEY=your_openai_api_key_here
MICROSOFT_CLIENT_ID=your_microsoft_client_id_here
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret_here
MICROSOFT_TENANT=your_microsoft_tenant_here
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key_here
LANGFUSE_SECRET_KEY=your_langfuse_secret_key_here
LANGFUSE_HOST=http://langfuse:3000
NEXTAUTH_SECRET=your_nextauth_secret_here
EOF
```

### Step 6: Setup SSL Certificate

```bash
# Stop any running nginx
sudo systemctl stop nginx

# Get SSL certificate
sudo certbot certonly --standalone -d newcf3.cloudfuze.com --non-interactive --agree-tos --email admin@cloudfuze.com
```

### Step 7: Deploy Application

```bash
# Build and start containers
docker-compose -f docker-compose.prod.yml --env-file .env.prod up --build -d
```

### Step 8: Configure Firewall

```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw --force enable
```

## Post-Deployment Verification

### 1. Check Service Status

```bash
# Check Docker containers
docker-compose -f docker-compose.prod.yml ps

# Check systemd service
sudo systemctl status slack2teams

# Check nginx
sudo systemctl status nginx
```

### 2. Test Application

```bash
# Test health endpoint
curl -I https://newcf3.cloudfuze.com/health

# Test main page
curl -I https://newcf3.cloudfuze.com/

# Test API
curl -I https://newcf3.cloudfuze.com/api/docs
```

### 3. Check Logs

```bash
# Application logs
docker-compose -f docker-compose.prod.yml logs -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -u slack2teams -f
```

## Management Commands

### Start/Stop Services

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# Stop services
docker-compose -f docker-compose.prod.yml down

# Restart services
docker-compose -f docker-compose.prod.yml restart

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### Update Application

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up --build -d
```

### Backup Data

```bash
# Backup application data
tar -czf slack2teams-backup-$(date +%Y%m%d).tar.gz data/ logs/

# Backup SSL certificates
sudo tar -czf ssl-backup-$(date +%Y%m%d).tar.gz /etc/letsencrypt/
```

## Monitoring and Maintenance

### SSL Certificate Renewal

```bash
# Test renewal
sudo certbot renew --dry-run

# Manual renewal
sudo certbot renew

# Check certificate expiry
echo | openssl s_client -servername newcf3.cloudfuze.com -connect newcf3.cloudfuze.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Log Rotation

```bash
# Check log rotation
sudo logrotate -d /etc/logrotate.d/slack2teams

# Force log rotation
sudo logrotate -f /etc/logrotate.d/slack2teams
```

### System Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker images
docker-compose -f docker-compose.prod.yml pull
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Common Issues

1. **Domain not accessible**:
   - Check DNS settings
   - Verify domain points to 64.227.160.206
   - Check firewall rules

2. **SSL certificate issues**:
   - Verify domain is accessible on port 80
   - Check Let's Encrypt rate limits
   - Review certificate logs: `/var/log/letsencrypt/`

3. **Application not starting**:
   - Check environment variables in `.env.prod`
   - Review Docker logs: `docker-compose -f docker-compose.prod.yml logs`
   - Verify API keys are valid

4. **Nginx errors**:
   - Test configuration: `sudo nginx -t`
   - Check error logs: `sudo tail -f /var/log/nginx/error.log`
   - Verify SSL certificate paths

### Performance Optimization

```bash
# Monitor resource usage
docker stats

# Check disk space
df -h

# Monitor memory usage
free -h

# Check CPU usage
top
```

## Security Considerations

1. **Keep system updated**: Regular security updates
2. **Monitor logs**: Check for suspicious activity
3. **Backup regularly**: Automated backups of data and certificates
4. **Use strong passwords**: For all accounts and API keys
5. **Limit access**: Use SSH keys instead of passwords
6. **Monitor SSL**: Regular certificate renewal checks

## Support and Maintenance

- **Application URL**: https://newcf3.cloudfuze.com
- **API Documentation**: https://newcf3.cloudfuze.com/api/docs
- **Health Check**: https://newcf3.cloudfuze.com/health
- **Logs Location**: `/opt/slack2teams/logs/`
- **Configuration**: `/opt/slack2teams/.env.prod`

For issues or questions, check the logs first and ensure all environment variables are correctly set.
