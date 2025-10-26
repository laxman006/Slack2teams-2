# Vectorstore Management Guide

## Problem
The chatbot automatically loads blog content every time it starts, costing $16-20 in OpenAI API calls. This happens because the vectorstore initialization runs automatically when the Docker container starts.

## Solution
We've added an environment variable `INITIALIZE_VECTORSTORE` that controls whether the vectorstore should be initialized on startup. This gives you complete control over when the expensive blog content loading happens.

## How It Works Now

### Environment Variable Control

Set `INITIALIZE_VECTORSTORE` in your environment:

- **`INITIALIZE_VECTORSTORE=false`** (Default): No automatic initialization, no costs
- **`INITIALIZE_VECTORSTORE=true`**: Automatic initialization with smart rebuild detection

### 1. **Default Behavior (No Cost)**
- `INITIALIZE_VECTORSTORE=false` (default)
- Docker container starts without loading blog content
- Application runs but has no knowledge base
- No API costs during startup

### 2. **Automatic Initialization (When Enabled)**
- `INITIALIZE_VECTORSTORE=true`
- Checks if rebuild is needed (smart detection)
- Only rebuilds if content has changed
- Full knowledge base available immediately

## Usage Examples

### Development (No Costs)
```bash
# Set in your .env file or environment
INITIALIZE_VECTORSTORE=false

# Start Docker
docker-compose up -d
# No API costs, starts quickly
```

### Production (With Knowledge Base)
```bash
# Set in your .env file or environment
INITIALIZE_VECTORSTORE=true

# Start Docker
docker-compose up -d
# Will check if rebuild needed, only rebuilds if content changed
```

### Docker Compose Override
```yaml
# docker-compose.override.yml
services:
  backend:
    environment:
      - INITIALIZE_VECTORSTORE=true
```

## Cost Control

### Before (Automatic)
- ❌ Every Docker restart = $16-20
- ❌ No control over when loading happens
- ❌ Expensive for development/testing

### After (Manual)
- ✅ Docker restart = $0
- ✅ You control when to load content
- ✅ Perfect for development/testing
- ✅ Only pay when you need fresh content

## When to Rebuild

### Rebuild When:
- ✅ New blog posts published
- ✅ Content updates on CloudFuze website
- ✅ You want fresh knowledge base
- ✅ After significant content changes

### Don't Rebuild When:
- ❌ Just restarting Docker
- ❌ Code changes (no content changes)
- ❌ Development/testing
- ❌ No new content published

## API Endpoints

### Check Status
```
GET /admin/vectorstore-status
```
Returns:
- Whether vectorstore exists
- Document count
- Last update timestamp
- Metadata information

### Rebuild Vectorstore
```
POST /admin/rebuild-vectorstore
```
Returns:
- Success/error status
- Total documents processed
- Timestamp of rebuild

## Docker Usage

### Start Without Vectorstore
```bash
docker-compose up -d
# No API costs, starts quickly
```

### Check Status
```bash
docker exec -it slack2teams-backend python manage_vectorstore.py status
```

### Load Content When Ready
```bash
docker exec -it slack2teams-backend python manage_vectorstore.py rebuild
```

## Development Workflow

1. **Start Docker**: `docker-compose up -d` (no cost)
2. **Develop/Test**: Make changes, test functionality
3. **Load Content**: Only when you need fresh blog content
4. **Deploy**: Load content once in production

## Production Deployment

1. Deploy application without vectorstore
2. Check status: `GET /admin/vectorstore-status`
3. Load content once: `POST /admin/rebuild-vectorstore`
4. Monitor and reload only when content changes

## Troubleshooting

### No Knowledge Base
- Chat will work but with limited context
- Use `/admin/vectorstore-status` to check
- Rebuild when needed

### Failed Rebuild
- Check OpenAI API key
- Check network connectivity
- Check CloudFuze blog URL accessibility

### High Costs
- Only rebuild when content actually changes
- Use status endpoint to check if rebuild is needed
- Monitor API usage in OpenAI dashboard

## Benefits

- 💰 **Cost Control**: Only pay when you need fresh content
- ⚡ **Fast Startup**: Docker starts quickly without API calls
- 🔧 **Development Friendly**: No costs during development
- 📊 **Transparency**: Clear status and control over loading
- 🚀 **Production Ready**: Load content once, use many times
