@echo off
REM Travelogue Studio — double-click entry (AC-P2-03 M8)
cd /d "%~dp0.."
python -m travelogue studio
if errorlevel 1 pause
