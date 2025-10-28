@echo off
REM Auto-Correction Script Runner for Windows
REM This script runs the automatic correction for low-scored responses

echo ========================================
echo CloudFuze Auto-Correction System
echo ========================================
echo.
echo This will automatically correct responses with score ^< 6
echo.
echo Options:
echo   1. Run once (check now and exit)
echo   2. Process ALL low-scored traces (no limit)
echo   3. Run in polling mode (check every 5 minutes)
echo   4. Dry run (show what would be corrected)
echo.

set /p choice="Enter your choice (1-4): "

if "%choice%"=="1" (
    echo.
    echo Running once (limit: 10 traces)...
    python scripts\auto_correct_low_scores.py
) else if "%choice%"=="2" (
    echo.
    echo Processing ALL low-scored traces...
    python scripts\auto_correct_low_scores.py --all
) else if "%choice%"=="3" (
    echo.
    echo Running in polling mode (Ctrl+C to stop)...
    python scripts\auto_correct_low_scores.py --poll --interval 300
) else if "%choice%"=="4" (
    echo.
    echo Running dry run...
    python scripts\auto_correct_low_scores.py --dry-run
) else (
    echo Invalid choice!
    goto :eof
)

echo.
pause

