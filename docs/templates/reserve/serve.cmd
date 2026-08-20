@echo off
cd /d "%~dp0"
where py >nul 2>nul && py -3 serve.py && goto :eof
python serve.py
if errorlevel 1 (
  echo 需要 Python 3。安装后在本夹再双击 serve.cmd。
  pause
)
