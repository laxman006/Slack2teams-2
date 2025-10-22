# Slack2Teams Docker Deployment

This document provides instructions for deploying the Slack2Teams migration chatbot using Docker with Python 3.13.5.

## 🐳 Docker Architecture

The application is containerized with the following services:

- **Backend**: FastAPI application with Python 3.13.5
- **Nginx**: Reverse proxy and static file server
- **Optional**: Langfuse for observability (with PostgreSQL)

## 📋 Prerequisites

- Docker Desktop installed and running
- Docker Compose v2.0+
- Valid API keys (OpenAI, Microsoft OAuth, Langfuse)

## 🚀 Quick Start

### 1. Environment Setup

Ensure your `.env` file contains the required environment variables:

```bash
# OpenAI API Key
OPENAI_API_KEY=your_openai_api_key_here

# Microsoft OAuth Configuration
MICROSOFT_CLIENT_ID=63bd4522-368b-4bd7-a84d-9c7f205cd2a6
MICROSOFT_CLIENT_SECRET=g-C8Q~ZCcJmuHOt~wEJinGVfiZGYd9gzEy6Wfb5Y
MICROSOFT_TENANT=c9b18954-8964-4212-8168-f54fa673490b

# Langfuse configuration
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key_here
LANGFUSE_SECRET_KEY=your_langfuse_secret_key_here
LANGFUSE_HOST=http://localhost:3100

# JSON Memory Storage
JSON_MEMORY_FILE=data/chat_history.json
```

### 2. Deploy with Docker Compose

#### Windows:
```cmd
deploy.bat
```

#### Linux/macOS:
```bash
chmod +x deploy.sh
./deploy.sh
```

#### Manual deployment:
```bash
# Build and start services
docker-compose up --build -d

# Check service status
docker-compose ps

# View logs
docker-compose logs -f
```

## 🌐 Access Points

After successful deployment:

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8002
- **API Documentation**: http://localhost:8002/docs
- **Health Check**: http://localhost/health

## 🔧 Management Commands

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f nginx
```

### Restart Services
```bash
# All services
docker-compose restart

# Specific service
docker-compose restart backend
```

### Stop Services
```bash
docker-compose down
```

### Clean Deployment (remove images)
```bash
docker-compose down --rmi all
```

## 📊 Optional: Langfuse Observability

To enable Langfuse for observability and monitoring:

```bash
# Start with Langfuse
docker-compose --profile observability up -d

# Access Langfuse UI
open http://localhost:3100
```

## 🏗️ Docker Configuration Details

### Backend Service
- **Base Image**: Python 3.13.5-slim
- **Port**: 8002
- **Health Check**: `/health` endpoint
- **Security**: Non-root user execution
- **Volumes**: Persistent data storage

### Nginx Service
- **Base Image**: nginx:alpine
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Features**: 
  - Gzip compression
  - Security headers
  - Static file caching
  - WebSocket support
  - Streaming support for chat

### Network Configuration
- **Internal Network**: Docker Compose default network
- **Service Discovery**: Services communicate via service names
- **External Access**: Nginx proxy handles all external traffic

## 🔍 Troubleshooting

### Common Issues

1. **Port Conflicts**
   ```bash
   # Check if ports are in use
   netstat -an | findstr :80
   netstat -an | findstr :8002
   ```

2. **Environment Variables**
   ```bash
   # Verify .env file exists and has correct values
   cat .env
   ```

3. **Container Health**
   ```bash
   # Check container status
   docker-compose ps
   
   # Check health status
   docker inspect slack2teams-backend | grep -A 10 Health
   ```

4. **Logs Analysis**
   ```bash
   # Backend logs
   docker-compose logs backend
   
   # Nginx logs
   docker-compose logs nginx
   ```

### Performance Optimization

1. **Resource Limits**
   ```yaml
   # Add to docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 2G
         cpus: '1.0'
   ```

2. **Volume Optimization**
   ```bash
   # Use named volumes for better performance
   docker volume create slack2teams_data
   ```

## 🔒 Security Considerations

- Non-root user execution in containers
- Security headers via Nginx
- Environment variable isolation
- Network isolation between services
- Regular image updates recommended

## 📈 Monitoring

### Health Checks
- Backend: `GET /health`
- Nginx: `GET /health` (proxied to backend)

### Metrics
- Container resource usage: `docker stats`
- Application logs: `docker-compose logs`
- Langfuse observability (if enabled)

## 🚀 Production Deployment

For production deployment:

1. **Use HTTPS**: Configure SSL certificates
2. **Environment Variables**: Use secure secret management
3. **Resource Limits**: Set appropriate CPU/memory limits
4. **Monitoring**: Enable comprehensive logging and monitoring
5. **Backup**: Regular data volume backups
6. **Updates**: Regular security updates

## 📝 Development

### Local Development with Docker
```bash
# Development mode with volume mounts
docker-compose -f docker-compose.dev.yml up -d
```

### Building Custom Images
```bash
# Build backend image
docker build -t slack2teams-backend:custom .

# Build with specific tag
docker build -t slack2teams-backend:v1.0.0 .
```

## 🤝 Support

For issues or questions:
1. Check the logs: `docker-compose logs`
2. Verify environment variables
3. Check Docker Desktop is running
4. Ensure ports are not in use by other services
