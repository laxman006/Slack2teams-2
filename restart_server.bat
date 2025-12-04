@echo off
echo ============================================
echo   Restarting CloudFuze Backend Server
echo ============================================
echo.

echo Stopping existing server...
taskkill /F /FI "WINDOWTITLE eq *python server.py*" 2>nul
timeout /t 2 /nobreak >nul

echo Starting server...
cd /d %~dp0
call venv\Scripts\activate.bat
python server.py

pause

