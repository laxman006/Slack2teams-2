#!/bin/bash

echo "🔄 Restarting CloudFuze services to apply nginx configuration fixes..."

# Stop all services
echo "⏹️ Stopping services..."
docker-compose down

# Rebuild nginx container to apply new configuration
echo "🔨 Rebuilding nginx container..."
docker-compose build nginx

# Start services
echo "🚀 Starting services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Check service health
echo "🔍 Checking service health..."
docker-compose ps

echo "✅ Services restarted! The 405 error should now be fixed."
echo "🌐 You can now test the login at: https://ai.cloudfuze.com/login.html"
