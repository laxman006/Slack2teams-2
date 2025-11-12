@echo off
REM Force rebuild vectorstore with proper environment variable
echo ============================================================
echo FORCE VECTORSTORE REBUILD
echo ============================================================
echo This will rebuild the vectorstore from scratch
echo.

REM Set environment variable to allow initialization
set INITIALIZE_VECTORSTORE=true

REM Run Python rebuild
python rebuild_now.py

pause


