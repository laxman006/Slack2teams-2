#!/bin/bash

# Deployment script for ai.cloudfuze.com
# Branch: feature/unified-retrieval-langfuse-fixes

set -e  # Exit on error

echo "=========================================="
echo "Deploying to ai.cloudfuze.com"
echo "Branch: feature/unified-retrieval-langfuse-fixes"
echo "=========================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env file exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}Creating .env file...${NC}"
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
    echo -e "${GREEN}.env file created${NC}"
else
    echo -e "${YELLOW}.env file already exists. Please update it manually if needed.${NC}"
fi

# Stop existing containers
echo -e "${YELLOW}Stopping existing containers...${NC}"
docker-compose -f docker-compose.ai-cloudfuze.yml down 2>/dev/null || true

# Pull latest code from the branch
echo -e "${YELLOW}Pulling latest code from feature/unified-retrieval-langfuse-fixes...${NC}"
git fetch origin
git checkout feature/unified-retrieval-langfuse-fixes
git pull origin feature/unified-retrieval-langfuse-fixes

# Build and start services
echo -e "${YELLOW}Building and starting services...${NC}"
docker-compose -f docker-compose.ai-cloudfuze.yml up -d --build

# Wait for services to start
echo -e "${YELLOW}Waiting for services to start...${NC}"
sleep 10

# Check service status
echo -e "${YELLOW}Checking service status...${NC}"
docker-compose -f docker-compose.ai-cloudfuze.yml ps

# Check health
echo -e "${YELLOW}Checking health endpoint...${NC}"
sleep 5
curl -f http://localhost/health || echo -e "${RED}Health check failed${NC}"

echo -e "${GREEN}=========================================="
echo "Deployment completed!"
echo "==========================================${NC}"
echo ""
echo "View logs with:"
echo "  docker-compose -f docker-compose.ai-cloudfuze.yml logs -f"
echo ""
echo "Check status with:"
echo "  docker-compose -f docker-compose.ai-cloudfuze.yml ps"
echo ""

