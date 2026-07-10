@echo off
REM Travelogue Studio — double-click entry (AC-P2-03 M8)
REM Opt in to local album paths for folder-picker / JSON import on this machine.
REM Production default is off; unset or set to 0 to restrict to uploads/demo/trips only.
if not defined TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM set TRAVELOGUE_STUDIO_TRUST_LOCAL_ALBUM=1
cd /d "%~dp0.."
python -m travelogue studio
if errorlevel 1 pause
