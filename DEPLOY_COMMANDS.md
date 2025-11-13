# Deployment Commands for ai.cloudfuze.com

## Quick Deploy (Using Script)

```bash
# SSH into the server
ssh user@64.227.160.206

# Navigate to project directory (adjust path as needed)
cd /path/to/Slack2teams-2-confident-chatbot

# Make script executable
chmod +x deploy-ai-cloudfuze.sh

# Run deployment script
./deploy-ai-cloudfuze.sh
```

## Manual Deploy (Step by Step)

### 1. SSH into the server
```bash
ssh user@64.227.160.206
```

### 2. Navigate to project directory
```bash
cd /path/to/Slack2teams-2-confident-chatbot
# or wherever your project is located
```

### 3. Stop existing containers
```bash
# Stop any running containers (adjust compose file name if different)
docker-compose down
# or if using specific compose file:
docker-compose -f docker-compose.prod.yml down
```

### 4. Switch to the new branch and pull latest code
```bash
# Fetch latest changes
git fetch origin

# Switch to the branch
git checkout feature/unified-retrieval-langfuse-fixes

# Pull latest code
git pull origin feature/unified-retrieval-langfuse-fixes
```

### 5. Create/Update .env file
```bash
# Create or update .env file with your values
cat > .env << 'EOF'
OPENAI_API_KEY=your-openai-api-key-here
# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=your-microsoft-client-id-here
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret-here
MICROSOFT_TENANT=your-tenant-domain.com

# Langfuse Configuration for observability
LANGFUSE_PUBLIC_KEY=your-langfuse-public-key-here
LANGFUSE_SECRET_KEY=your-langfuse-secret-key-here
LANGFUSE_HOST=https://cloud.langfuse.com

# MongoDB Configuration
MONGODB_URL=your-mongodb-connection-string-here
MONGODB_DATABASE=slack2teams
MONGODB_CHAT_COLLECTION=chat_histories

INITIALIZE_VECTORSTORE=false
ENABLE_WEB_SOURCE=false
ENABLE_SHAREPOINT_SOURCE=false
EOF
```

### 6. Build and start services
```bash
# Build and start with the new docker-compose file
docker-compose -f docker-compose.ai-cloudfuze.yml up -d --build
```

### 7. Check deployment status
```bash
# View running containers
docker-compose -f docker-compose.ai-cloudfuze.yml ps

# View logs
docker-compose -f docker-compose.ai-cloudfuze.yml logs -f

# Check health endpoint
curl http://localhost/health

# Check readiness
curl http://localhost/ready
```

## Verification Commands

```bash
# Check if containers are running
docker ps | grep slack2teams

# Check nginx configuration
docker exec slack2teams-nginx-ai-cloudfuze nginx -t

# View backend logs
docker logs slack2teams-backend-ai-cloudfuze -f

# View nginx logs
docker logs slack2teams-nginx-ai-cloudfuze -f

# Test from outside (if domain is configured)
curl https://ai.cloudfuze.com/health
```

## Troubleshooting

### If containers fail to start:
```bash
# Check logs for errors
docker-compose -f docker-compose.ai-cloudfuze.yml logs

# Check if ports are in use
sudo netstat -tulpn | grep :80
sudo netstat -tulpn | grep :443

# Restart services
docker-compose -f docker-compose.ai-cloudfuze.yml restart
```

### If you need to rollback:
```bash
# Stop current containers
docker-compose -f docker-compose.ai-cloudfuze.yml down

# Switch back to previous branch
git checkout <previous-branch>

# Start previous version
docker-compose -f docker-compose.prod.yml up -d
```

## Important Notes

1. **SSL Certificates**: Make sure SSL certificates are set up for `ai.cloudfuze.com` before deploying
2. **Environment Variables**: The `.env` file contains sensitive data - ensure it's not committed to git
3. **MongoDB**: The configuration uses external MongoDB (MongoDB Atlas) - no local MongoDB container
4. **Port Conflicts**: If ports 80/443 are in use, stop other services first

