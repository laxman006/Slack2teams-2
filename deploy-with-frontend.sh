#!/bin/bash

# ============================================
# COMPLETE DEPLOYMENT SCRIPT WITH NEXT.JS FRONTEND
# For: newcf3.cloudfuze.com
# ============================================

set -e  # Exit on any error

echo "🚀 Starting Complete Deployment with Next.js Frontend..."
echo "========================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Step 1: Verify we're in the correct directory
print_status "Verifying deployment directory..."
if [ ! -f "docker-compose.prod.yml" ]; then
    print_error "docker-compose.prod.yml not found! Are you in the correct directory?"
    exit 1
fi
print_success "Found docker-compose.prod.yml"

# Step 2: Check if .env.prod exists
print_status "Checking .env.prod configuration..."
if [ ! -f ".env.prod" ]; then
    print_error ".env.prod not found! Please create it first."
    exit 1
fi
print_success ".env.prod found"

# Step 3: Verify frontend Dockerfile exists
print_status "Checking frontend Dockerfile..."
if [ ! -f "frontend/Dockerfile.frontend" ]; then
    print_error "frontend/Dockerfile.frontend not found!"
    exit 1
fi
print_success "Frontend Dockerfile found"

# Step 4: Create frontend .env.production if it doesn't exist
print_status "Creating frontend environment file..."
cat > frontend/.env.production << 'EOF'
# Frontend Production Environment Variables
NEXT_PUBLIC_API_URL=https://newcf3.cloudfuze.com
EOF
print_success "Frontend environment file created"

# Step 5: Stop any existing containers
print_status "Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down 2>/dev/null || true
print_success "Existing containers stopped"

# Step 6: Remove old images (optional - uncomment if you want fresh builds)
# print_status "Removing old images..."
# docker-compose -f docker-compose.prod.yml down --rmi all

# Step 7: Build and start all services (backend + frontend + nginx)
print_status "Building and starting all services..."
print_warning "This may take 5-10 minutes for first build..."
docker-compose -f docker-compose.prod.yml --env-file .env.prod up --build -d

# Step 8: Wait for services to initialize
print_status "Waiting for services to initialize..."
sleep 45

# Step 9: Check service status
print_status "Checking service status..."
docker-compose -f docker-compose.prod.yml ps

# Step 10: Health checks
print_status "Running health checks..."

# Check backend
print_status "Checking backend health..."
sleep 5
if curl -f -s http://localhost:8002/health > /dev/null 2>&1; then
    print_success "✅ Backend is healthy"
else
    print_warning "⚠️  Backend health check failed (may still be starting)"
fi

# Check frontend
print_status "Checking frontend health..."
sleep 5
if curl -f -s http://localhost:3000 > /dev/null 2>&1; then
    print_success "✅ Frontend is healthy"
else
    print_warning "⚠️  Frontend health check failed (may still be starting)"
fi

# Check nginx
print_status "Checking nginx..."
if curl -f -s http://localhost/ > /dev/null 2>&1; then
    print_success "✅ Nginx is healthy"
else
    print_warning "⚠️  Nginx health check failed"
fi

# Step 11: Show logs
print_status "Recent logs from all services..."
docker-compose -f docker-compose.prod.yml logs --tail=20

# Step 12: Final summary
echo ""
echo "========================================================"
print_success "🎉 Deployment Complete!"
echo "========================================================"
echo ""
echo "📋 Service Status:"
docker-compose -f docker-compose.prod.yml ps
echo ""
echo "🌐 Access Points:"
echo "   Frontend:  http://localhost (Next.js)"
echo "   Backend:   http://localhost:8002 (FastAPI)"
echo "   API Docs:  http://localhost:8002/docs"
echo ""
echo "📝 Useful Commands:"
echo "   View logs:         docker-compose -f docker-compose.prod.yml logs -f"
echo "   View backend logs: docker-compose -f docker-compose.prod.yml logs -f backend"
echo "   View frontend logs:docker-compose -f docker-compose.prod.yml logs -f frontend"
echo "   Restart services:  docker-compose -f docker-compose.prod.yml restart"
echo "   Stop services:     docker-compose -f docker-compose.prod.yml down"
echo ""
print_warning "Next Steps:"
echo "   1. Check logs if any service shows 'unhealthy'"
echo "   2. Access https://newcf3.cloudfuze.com to test"
echo "   3. Verify login functionality"
echo "   4. Test chat features"
echo ""
print_success "Happy deploying! 🚀"

