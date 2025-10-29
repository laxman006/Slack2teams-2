#!/bin/bash

# Production Environment Verification Script
# Checks if environment variables are correctly loaded in production

echo "=========================================="
echo "PRODUCTION ENVIRONMENT VERIFICATION"
echo "=========================================="
echo ""

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo "❌ ERROR: .env.prod file not found!"
    echo "   Create .env.prod with your production credentials"
    exit 1
else
    echo "✅ .env.prod file exists"
fi

# Load environment variables
export $(cat .env.prod | grep -v '^#' | xargs)

echo ""
echo "Checking critical environment variables:"
echo ""

# Function to check env var
check_env_var() {
    local var_name=$1
    local var_value="${!var_name}"
    
    if [ -z "$var_value" ]; then
        echo "❌ $var_name: NOT SET"
        return 1
    else
        # Show first 50 chars for long values
        local display_value="${var_value:0:50}"
        if [ ${#var_value} -gt 50 ]; then
            display_value="${display_value}..."
        fi
        echo "✅ $var_name: $display_value"
        return 0
    fi
}

# Check all required variables
errors=0

check_env_var "OPENAI_API_KEY" || ((errors++))
check_env_var "MICROSOFT_CLIENT_ID" || ((errors++))
check_env_var "MICROSOFT_CLIENT_SECRET" || ((errors++))
check_env_var "MICROSOFT_TENANT" || ((errors++))
check_env_var "LANGFUSE_PUBLIC_KEY" || ((errors++))
check_env_var "LANGFUSE_SECRET_KEY" || ((errors++))
check_env_var "LANGFUSE_HOST" || ((errors++))
check_env_var "MONGODB_URL" || ((errors++))
check_env_var "MONGODB_DATABASE" || ((errors++))
check_env_var "MONGODB_VECTORSTORE_COLLECTION" || ((errors++))
check_env_var "VECTORSTORE_BACKEND" || ((errors++))

echo ""
echo "=========================================="
echo "MONGODB ATLAS CONFIGURATION CHECK"
echo "=========================================="

# Check if MongoDB URL is Atlas or localhost
if [[ "$MONGODB_URL" == *"mongodb+srv://"* ]] || [[ "$MONGODB_URL" == *"mongodb.net"* ]]; then
    echo "✅ MongoDB Atlas connection detected"
    echo "   Using cloud database (correct for production)"
else
    echo "⚠️  WARNING: Not using MongoDB Atlas!"
    echo "   Current: $MONGODB_URL"
    if [[ "$MONGODB_URL" == *"localhost"* ]]; then
        echo "   ❌ ERROR: Using localhost MongoDB"
        echo "   This will NOT work in production!"
        echo "   Update MONGODB_URL to your Atlas connection string"
        ((errors++))
    fi
fi

# Check Langfuse host
if [[ "$LANGFUSE_HOST" == *"cloud.langfuse.com"* ]]; then
    echo "✅ Langfuse cloud host configured correctly"
else
    echo "⚠️  Langfuse host: $LANGFUSE_HOST"
    echo "   Should be: https://cloud.langfuse.com for production"
fi

echo ""
echo "=========================================="
echo "VECTORSTORE CONFIGURATION"
echo "=========================================="

echo "Backend: $VECTORSTORE_BACKEND"
echo "Collection: $MONGODB_VECTORSTORE_COLLECTION"
echo "Database: $MONGODB_DATABASE"

if [ "$VECTORSTORE_BACKEND" != "mongodb" ]; then
    echo "⚠️  WARNING: Vectorstore backend is not 'mongodb'"
    echo "   Current value: $VECTORSTORE_BACKEND"
    echo "   Should be: mongodb (for production)"
fi

echo ""
echo "=========================================="
echo "SUMMARY"
echo "=========================================="

if [ $errors -eq 0 ]; then
    echo "✅ All checks passed!"
    echo "   Environment is ready for production deployment"
    echo ""
    echo "Next steps:"
    echo "  1. docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d --build"
    echo "  2. docker-compose -f docker-compose.prod.yml logs -f backend"
    exit 0
else
    echo "❌ Found $errors error(s)"
    echo "   Fix the errors above before deploying"
    exit 1
fi

