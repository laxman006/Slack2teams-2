@echo off
echo ======================================================================
echo MongoDB Integration - Server Startup
echo ======================================================================
echo.
echo Starting FastAPI backend with MongoDB...
echo.
echo After server starts, you should see:
echo   [*] MongoDB vector store backend selected
echo   [OK] Loaded MongoDB vectorstore with 1511 documents
echo   INFO: Uvicorn running on http://0.0.0.0:8000
echo.
echo Then open your browser to: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo ======================================================================
echo.

cd /d "%~dp0"
python server.py



