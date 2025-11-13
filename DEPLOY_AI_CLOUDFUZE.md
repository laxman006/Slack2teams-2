# Deployment Guide for ai.cloudfuze.com

This guide will help you deploy the application to `ai.cloudfuze.com` (64.227.160.206).

## Prerequisites

1. SSH access to the server at `64.227.160.206`
2. Docker and Docker Compose installed on the server
3. Domain `ai.cloudfuze.com` pointing to the server IP
4. Let's Encrypt certificates (or SSL certificates) for the domain

## Step 1: SSL Certificate Setup

Before deploying, you need to set up SSL certificates for `ai.cloudfuze.com`:

```bash
# SSH into the server
ssh user@64.227.160.206

# Install certbot if not already installed
sudo apt-get update
sudo apt-get install certbot

# Obtain Let's Encrypt certificate
sudo certbot certonly --standalone -d ai.cloudfuze.com

# The certificates will be stored at:
# /etc/letsencrypt/live/ai.cloudfuze.com/fullchain.pem
# /etc/letsencrypt/live/ai.cloudfuze.com/privkey.pem
```

## Step 2: Deploy Application

1. **Clone/Upload the code** to the server:
   ```bash
   # On your local machine, copy files to server
   scp -r . user@64.227.160.206:/path/to/app/
   ```

2. **SSH into the server**:
   ```bash
   ssh user@64.227.160.206
   cd /path/to/app
   ```

3. **Create/Update `.env` file** with all required environment variables:
   ```bash
   # Make sure all required variables are set:
   # OPENAI_API_KEY
   # MICROSOFT_CLIENT_ID
   # MICROSOFT_CLIENT_SECRET
   # MICROSOFT_TENANT
   # LANGFUSE_PUBLIC_KEY
   # LANGFUSE_SECRET_KEY
   # LANGFUSE_HOST
   # MONGODB_URL (REQUIRED - external MongoDB connection string)
   #   Examples:
   #   - MongoDB Atlas: mongodb+srv://username:password@cluster.mongodb.net/database
   #   - Remote MongoDB: mongodb://user:pass@host:27017/database
   # etc.
   ```

4. **Build and start the services**:
   ```bash
   # Stop any existing containers
   docker-compose -f docker-compose.ai-cloudfuze.yml down

   # Build and start
   docker-compose -f docker-compose.ai-cloudfuze.yml up -d --build

   # Check logs
   docker-compose -f docker-compose.ai-cloudfuze.yml logs -f
   ```

## Step 3: Verify Deployment

1. **Check health endpoint**:
   ```bash
   curl https://ai.cloudfuze.com/health
   ```

2. **Check readiness**:
   ```bash
   curl https://ai.cloudfuze.com/ready
   ```

3. **Access the application**:
   - Open browser: `https://ai.cloudfuze.com`
   - Should see the login page or main interface

## Step 4: SSL Certificate Auto-Renewal

Set up automatic renewal for Let's Encrypt certificates:

```bash
# Test renewal
sudo certbot renew --dry-run

# Add to crontab (runs twice daily)
sudo crontab -e
# Add this line:
0 0,12 * * * certbot renew --quiet
```

## Troubleshooting

### Nginx not starting
- Check if ports 80 and 443 are available: `sudo netstat -tulpn | grep :80`
- Check nginx logs: `docker logs slack2teams-nginx-ai-cloudfuze`
- Verify SSL certificate paths in `nginx-ai-cloudfuze.conf`

### Backend not responding
- Check backend logs: `docker logs slack2teams-backend-ai-cloudfuze`
- Verify environment variables in `.env` file
- **MongoDB connection**: Ensure `MONGODB_URL` is set correctly in `.env` file
  - For MongoDB Atlas: `mongodb+srv://username:password@cluster.mongodb.net/database`
  - For remote MongoDB: `mongodb://user:pass@host:27017/database`
  - Verify network connectivity to MongoDB server

### SSL Certificate Issues
- Verify certificate files exist: `ls -la /etc/letsencrypt/live/ai.cloudfuze.com/`
- Check certificate expiration: `sudo certbot certificates`
- Renew if needed: `sudo certbot renew`

### Port Conflicts
- If ports 80/443 are in use, you may need to stop other services
- Check what's using the ports: `sudo lsof -i :80` and `sudo lsof -i :443`

## Maintenance Commands

```bash
# View logs
docker-compose -f docker-compose.ai-cloudfuze.yml logs -f

# Restart services
docker-compose -f docker-compose.ai-cloudfuze.yml restart

# Stop services
docker-compose -f docker-compose.ai-cloudfuze.yml down

# Update and rebuild
docker-compose -f docker-compose.ai-cloudfuze.yml pull
docker-compose -f docker-compose.ai-cloudfuze.yml up -d --build

# View running containers
docker ps

# Check nginx configuration
docker exec slack2teams-nginx-ai-cloudfuze nginx -t
```

## File Structure

- `nginx-ai-cloudfuze.conf` - Nginx configuration for ai.cloudfuze.com
- `docker-compose.ai-cloudfuze.yml` - Docker Compose configuration for deployment
- `.env` - Environment variables (create this file with your secrets)

## Notes

- The nginx configuration includes HTTP to HTTPS redirect
- SSL certificates are mounted from `/etc/letsencrypt`
- Static files are served from `/var/www/html` in the container
- Backend API runs on port 8002 internally
- **MongoDB is external** - you must provide `MONGODB_URL` in your `.env` file
  - No local MongoDB container is started
  - Use MongoDB Atlas or any remote MongoDB instance

