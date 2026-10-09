@echo off
title RF Noise Monitor & Reduction Analyzer - KLS VDIT
cd /d "%~dp0"

echo ======================================================================
echo   SDR-BASED RF NOISE MONITORING AND REDUCTION ANALYSIS
echo   Department of ECE, KLS VDIT Haliyal
echo ======================================================================
echo.

if exist ".venv\Scripts\python.exe" (
    echo [INFO] Starting application using virtual environment (.venv)...
    ".venv\Scripts\python.exe" main.py
) else (
    echo [INFO] Starting application using system Python...
    python main.py
)

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Application exited with error code %ERRORLEVEL%.
    pause
)
