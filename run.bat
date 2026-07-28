@echo off
cd /d %~dp0

echo Checking/installing required packages...
pip install -r requirements.txt >nul 2>&1

echo.
echo Starting web app: http://127.0.0.1:8000
echo Press Ctrl+C in this window to stop.
echo.

start "" /min powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://127.0.0.1:8000'"

python app.py

pause
