@echo off
setlocal
title VideoTransformer
cd /d "%~dp0"
if not exist "videotrans\Scripts\python.exe" (
    call INSTALL.bat
    if errorlevel 1 exit /b 1
)
"videotrans\Scripts\python.exe" -c "import flask, flask_socketio, requests, yt_dlp, curl_cffi" >nul 2>&1
if errorlevel 1 (
    call INSTALL.bat
    if errorlevel 1 exit /b 1
)
echo VideoTransformer: http://127.0.0.1:5000
"videotrans\Scripts\python.exe" web\app.py
exit /b %errorlevel%
