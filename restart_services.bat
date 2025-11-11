@echo off
echo 🔄 Restarting CloudFuze services to apply nginx configuration fixes...

REM Stop all services
echo ⏹️ Stopping services...
docker-compose down

REM Rebuild nginx container to apply new configuration
echo 🔨 Rebuilding nginx container...
docker-compose build nginx

REM Start services
echo 🚀 Starting services...
docker-compose up -d

REM Wait for services to be ready
echo ⏳ Waiting for services to be ready...
timeout /t 10 /nobreak >nul

REM Check service health
echo 🔍 Checking service health...
docker-compose ps

echo ✅ Services restarted! The 405 error should now be fixed.
echo 🌐 You can now test the login at: https://ai.cloudfuze.com/login.html
pause
