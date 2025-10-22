#!/bin/bash

# Slack2Teams Docker Deployment Script
echo "🚀 Starting Slack2Teams Docker Deployment..."

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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    cat > .env << EOF
# OpenAI API Key - Get your key from https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=your_microsoft_client_id_here
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret_here
MICROSOFT_TENANT=your_microsoft_tenant_id_here

# Langfuse configuration for observability
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key_here
LANGFUSE_SECRET_KEY=your_langfuse_secret_key_here
LANGFUSE_HOST=http://localhost:3100

# JSON Memory Storage Configuration
JSON_MEMORY_FILE=data/chat_history.json
EOF
    print_warning "Please update the .env file with your actual API keys before running again."
    exit 1
fi

# Stop existing containers
print_status "Stopping existing containers..."
docker-compose down

# Remove old images (optional)
if [ "$1" = "--clean" ]; then
    print_status "Cleaning up old images..."
    docker-compose down --rmi all
fi

# Build and start services
print_status "Building and starting services..."
docker-compose up --build -d

# Wait for services to be ready
print_status "Waiting for services to start..."
sleep 10

# Check if services are running
print_status "Checking service health..."

# Check backend health
if curl -f http://localhost:8002/health > /dev/null 2>&1; then
    print_success "Backend service is healthy"
else
    print_error "Backend service is not responding"
    docker-compose logs backend
    exit 1
fi

# Check nginx health
if curl -f http://localhost/health > /dev/null 2>&1; then
    print_success "Nginx service is healthy"
else
    print_error "Nginx service is not responding"
    docker-compose logs nginx
    exit 1
fi

print_success "🎉 Deployment completed successfully!"
echo ""
echo "📱 Your application is now available at:"
echo "   🌐 Frontend: http://localhost"
echo "   🔧 Backend API: http://localhost:8002"
echo "   📊 API Docs: http://localhost:8002/docs"
echo ""
echo "🔍 To view logs:"
echo "   docker-compose logs -f"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose down"
echo ""
echo "🔄 To restart services:"
echo "   docker-compose restart"
