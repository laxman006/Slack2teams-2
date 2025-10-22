@echo off
echo 🚀 Starting Slack2Teams Docker Deployment...

REM Check if Docker is installed
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker is not installed. Please install Docker first.
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Docker Compose is not installed. Please install Docker Compose first.
    exit /b 1
)

REM Check if .env file exists
if not exist .env (
    echo [WARNING] .env file not found. Creating from template...
    (
        echo # OpenAI API Key - Get your key from https://platform.openai.com/api-keys
        echo OPENAI_API_KEY=your_openai_api_key_here
        echo.
        echo # Microsoft OAuth Configuration
        echo MICROSOFT_CLIENT_ID=your_microsoft_client_id_here
        echo MICROSOFT_CLIENT_SECRET=your_microsoft_client_secret_here
        echo MICROSOFT_TENANT=your_microsoft_tenant_id_here
        echo.
        echo # Langfuse configuration for observability
        echo LANGFUSE_PUBLIC_KEY=your_langfuse_public_key_here
        echo LANGFUSE_SECRET_KEY=your_langfuse_secret_key_here
        echo LANGFUSE_HOST=http://localhost:3100
        echo.
        echo # JSON Memory Storage Configuration
        echo JSON_MEMORY_FILE=data/chat_history.json
    ) > .env
    echo [WARNING] Please update the .env file with your actual API keys before running again.
    exit /b 1
)

REM Stop existing containers
echo [INFO] Stopping existing containers...
docker-compose down

REM Build and start services
echo [INFO] Building and starting services...
docker-compose up --build -d

REM Wait for services to be ready
echo [INFO] Waiting for services to start...
timeout /t 10 /nobreak >nul

REM Check if services are running
echo [INFO] Checking service health...

REM Check backend health
curl -f http://localhost:8002/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Backend service is healthy
) else (
    echo [ERROR] Backend service is not responding
    docker-compose logs backend
    exit /b 1
)

REM Check nginx health
curl -f http://localhost/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [SUCCESS] Nginx service is healthy
) else (
    echo [ERROR] Nginx service is not responding
    docker-compose logs nginx
    exit /b 1
)

echo [SUCCESS] 🎉 Deployment completed successfully!
echo.
echo 📱 Your application is now available at:
echo    🌐 Frontend: http://localhost
echo    🔧 Backend API: http://localhost:8002
echo    📊 API Docs: http://localhost:8002/docs
echo.
echo 🔍 To view logs:
echo    docker-compose logs -f
echo.
echo 🛑 To stop services:
echo    docker-compose down
echo.
echo 🔄 To restart services:
echo    docker-compose restart
