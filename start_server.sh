#!/bin/bash

# Slack2teams Server Startup Script
# This script handles port conflicts and starts the server cleanly

echo "🚀 Starting Slack2teams Server..."

# Check if port 8002 is in use
if lsof -i :8002 > /dev/null 2>&1; then
    echo "⚠️  Port 8002 is already in use. Stopping existing processes..."
    
    # Kill any processes using port 8002
    lsof -ti :8002 | xargs kill -9 2>/dev/null
    
    # Wait a moment for the port to be released
    sleep 2
    
    # Verify port is free
    if lsof -i :8002 > /dev/null 2>&1; then
        echo "❌ Failed to free port 8002. Please check manually."
        exit 1
    else
        echo "✅ Port 8002 is now free."
    fi
else
    echo "✅ Port 8002 is available."
fi

# Start the server
echo "🎯 Starting server on port 8002..."
python3 server.py
