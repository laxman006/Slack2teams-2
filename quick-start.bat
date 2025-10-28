@echo off
REM Quick Start Script for Local Testing (Windows)
REM This script sets up and runs the application locally

setlocal enabledelayedexpansion

echo ==================================
echo CF Chatbot - Quick Start Script
echo ==================================
echo.

REM Step 1: Check Python
echo Step 1: Checking Python installation...
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo [92m✅ Python found[0m
    python --version
) else (
    echo [91m❌ Python not found. Please install Python 3.8+[0m
    pause
    exit /b 1
)

REM Step 2: Check/Create virtual environment
echo.
echo Step 2: Setting up virtual environment...
if not exist "venv\" (
    echo [93m💡 Creating virtual environment...[0m
    python -m venv venv
    echo [92m✅ Virtual environment created[0m
) else (
    echo [92m✅ Virtual environment already exists[0m
)

REM Step 3: Activate virtual environment
echo.
echo Step 3: Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% == 0 (
    echo [92m✅ Virtual environment activated[0m
) else (
    echo [91m❌ Failed to activate virtual environment[0m
    echo [93m💡 Try running: Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser[0m
    pause
    exit /b 1
)

REM Step 4: Install dependencies
echo.
echo Step 4: Installing dependencies...
echo This may take a few minutes...
python -m pip install --upgrade pip -q
pip install -r requirements.txt -q
if %errorlevel% == 0 (
    echo [92m✅ Dependencies installed[0m
) else (
    echo [91m❌ Failed to install dependencies[0m
    pause
    exit /b 1
)

REM Step 5: Check .env file
echo.
echo Step 5: Checking environment configuration...
if not exist ".env" (
    if exist ".env.example" (
        echo [93m⚠️ .env file not found. Copying from .env.example...[0m
        copy .env.example .env
        echo [93m💡 Please edit .env file and add your credentials[0m
        echo [93m💡 Required: MICROSOFT_CLIENT_SECRET, OPENAI_API_KEY, LANGFUSE keys[0m
        echo.
        echo Press any key when you've updated .env file...
        pause >nul
    ) else (
        echo [91m❌ .env.example not found. Please create .env file manually[0m
        pause
        exit /b 1
    )
) else (
    echo [92m✅ .env file found[0m
)

REM Step 6: Run diagnostic tests
echo.
echo Step 6: Running diagnostic tests...
python test_auth.py
if %errorlevel% neq 0 (
    echo [93m⚠️ Diagnostic tests completed with warnings[0m
    echo.
)

REM Step 7: Check MongoDB
echo.
echo Step 7: Checking MongoDB...
netstat -ano | findstr :27017 >nul 2>&1
if %errorlevel% == 0 (
    echo [92m✅ MongoDB is running on port 27017[0m
) else (
    echo [93m⚠️ MongoDB not detected. Will use JSON storage as fallback[0m
    echo [93m💡 To use MongoDB, install and start it: net start MongoDB[0m
)

REM Step 8: Start backend server
echo.
echo Step 8: Starting backend server...
echo [93m💡 Backend will run on http://localhost:8002[0m
echo [93m💡 Press Ctrl+C to stop the server[0m
echo.
echo [92m====================================[0m
echo [92mServer starting...[0m
echo [92m====================================[0m
echo.

REM Run the server
python server.py

pause




