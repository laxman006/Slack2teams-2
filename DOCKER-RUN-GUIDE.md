# Docker Run Guide

## Quick Start

### 1. Create Environment File
Create a `.env` file with your configuration:

```bash
# Required
OPENAI_API_KEY=your_openai_api_key_here
MICROSOFT_CLIENT_ID=your_microsoft_client_id
MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret
MICROSOFT_TENANT=common

# Optional
LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
LANGFUSE_SECRET_KEY=your_langfuse_secret_key
LANGFUSE_HOST=http://localhost:3100

# MongoDB (uses local MongoDB container by default)
MONGODB_URL=mongodb://mongodb:27017
MONGODB_DATABASE=slack2teams
MONGODB_CHAT_COLLECTION=chat_histories

# Alternative: Use MongoDB Atlas (Cloud)
# MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/
```

### 2. Run with Docker Compose

**Basic setup (Backend + MongoDB + Nginx):**
```bash
docker-compose up -d
```

**With observability (includes Langfuse):**
```bash
docker-compose --profile observability up -d
```

### 3. Access Your Application

- **Frontend**: http://localhost
- **Backend API**: http://localhost:8002
- **API Docs**: http://localhost:8002/docs
- **Health Check**: http://localhost/health

## Services

### Backend Service
- **Container**: `slack2teams-backend`
- **Port**: 8002
- **Health Check**: Built-in

### MongoDB Service
- **Container**: `slack2teams-mongodb`
- **Port**: 27017
- **Data**: Persistent volume `mongodb_data`

### Nginx Service
- **Container**: `slack2teams-nginx`
- **Ports**: 80, 443
- **Purpose**: Reverse proxy and static file serving

### Langfuse Service (Optional)
- **Container**: `slack2teams-langfuse`
- **Port**: 3100
- **Purpose**: Observability and monitoring

## Commands

### Start Services
```bash
# Start all services
docker-compose up -d

# Start with logs
docker-compose up

# Start specific services
docker-compose up -d backend mongodb nginx
```

### Stop Services
```bash
# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f mongodb
```

### Health Checks
```bash
# Check service status
docker-compose ps

# Check health
curl http://localhost/health
curl http://localhost:8002/health
```

## Troubleshooting

### MongoDB Connection Issues
```bash
# Check MongoDB logs
docker-compose logs mongodb

# Connect to MongoDB
docker exec -it slack2teams-mongodb mongosh
```

### Backend Issues
```bash
# Check backend logs
docker-compose logs backend

# Restart backend
docker-compose restart backend
```

### Port Conflicts
If ports are already in use:
```bash
# Check what's using the ports
netstat -tulpn | grep :8002
netstat -tulpn | grep :27017
netstat -tulpn | grep :80

# Stop conflicting services or change ports in docker-compose.yml
```

## Production Deployment

For production, use `docker-compose.prod.yml`:

```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key | Required |
| `MICROSOFT_CLIENT_ID` | Microsoft OAuth client ID | Required |
| `MICROSOFT_CLIENT_SECRET` | Microsoft OAuth client secret | Required |
| `MONGODB_URL` | MongoDB connection string | `mongodb://mongodb:27017` |
| `MONGODB_DATABASE` | MongoDB database name | `slack2teams` |
| `MONGODB_CHAT_COLLECTION` | MongoDB collection name | `chat_histories` |
| `LANGFUSE_HOST` | Langfuse server URL | `http://localhost:3100` |

## Data Persistence

- **MongoDB Data**: Stored in `mongodb_data` volume
- **Application Data**: Stored in `./data` directory (mounted as volume)
- **Images**: Stored in `./images` directory (mounted as volume)

## Security Notes

- The application runs as a non-root user inside the container
- MongoDB is only accessible from within the Docker network
- Use environment variables for sensitive data
- For production, consider using Docker secrets
