@echo off
REM Build Travelogue Studio onedir + portable zip (Desktop Installer V1 · M-INS-0a)
REM Requires: pip install -e ".[desktop]"
setlocal
cd /d "%~dp0.."

echo [1/2] PyInstaller onedir ...
python -m PyInstaller packaging/travelogue-studio.spec --noconfirm
if errorlevel 1 exit /b 1

echo [2/2] Portable sidecar + VERSION + SHA256 + zip ...
python scripts/package_studio_portable.py
if errorlevel 1 exit /b 1

echo.
echo OK: dist\TravelogueStudio\TravelogueStudio.exe
echo     dist\TravelogueStudio-portable-*.zip
echo Run: dist\TravelogueStudio\TravelogueStudio.exe
endlocal
