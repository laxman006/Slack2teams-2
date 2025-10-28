#!/bin/bash
# Quick Start Script for Local Testing
# This script sets up and runs the application locally

set -e  # Exit on error

echo "=================================="
echo "CF Chatbot - Quick Start Script"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${YELLOW}💡 $1${NC}"
}

# Step 1: Check Python
echo "Step 1: Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
    print_success "Python 3 found: $(python3 --version)"
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
    print_success "Python found: $(python --version)"
else
    print_error "Python not found. Please install Python 3.8+"
    exit 1
fi

# Step 2: Check/Create virtual environment
echo ""
echo "Step 2: Setting up virtual environment..."
if [ ! -d "venv" ]; then
    print_info "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Step 3: Activate virtual environment
echo ""
echo "Step 3: Activating virtual environment..."
source venv/bin/activate
print_success "Virtual environment activated"

# Step 4: Install dependencies
echo ""
echo "Step 4: Installing dependencies..."
pip install --upgrade pip -q
pip install -r requirements.txt -q
print_success "Dependencies installed"

# Step 5: Check .env file
echo ""
echo "Step 5: Checking environment configuration..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        print_warning ".env file not found. Copying from .env.example..."
        cp .env.example .env
        print_info "Please edit .env file and add your credentials"
        print_info "Required: MICROSOFT_CLIENT_SECRET, OPENAI_API_KEY, LANGFUSE keys"
        echo ""
        echo "Press Enter when you've updated .env file..."
        read -r
    else
        print_error ".env.example not found. Please create .env file manually"
        exit 1
    fi
else
    print_success ".env file found"
fi

# Step 6: Run diagnostic tests
echo ""
echo "Step 6: Running diagnostic tests..."
$PYTHON_CMD test_auth.py

# Step 7: Check if MongoDB is needed
echo ""
echo "Step 7: Checking MongoDB..."
if command -v mongod &> /dev/null; then
    if pgrep -x "mongod" > /dev/null; then
        print_success "MongoDB is running"
    else
        print_warning "MongoDB is installed but not running"
        print_info "Starting MongoDB..."
        # Try to start MongoDB based on OS
        if [[ "$OSTYPE" == "darwin"* ]]; then
            brew services start mongodb-community || print_warning "Could not start MongoDB automatically"
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            sudo systemctl start mongod || print_warning "Could not start MongoDB automatically"
        fi
    fi
else
    print_warning "MongoDB not found. Will use JSON storage as fallback"
fi

# Step 8: Start backend server
echo ""
echo "Step 8: Starting backend server..."
print_info "Backend will run on http://localhost:8002"
print_info "Press Ctrl+C to stop the server"
echo ""

# Run the server
$PYTHON_CMD server.py




