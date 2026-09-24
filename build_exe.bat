@echo off
title Build Standalone BlaBlAI Executable
cd /d "%~dp0"

echo ========================================================
echo  Building Standalone Windows Executable (.exe)
echo  BlaBlAI — Academic AI Interaction Protocol Logger
echo ========================================================
echo.

echo 1. Ensuring dependencies are installed...
python -m pip install pyinstaller customtkinter markdown packaging darkdetect reportlab pillow

echo.
echo 2. Ensuring vector icon asset is generated...
python -c "from gui.assets import ensure_icon_file; ensure_icon_file()"

echo.
echo 3. Packaging application into single standalone .exe...
pyinstaller --noconsole --onefile ^
    --name "BlaBlAI" ^
    --add-data "styles.css;." ^
    --add-data "blablai_icon.png;." ^
    --collect-all customtkinter ^
    --collect-all reportlab ^
    --collect-all PIL ^
    app.py

if %errorlevel% equ 0 (
    echo.
    echo ========================================================
    echo  SUCCESS! Standalone executable generated at:
    echo  dist\BlaBlAI.exe
    echo ========================================================
    echo You can copy this .exe to any Windows computer or USB stick!
) else (
    echo.
    echo [ERROR] Build failed. Review output above.
)

pause
