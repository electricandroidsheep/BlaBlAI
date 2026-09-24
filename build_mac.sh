#!/bin/bash
# ==============================================================================
# Build Standalone macOS .app Bundle and .dmg Installer for BlaBlAI
# Run on macOS: chmod +x build_mac.sh && ./build_mac.sh
# ==============================================================================

set -e

echo "========================================================"
echo " Building BlaBlAI for macOS (.app & .dmg)"
echo "========================================================"

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "1. Checking / Installing dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install pyinstaller customtkinter markdown packaging darkdetect reportlab pillow

echo "2. Generating icon asset..."
python3 -c "from gui.assets import ensure_icon_file; ensure_icon_file()"

echo "3. Building macOS Application Bundle (dist/BlaBlAI.app)..."
pyinstaller --windowed --noconfirm \
    --name "BlaBlAI" \
    --add-data "styles.css:." \
    --add-data "blablai_icon.png:." \
    --collect-all customtkinter \
    --collect-all reportlab \
    --collect-all PIL \
    app.py

echo "4. Creating native macOS .dmg disk image..."
if command -v hdiutil &> /dev/null; then
    hdiutil create -volname "BlaBlAI" -srcfolder "dist/BlaBlAI.app" -ov -format UDZO "dist/BlaBlAI.dmg"
    echo "========================================================"
    echo " SUCCESS! Native macOS DMG created at:"
    echo " dist/BlaBlAI.dmg"
    echo "========================================================"
else
    echo "Bundle built at dist/BlaBlAI.app (hdiutil not found, skipping dmg wrapper)."
fi
