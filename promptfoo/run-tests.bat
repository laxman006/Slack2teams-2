@echo off
echo ========================================
echo CloudFuze Chatbot - Promptfoo Tests
echo ========================================
echo.
echo Checking if server is running...
curl -s http://localhost:8002/health >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] FastAPI server is not running!
    echo Please start the server first: python server.py
    echo.
    pause
    exit /b 1
)
echo [OK] Server is running
echo.
echo Starting promptfoo tests...
cd /d "%~dp0"
call npx promptfoo eval -c promptfooconfig.yaml
echo.
echo ========================================
echo Tests complete! Opening results viewer...
echo ========================================
call npx promptfoo view



