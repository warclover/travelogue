@echo off
REM Build Travelogue Studio exe (M11 · requires: pip install -e ".[desktop]")
cd /d "%~dp0.."
python -m PyInstaller packaging/travelogue-studio.spec --noconfirm
if errorlevel 1 exit /b 1
echo.
echo OK: dist\TravelogueStudio.exe
echo Run: dist\TravelogueStudio.exe
echo      dist\TravelogueStudio.exe studio --pick-folder-dialog
echo      dist\TravelogueStudio.exe studio --demo-album
