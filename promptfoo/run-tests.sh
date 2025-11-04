#!/bin/bash

echo "========================================"
echo "CloudFuze Chatbot - Promptfoo Tests"
echo "========================================"
echo ""
echo "Checking if server is running..."
if ! curl -s http://localhost:8002/health > /dev/null 2>&1; then
    echo "[ERROR] FastAPI server is not running!"
    echo "Please start the server first: python server.py"
    echo ""
    exit 1
fi
echo "[OK] Server is running"
echo ""
echo "Starting promptfoo tests..."
cd "$(dirname "$0")"
npx promptfoo eval -c promptfooconfig.yaml
echo ""
echo "========================================"
echo "Tests complete! Opening results viewer..."
echo "========================================"
npx promptfoo view



