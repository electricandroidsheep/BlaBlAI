@echo off
title Academic AI Interaction Protocol Logger
cd /d "%~dp0"

echo Launching Academic AI Interaction Protocol Logger...
python app.py
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Application exited with code %errorlevel%.
    pause
)
