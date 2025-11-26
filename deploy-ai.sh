#!/bin/bash

# Deployment Script for ai.cloudfuze.com (64.227.160.206)
# This script deploys the CF_Chatbot-V1 branch with frontend

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}AI.CloudFuze.com Deployment${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Configuration
SERVER_IP="64.227.160.206"
SERVER_USER="root"
DOMAIN="ai.cloudfuze.com"
PROJECT_DIR="/opt/slack2teams-ai"
BRANCH="CF_Chatbot-V1"
FRONTEND_IMAGE="laxman006/slack2teams-frontend:ai"

# Step 1: Build and push frontend Docker image locally
echo -e "${YELLOW}Step 1: Building frontend Docker image...${NC}"
cd frontend
docker build -f Dockerfile.frontend -t ${FRONTEND_IMAGE} \
  --build-arg NEXT_PUBLIC_API_URL=https://${DOMAIN} .
echo -e "${GREEN}✓ Frontend image built${NC}"

echo -e "${YELLOW}Step 2: Pushing frontend image to Docker Hub...${NC}"
docker push ${FRONTEND_IMAGE}
echo -e "${GREEN}✓ Frontend image pushed${NC}"
cd ..

# Step 2: Prepare server
echo -e "${YELLOW}Step 3: Preparing server...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
# Stop old services
echo "Stopping old services..."
cd /opt/slack2teams 2>/dev/null && docker-compose down || true
cd /opt/slack2teams-prod 2>/dev/null && docker-compose down || true

# Create project directory
echo "Creating project directory..."
mkdir -p /opt/slack2teams-ai
cd /opt/slack2teams-ai

# Update system
echo "Updating system packages..."
apt-get update
apt-get install -y docker.io docker-compose git curl

# Ensure Docker is running
systemctl start docker
systemctl enable docker
ENDSSH
echo -e "${GREEN}✓ Server prepared${NC}"

# Step 3: Clone repository and setup
echo -e "${YELLOW}Step 4: Setting up repository on server...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << ENDSSH
cd /opt/slack2teams-ai

# Remove old repo if exists
if [ -d ".git" ]; then
    echo "Removing old repository..."
    rm -rf .git
fi

# Clone repository
echo "Cloning repository..."
git clone -b ${BRANCH} https://github.com/laxman006/chatbot.git .

# Pull latest changes
git pull origin ${BRANCH}

echo "Repository setup complete!"
ENDSSH
echo -e "${GREEN}✓ Repository cloned${NC}"

# Step 4: Copy environment file
echo -e "${YELLOW}Step 5: Setting up environment variables...${NC}"
echo -e "${RED}IMPORTANT: You need to manually create .env.ai on the server${NC}"
echo -e "${YELLOW}The file should contain all your production API keys and configs${NC}"
echo ""
read -p "Press Enter after you've created .env.ai on the server..."

# Step 5: Pull frontend image on server
echo -e "${YELLOW}Step 6: Pulling frontend image on server...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << ENDSSH
cd /opt/slack2teams-ai
docker pull ${FRONTEND_IMAGE}
ENDSSH
echo -e "${GREEN}✓ Frontend image pulled${NC}"

# Step 6: Setup SSL Certificate
echo -e "${YELLOW}Step 7: Setting up SSL certificate...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << ENDSSH
# Install certbot if not present
if ! command -v certbot &> /dev/null; then
    apt-get install -y certbot python3-certbot-nginx
fi

# Get SSL certificate
certbot certonly --standalone -d ${DOMAIN} --agree-tos --non-interactive --email admin@cloudfuze.com || true
ENDSSH
echo -e "${GREEN}✓ SSL certificate configured${NC}"

# Step 7: Deploy services
echo -e "${YELLOW}Step 8: Deploying services...${NC}"
ssh ${SERVER_USER}@${SERVER_IP} << 'ENDSSH'
cd /opt/slack2teams-ai

# Stop any running containers
docker-compose -f docker-compose.ai.yml down 2>/dev/null || true

# Start services with environment file
docker-compose -f docker-compose.ai.yml --env-file .env.ai up -d

# Wait for services to start
echo "Waiting for services to start..."
sleep 30

# Check service status
echo ""
echo "Service Status:"
docker-compose -f docker-compose.ai.yml ps

# Check health
echo ""
echo "Backend Health:"
curl -s http://localhost:8002/health || echo "Backend not ready yet"

echo ""
echo "Frontend Status:"
docker logs slack2teams-frontend-ai --tail 5
ENDSSH
echo -e "${GREEN}✓ Services deployed${NC}"

# Step 8: Final verification
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Deployment Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo -e "URLs:"
echo -e "  Frontend: https://${DOMAIN}/"
echo -e "  Backend Health: https://${DOMAIN}/api/health"
echo -e "  Auth Config: https://${DOMAIN}/auth/config"
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo -e "1. Test the application: https://${DOMAIN}"
echo -e "2. Add redirect URLs to Microsoft App Registration:"
echo -e "   - https://${DOMAIN}/api/auth/callback"
echo -e "   - https://${DOMAIN}/"
echo -e "3. Monitor logs: ssh ${SERVER_USER}@${SERVER_IP} 'cd ${PROJECT_DIR} && docker-compose -f docker-compose.ai.yml logs -f'"
echo ""

